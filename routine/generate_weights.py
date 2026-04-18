# routine/generate_weights.py
# Run from the Rensai repo root.
# Data: temp-data/mal-archives/{anime,manga,characters,people,producers}/full.zip
# VNDB: place vndb-db-*.tar.zst in repo root if needed (gitignored, processed once)
# Requires: pip install zstandard  (only if VNDB dump is present)
# Outputs: routine/topics.json
#
# Safe to re-run: existing scores are preserved, only weights/names update.

import json
import math
import re
import sys
import zipfile
from pathlib import Path

DATA_DIR = Path("temp-data/mal-archives")
OUTPUT = Path("routine/topics.json")

# Minimum favorites required to include an entry (gate check before metric computation)
FAVES_GATE = {
    "anime":      500,
    "manga":       500,
    "ln":          500,
    "people":     1000,
    "characters": 1_500,
    "producers":  1000,
}

SCORE_FALLBACK = 7.0  # used when MAL score is null/zero
VN_THRESHOLD   = 450  # minimum c_votecount for VNDB entries (~750 entries)
VN_FLOOR       = 150  # minimum c_votecount for long-tail VNDB entries

LONG_TAIL_WEIGHT = (250, 1200)  # weight range for below-threshold entries
LONG_TAIL_SCORE  = (150, 600)   # starting score range for below-threshold entries

def to_slug(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s-]", "", title)
    slug = re.sub(r"[\s]+", "-", title.strip())
    return slug if slug else None


def slug_to_name(slug: str) -> str:
    return slug.replace("-", " ").title()


def calc_weight(metric, threshold, max_metric, low=60, high=150):
    if max_metric <= threshold or metric <= threshold:
        return high
    ratio = (math.log10(metric) - math.log10(threshold)) / \
            (math.log10(max_metric) - math.log10(threshold))
    return max(low, min(high, round(high - ratio * (high - low))))


def iter_zip(zip_path):
    """Yield parsed dicts from every .json entry in a zip file."""
    if not zip_path.exists():
        return
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".json"):
                continue
            try:
                yield json.loads(zf.read(name))
            except Exception:
                continue


def main():
    # Load existing topics to preserve scores across re-runs
    existing = {}
    if OUTPUT.exists():
        try:
            existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Collected: slug -> {"name": str, "type": [str], "weight": int}
    # Seed from existing so entries survive re-runs without their source data present.
    def _to_list(t):
        return t if isinstance(t, list) else [t]

    collected = {
        slug: {"name": v["name"], "type": _to_list(v["type"]), "weight": v["weight"]}
        for slug, v in existing.items()
    }

    def merge(slug, name, weight, topic_type):
        if not slug:
            return
        if slug in existing:
            # Preserve weight/score, but collect new types
            if slug in collected and topic_type not in collected[slug]["type"]:
                collected[slug]["type"].append(topic_type)
            return
        if slug not in collected:
            collected[slug] = {"name": name, "type": [topic_type], "weight": weight}
        else:
            if topic_type not in collected[slug]["type"]:
                collected[slug]["type"].append(topic_type)
            if weight < collected[slug]["weight"]:
                collected[slug]["weight"] = weight

    def merge_tail(slug, name, weight, initial_score, topic_type):
        """Add a long-tail entry only if the slug is not already claimed."""
        if not slug:
            return
        if slug in collected:
            # Slug exists (main tier or existing) — just add the type
            if topic_type not in collected[slug]["type"]:
                collected[slug]["type"].append(topic_type)
            return
        collected[slug] = {
            "name": name, "type": [topic_type],
            "weight": weight, "initial_score": initial_score,
        }

    data_available = DATA_DIR.exists() and any(DATA_DIR.iterdir())

    if not data_available:
        print(f"Data directory not found or empty at {DATA_DIR} — skipping automated passes.",
              file=sys.stderr)
    else:
        # --- Anime ---
        anime_entries = []
        anime_tail = []
        anime_floor = max(10, FAVES_GATE["anime"] // 10)
        for d in iter_zip(DATA_DIR / "anime/full.zip"):
            fav = d.get("favorites", 0)
            title = (d.get("title_english") or d.get("title") or "").strip()
            if not title:
                continue
            metric = fav * (d.get("score") or SCORE_FALLBACK)
            if fav >= FAVES_GATE["anime"]:
                anime_entries.append((title, metric))
            elif fav >= anime_floor:
                anime_tail.append((title, metric))

        if anime_entries:
            max_a = max(m for _, m in anime_entries)
            min_a = min(m for _, m in anime_entries)
            for title, metric in anime_entries:
                merge(to_slug(title), title, calc_weight(metric, min_a, max_a), "anime")

        if anime_tail:
            max_at = max(m for _, m in anime_tail)
            min_at = min(m for _, m in anime_tail)
            for title, metric in anime_tail:
                w = calc_weight(metric, min_at, max_at, *LONG_TAIL_WEIGHT)
                s = calc_weight(metric, min_at, max_at, *LONG_TAIL_SCORE)
                merge_tail(to_slug(title), title, w, s, "anime")

        print(f"Anime: {len(anime_entries)} entries, {len(anime_tail)} long-tail", file=sys.stderr)

        # --- Manga & Light Novels (same zip, single pass) ---
        manga_entries = []
        manga_tail = []
        manga_floor = max(10, FAVES_GATE["manga"] // 10)
        ln_entries = []
        ln_tail = []
        ln_floor = max(10, FAVES_GATE["ln"] // 10)
        for d in iter_zip(DATA_DIR / "manga/full.zip"):
            fav = d.get("favorites", 0)
            title = (d.get("title_english") or d.get("title") or "").strip()
            if not title:
                continue
            metric = fav * (d.get("score") or SCORE_FALLBACK)
            if d.get("type") in ("Light Novel", "Novel"):
                if fav >= FAVES_GATE["ln"]:
                    ln_entries.append((title, metric))
                elif fav >= ln_floor:
                    ln_tail.append((title, metric))
            else:
                if fav >= FAVES_GATE["manga"]:
                    manga_entries.append((title, metric))
                elif fav >= manga_floor:
                    manga_tail.append((title, metric))

        if manga_entries:
            max_m = max(m for _, m in manga_entries)
            min_m = min(m for _, m in manga_entries)
            for title, metric in manga_entries:
                merge(to_slug(title), title, calc_weight(metric, min_m, max_m), "manga")

        if manga_tail:
            max_mt = max(m for _, m in manga_tail)
            min_mt = min(m for _, m in manga_tail)
            for title, metric in manga_tail:
                w = calc_weight(metric, min_mt, max_mt, *LONG_TAIL_WEIGHT)
                s = calc_weight(metric, min_mt, max_mt, *LONG_TAIL_SCORE)
                merge_tail(to_slug(title), title, w, s, "manga")

        print(f"Manga: {len(manga_entries)} entries, {len(manga_tail)} long-tail", file=sys.stderr)

        if ln_entries:
            max_l = max(m for _, m in ln_entries)
            min_l = min(m for _, m in ln_entries)
            for title, metric in ln_entries:
                merge(to_slug(title), title, calc_weight(metric, min_l, max_l), "light-novel")

        if ln_tail:
            max_lt = max(m for _, m in ln_tail)
            min_lt = min(m for _, m in ln_tail)
            for title, metric in ln_tail:
                w = calc_weight(metric, min_lt, max_lt, *LONG_TAIL_WEIGHT)
                s = calc_weight(metric, min_lt, max_lt, *LONG_TAIL_SCORE)
                merge_tail(to_slug(title), title, w, s, "light-novel")

        print(f"Light Novels: {len(ln_entries)} entries, {len(ln_tail)} long-tail", file=sys.stderr)

        # --- MAL Personnel (seiyuu, composers, directors, etc.) ---
        people_entries = []
        people_tail = []
        people_floor = max(10, FAVES_GATE["people"] // 10)
        for d in iter_zip(DATA_DIR / "people/full.zip"):
            fav = d.get("favorites", 0)
            name = (d.get("name") or "").strip()
            if not name:
                continue
            if fav >= FAVES_GATE["people"]:
                people_entries.append((name, fav))
            elif fav >= people_floor:
                people_tail.append((name, fav))

        if people_entries:
            max_p = max(m for _, m in people_entries)
            for name, fav in people_entries:
                merge(to_slug(name), name, calc_weight(fav, FAVES_GATE["people"], max_p), "person")

        if people_tail:
            max_pt = max(m for _, m in people_tail)
            min_pt = min(m for _, m in people_tail)
            for name, fav in people_tail:
                w = calc_weight(fav, min_pt, max_pt, *LONG_TAIL_WEIGHT)
                s = calc_weight(fav, min_pt, max_pt, *LONG_TAIL_SCORE)
                merge_tail(to_slug(name), name, w, s, "person")

        print(f"MAL Personnel: {len(people_entries)} entries, {len(people_tail)} long-tail", file=sys.stderr)

        # --- Characters ---
        char_entries = []
        char_tail = []
        char_floor = max(10, FAVES_GATE["characters"] // 10)
        for d in iter_zip(DATA_DIR / "characters/full.zip"):
            fav = d.get("favorites", 0)
            name = (d.get("name") or "").strip()
            if not name:
                continue
            if fav >= FAVES_GATE["characters"]:
                char_entries.append((name, fav))
            elif fav >= char_floor:
                char_tail.append((name, fav))

        if char_entries:
            max_c = max(m for _, m in char_entries)
            for name, fav in char_entries:
                merge(to_slug(name), name, calc_weight(fav, FAVES_GATE["characters"], max_c), "character")

        if char_tail:
            max_ct = max(m for _, m in char_tail)
            min_ct = min(m for _, m in char_tail)
            for name, fav in char_tail:
                w = calc_weight(fav, min_ct, max_ct, *LONG_TAIL_WEIGHT)
                s = calc_weight(fav, min_ct, max_ct, *LONG_TAIL_SCORE)
                merge_tail(to_slug(name), name, w, s, "character")

        print(f"Characters: {len(char_entries)} entries, {len(char_tail)} long-tail", file=sys.stderr)

        # --- Producers (studios / labels) ---
        producer_entries = []
        producer_tail = []
        producer_floor = max(10, FAVES_GATE["producers"] // 10)
        for d in iter_zip(DATA_DIR / "producers/full.zip"):
            fav = d.get("favorites", 0)
            titles = d.get("titles", [])
            name = next((t["title"] for t in titles if t.get("type") == "Default"), "")
            if not name and titles:
                name = titles[0].get("title", "")
            name = name.strip()
            if not name:
                continue
            if fav >= FAVES_GATE["producers"]:
                producer_entries.append((name, fav))
            elif fav >= producer_floor:
                producer_tail.append((name, fav))

        if producer_entries:
            max_pr = max(m for _, m in producer_entries)
            for name, fav in producer_entries:
                merge(to_slug(name), name, calc_weight(fav, FAVES_GATE["producers"], max_pr), "producer")

        if producer_tail:
            max_prt = max(m for _, m in producer_tail)
            min_prt = min(m for _, m in producer_tail)
            for name, fav in producer_tail:
                w = calc_weight(fav, min_prt, max_prt, *LONG_TAIL_WEIGHT)
                s = calc_weight(fav, min_prt, max_prt, *LONG_TAIL_SCORE)
                merge_tail(to_slug(name), name, w, s, "producer")

        print(f"Producers: {len(producer_entries)} entries, {len(producer_tail)} long-tail", file=sys.stderr)

        # --- Visual Novels (from VNDB dump in repo root, if present) ---
        vndb_dumps = sorted(
            list(Path(".").glob("vndb-db-*.tar.zst")) +
            list(Path("temp-data").glob("vndb-db-*.tar.zst"))
        )
        if vndb_dumps:
            try:
                import zstandard
                import tarfile as tarlib
            except ImportError:
                print("zstandard not installed — skipping VN pass. Run: pip install zstandard",
                      file=sys.stderr)
                vndb_dumps = []
        if vndb_dumps:
            VNDB_DUMP = vndb_dumps[-1]
            vn_titles = {}
            vn_votes = {}

            with open(VNDB_DUMP, "rb") as fh:
                dctx = zstandard.ZstdDecompressor()
                with dctx.stream_reader(fh) as reader:
                    with tarlib.open(fileobj=reader, mode="r|") as tar:
                        for m in tar:
                            f = tar.extractfile(m)
                            if not f:
                                continue
                            if m.name == "db/vn":
                                for line in f:
                                    cols = line.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                                    if len(cols) < 5:
                                        continue
                                    vid = cols[0]
                                    try:
                                        vn_votes[vid] = int(cols[4])
                                    except ValueError:
                                        pass
                            elif m.name == "db/vn_titles":
                                for line in f:
                                    cols = line.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                                    if len(cols) < 5:
                                        continue
                                    vid, lang, official, title, latin = \
                                        cols[0], cols[1], cols[2], cols[3], cols[4]
                                    if official != "t":
                                        continue
                                    if lang == "en" and title and title != r"\N":
                                        vn_titles[vid] = title
                                    elif vid not in vn_titles and latin and latin != r"\N":
                                        vn_titles[vid] = latin

            vn_count = 0
            vn_tail_count = 0
            vn_main = []
            vn_tail = []
            for vid, votes in vn_votes.items():
                title = vn_titles.get(vid)
                if not title:
                    continue
                if votes >= VN_THRESHOLD:
                    vn_main.append((title, votes))
                elif votes >= VN_FLOOR:
                    vn_tail.append((title, votes))

            if vn_main:
                max_vm = max(m for _, m in vn_main)
                min_vm = min(m for _, m in vn_main)
                for title, votes in vn_main:
                    merge(to_slug(title), title, calc_weight(votes, min_vm, max_vm), "visual-novel")
                vn_count = len(vn_main)

            if vn_tail:
                max_vt = max(m for _, m in vn_tail)
                min_vt = min(m for _, m in vn_tail)
                for title, votes in vn_tail:
                    w = calc_weight(votes, min_vt, max_vt, *LONG_TAIL_WEIGHT)
                    s = calc_weight(votes, min_vt, max_vt, *LONG_TAIL_SCORE)
                    merge_tail(to_slug(title), title, w, s, "visual-novel")
                vn_tail_count = len(vn_tail)

            print(f"Visual Novels: {vn_count} entries, {vn_tail_count} long-tail", file=sys.stderr)
        else:
            print("No VNDB dump found — skipping VN pass.", file=sys.stderr)

    # Build final topics, preserving existing scores
    topics = {}
    for slug, meta in sorted(collected.items()):
        if not slug:
            continue
        topics[slug] = {
            "name":   meta["name"],
            "type":   meta["type"],
            "weight": meta["weight"],
            "score":  existing.get(slug, {}).get("score", meta.get("initial_score", 0)),
        }

    OUTPUT.write_text(json.dumps(topics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(topics)} total entries -> {OUTPUT}")


if __name__ == "__main__":
    main()
