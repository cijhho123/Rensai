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
VN_THRESHOLD   = 100  # minimum c_votecount for VNDB entries

def to_slug(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s-]", "", title)
    return re.sub(r"[\s]+", "-", title.strip())


def slug_to_name(slug: str) -> str:
    return slug.replace("-", " ").title()


def calc_weight(metric: int, threshold: int, max_metric: int) -> int:
    if metric <= threshold:
        return 150
    ratio = (math.log10(metric) - math.log10(threshold)) / \
            (math.log10(max_metric) - math.log10(threshold))
    return max(60, min(150, round(150 - ratio * 90)))


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

    # Collected: slug -> {"name": str, "type": str, "weight": int}
    # Seed from existing so entries survive re-runs without their source data present.
    # When source data IS present, merge() updates weights in place.
    collected = {
        slug: {"name": v["name"], "type": v["type"], "weight": v["weight"]}
        for slug, v in existing.items()
    }

    def merge(slug, name, weight, topic_type):
        if slug not in collected or collected[slug]["weight"] > weight:
            collected[slug] = {"name": name, "type": topic_type, "weight": weight}

    data_available = DATA_DIR.exists() and any(DATA_DIR.iterdir())

    if not data_available:
        print(f"Data directory not found or empty at {DATA_DIR} — skipping automated passes.",
              file=sys.stderr)
    else:
        # --- Anime ---
        anime_entries = []
        for d in iter_zip(DATA_DIR / "anime/full.zip"):
            fav = d.get("favorites", 0)
            if fav < FAVES_GATE["anime"]:
                continue
            title = (d.get("title_english") or d.get("title") or "").strip()
            if not title:
                continue
            anime_entries.append((title, fav * (d.get("score") or SCORE_FALLBACK)))

        if anime_entries:
            max_a = max(m for _, m in anime_entries)
            min_a = min(m for _, m in anime_entries)
            for title, metric in anime_entries:
                merge(to_slug(title), title, calc_weight(metric, min_a, max_a), "anime")
        print(f"Anime: {len(anime_entries)} entries", file=sys.stderr)

        # --- Manga & Light Novels (same zip, single pass) ---
        manga_entries = []
        ln_entries = []
        for d in iter_zip(DATA_DIR / "manga/full.zip"):
            fav = d.get("favorites", 0)
            title = (d.get("title_english") or d.get("title") or "").strip()
            if not title:
                continue
            metric = fav * (d.get("score") or SCORE_FALLBACK)
            if d.get("type") == "Light Novel":
                if fav >= FAVES_GATE["ln"]:
                    ln_entries.append((title, metric))
            else:
                if fav >= FAVES_GATE["manga"]:
                    manga_entries.append((title, metric))

        if manga_entries:
            max_m = max(m for _, m in manga_entries)
            min_m = min(m for _, m in manga_entries)
            for title, metric in manga_entries:
                merge(to_slug(title), title, calc_weight(metric, min_m, max_m), "manga")
        print(f"Manga: {len(manga_entries)} entries", file=sys.stderr)

        if ln_entries:
            max_l = max(m for _, m in ln_entries)
            min_l = min(m for _, m in ln_entries)
            for title, metric in ln_entries:
                merge(to_slug(title), title, calc_weight(metric, min_l, max_l), "light-novel")
        print(f"Light Novels: {len(ln_entries)} entries", file=sys.stderr)

        # --- MAL Personnel (seiyuu, composers, directors, etc.) ---
        people_entries = []
        for d in iter_zip(DATA_DIR / "people/full.zip"):
            fav = d.get("favorites", 0)
            name = (d.get("name") or "").strip()
            if fav >= FAVES_GATE["people"] and name:
                people_entries.append((name, fav))

        if people_entries:
            max_p = max(m for _, m in people_entries)
            for name, fav in people_entries:
                merge(to_slug(name), name, calc_weight(fav, FAVES_GATE["people"], max_p), "person")
        print(f"MAL Personnel: {len(people_entries)} entries", file=sys.stderr)

        # --- Characters ---
        char_entries = []
        for d in iter_zip(DATA_DIR / "characters/full.zip"):
            fav = d.get("favorites", 0)
            name = (d.get("name") or "").strip()
            if fav >= FAVES_GATE["characters"] and name:
                char_entries.append((name, fav))

        if char_entries:
            max_c = max(m for _, m in char_entries)
            for name, fav in char_entries:
                merge(to_slug(name), name, calc_weight(fav, FAVES_GATE["characters"], max_c), "character")
        print(f"Characters: {len(char_entries)} entries", file=sys.stderr)

        # --- Producers (studios / labels) ---
        producer_entries = []
        for d in iter_zip(DATA_DIR / "producers/full.zip"):
            fav = d.get("favorites", 0)
            if fav < FAVES_GATE["producers"]:
                continue
            titles = d.get("titles", [])
            name = next((t["title"] for t in titles if t.get("type") == "Default"), "")
            if not name and titles:
                name = titles[0].get("title", "")
            name = name.strip()
            if not name:
                continue
            producer_entries.append((name, fav))

        if producer_entries:
            max_pr = max(m for _, m in producer_entries)
            for name, fav in producer_entries:
                merge(to_slug(name), name, calc_weight(fav, FAVES_GATE["producers"], max_pr), "producer")
        print(f"Producers: {len(producer_entries)} entries", file=sys.stderr)

        # --- Visual Novels (from VNDB dump in repo root, if present) ---
        vndb_dumps = sorted(Path(".").glob("vndb-db-*.tar.zst"))
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

            max_vn = max(vn_votes.values(), default=1)
            vn_count = 0
            for vid, votes in vn_votes.items():
                if votes < VN_THRESHOLD:
                    continue
                title = vn_titles.get(vid)
                if not title:
                    continue
                merge(to_slug(title), title, calc_weight(votes, VN_THRESHOLD, max_vn), "visual-novel")
                vn_count += 1
            print(f"Visual Novels: {vn_count} entries", file=sys.stderr)
        else:
            print("No VNDB dump found — skipping VN pass.", file=sys.stderr)

    # Build final topics, preserving existing scores
    topics = {}
    for slug, meta in sorted(collected.items()):
        topics[slug] = {
            "name":   meta["name"],
            "type":   meta["type"],
            "weight": meta["weight"],
            "score":  existing.get(slug, {}).get("score", 0),
        }

    OUTPUT.write_text(json.dumps(topics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(topics)} total entries -> {OUTPUT}")


if __name__ == "__main__":
    main()
