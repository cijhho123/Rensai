# routine/generate_weights.py
# Run from the Rensai repo root on the machine with MAL_Archive data.
# Requires: pip install zstandard
# MAL_Archive path: C:/Users/benka/git/MAL_Archive/data/raw
# VNDB dump: vndb-db-*.tar.zst (in repo root)
# Outputs: routine/topics.json
#
# Safe to re-run: existing scores are preserved, only weights/names update.

import json
import math
import re
import sys
from pathlib import Path

MAL_ARCHIVE = Path("C:/Users/benka/git/MAL_Archive/data/raw")
OUTPUT = Path("routine/topics.json")

THRESHOLDS = {
    "anime":   10_000,
    "manga":   5_000,
    "ln":      3_000,
    "people":  500,
}

# Manual entries: slug -> (weight, type)
# Type maps to blog categories: anime, manga, light-novel, visual-novel,
# seiyuu, anime-music, figures, cosplay, idol, otaku-culture, otaku-history
MANUAL = {
    # Anime Music
    "anison-composers":        (95,  "anime-music"),
    "anime-op-ed":             (90,  "anime-music"),
    "anime-soundtracks":       (100, "anime-music"),
    "anime-movie-soundtracks": (105, "anime-music"),
    "anison-history":          (100, "anime-music"),
    "vocaloid-culture":        (95,  "anime-music"),
    "idol-anime-music":        (105, "anime-music"),
    "seiyuu-who-sing":         (110, "anime-music"),
    "anime-bands":             (110, "anime-music"),
    "anison-labels":           (115, "anime-music"),
    # Otaku History / Culture
    "otaku-history-1980s":     (100, "otaku-history"),
    "otaku-history-1990s":     (100, "otaku-history"),
    "otaku-history-2000s":     (100, "otaku-history"),
    "moe-culture":             (100, "otaku-culture"),
    "fansub-era":              (110, "otaku-history"),
    "akihabara-culture":       (100, "otaku-culture"),
    "comiket-history":         (100, "otaku-history"),
    "otaku-bashing":           (110, "otaku-history"),
    "isekai-boom":             (100, "otaku-culture"),
    "vtuber-culture":          (90,  "otaku-culture"),
    "idol-culture":            (95,  "otaku-culture"),
    "fujoshi-culture":         (105, "otaku-culture"),
    "anime-overseas-spread":   (100, "otaku-history"),
    "doujinshi-culture":       (105, "otaku-culture"),
    "light-novel-boom":        (105, "otaku-history"),
    "anime-piracy-history":    (110, "otaku-history"),
    "gacha-and-anime-franchises": (105, "otaku-culture"),
    # Otaku Districts & Physical Spaces
    "akihabara-electronics-to-anime": (102, "otaku-history"),
    "akihabara-2008-and-after":       (104, "otaku-history"),
    "nakano-broadway":                (103, "otaku-culture"),
    "ikebukuro-otome-road":           (102, "otaku-culture"),
    "nipponbashi-den-den-town":       (103, "otaku-culture"),
    "otaku-tourism":                  (102, "otaku-culture"),
    "anime-location-pilgrimages":     (103, "otaku-culture"),
    # Maid Cafes & Concept Cafes
    "maid-cafe-history":      (101, "otaku-culture"),
    "maid-cafe-industry":     (103, "otaku-culture"),
    "maid-cafe-overseas":     (104, "otaku-culture"),
    "butler-cafe-culture":    (105, "otaku-culture"),
    "concept-cafe-evolution": (103, "otaku-culture"),
    "anime-themed-cafes":     (103, "otaku-culture"),
    # Arcades & Game Centers
    "game-center-culture":        (101, "otaku-culture"),
    "rhythm-game-culture":        (102, "otaku-culture"),
    "crane-game-culture":         (103, "otaku-culture"),
    "arcade-fighting-game-scene": (103, "otaku-culture"),
    "arcade-decline-and-survival":(104, "otaku-culture"),
    # Otaku Retail & Collecting
    "doujinshi-shops":             (103, "otaku-culture"),
    "figure-collecting-culture":   (101, "figures"),
    "retro-anime-goods-collecting":(103, "figures"),
    "blind-box-culture":           (102, "figures"),
    "gashapon-history":            (103, "figures"),
    # Japanese Fashion & Street Culture
    "lolita-fashion":          (100, "otaku-culture"),
    "gothic-lolita":           (103, "otaku-culture"),
    "sweet-lolita":            (103, "otaku-culture"),
    "classic-lolita":          (104, "otaku-culture"),
    "wa-lolita":               (106, "otaku-culture"),
    "jirai-kei":               (101, "otaku-culture"),
    "menhera-kei":             (103, "otaku-culture"),
    "yami-kawaii":             (102, "otaku-culture"),
    "decora-fashion":          (104, "otaku-culture"),
    "fairy-kei":               (105, "otaku-culture"),
    "otome-kei":               (105, "otaku-culture"),
    "mori-girl":               (106, "otaku-culture"),
    "dolly-kei":               (107, "otaku-culture"),
    "gyaru-culture":           (101, "otaku-culture"),
    "kogal":                   (103, "otaku-culture"),
    "ganguro":                 (103, "otaku-culture"),
    "himegyaru":               (104, "otaku-culture"),
    "visual-kei-fashion":      (102, "otaku-culture"),
    "harajuku-fashion-history":(100, "otaku-history"),
    "fruits-magazine":         (104, "otaku-culture"),
    "ura-harajuku":            (105, "otaku-culture"),
    "angura-kei":              (107, "otaku-culture"),
    "kawaii-as-cultural-export":(100, "otaku-culture"),
    "anime-fashion-collabs":   (103, "otaku-culture"),
    "maid-fashion-and-cafes":  (103, "otaku-culture"),
    # Anime Production Industry
    "anime-production-committee-system": (100, "otaku-history"),
    "anime-labor-conditions":            (101, "otaku-history"),
    "anime-overseas-production":         (103, "otaku-history"),
    "cel-to-digital-transition":         (102, "otaku-history"),
    "ova-era-history":                   (101, "otaku-history"),
    "cgi-in-anime-history":              (102, "anime"),
    "anime-streaming-revolution":        (100, "otaku-history"),
    "anime-disc-sales-culture":          (104, "otaku-culture"),
    "anime-production-pipeline":         (103, "otaku-history"),
    # Notable Anime Studios
    "gainax-history":          (98,  "anime"),
    "kyoto-animation-history": (97,  "anime"),
    "studio-ghibli-legacy":    (96,  "anime"),
    "mappa-controversy":       (101, "anime"),
    "trigger-studio":          (102, "anime"),
    "shaft-studio":            (101, "anime"),
    "madhouse-golden-era":     (102, "anime"),
    "toei-animation-history":  (99,  "anime"),
    "sunrise-and-gundam":      (99,  "anime"),
    "production-ig-history":   (101, "anime"),
    "wit-studio":              (103, "anime"),
    "bones-studio":            (101, "anime"),
    # Online Platforms & Communities
    "niconico-douga-history":   (99,  "otaku-history"),
    "pixiv-and-fan-art-culture":(100, "otaku-culture"),
    "narou-web-novel-platform": (100, "otaku-history"),
    "2channel-otaku-culture":   (103, "otaku-history"),
    "twitter-anime-fandom":     (103, "otaku-culture"),
    "mal-and-anime-list-culture":(104, "otaku-culture"),
    # Manga Industry Structure
    "shonen-jump-history":          (98,  "manga"),
    "manga-magazine-ecosystem":     (101, "manga"),
    "manga-editor-culture":         (103, "manga"),
    "manga-magazine-decline":       (102, "manga"),
    "tankobon-vs-magazine-reading": (104, "otaku-culture"),
    # Seiyuu Industry Structure
    "seiyuu-training-schools": (103, "seiyuu"),
    "seiyuu-agency-system":    (103, "seiyuu"),
    "seiyuu-live-events":      (101, "seiyuu"),
    "seiyuu-radio-shows":      (104, "seiyuu"),
    # Anime Conventions & Events
    "comiket-economics":               (101, "otaku-culture"),
    "animejapan-and-tokyo-game-show":  (102, "otaku-culture"),
    "anime-expo-history":              (103, "otaku-culture"),
    "anime-conventions-global":        (103, "otaku-culture"),
    "wonder-festival-history":         (103, "figures"),
    # Touhou Project
    "touhou-project":    (96,  "otaku-culture"),
    "touhou-music-scene":(100, "anime-music"),
    "touhou-and-comiket":(101, "otaku-culture"),
    # Adult content — analytical/historical coverage only
    "ero-manga-history":                      (103, "otaku-history"),
    "hentai-ova-boom":                        (104, "otaku-history"),
    "h-game-industry":                        (102, "otaku-history"),
    "galge-and-dating-sim-history":           (103, "otaku-history"),
    "doujinshi-adult-market":                 (103, "otaku-culture"),
    "japan-obscenity-law-history":            (102, "otaku-history"),
    "adult-content-creators-gone-mainstream": (104, "otaku-history"),
    "eroge-to-mainstream-vn":                 (102, "otaku-history"),
    "r18-doujinshi-and-fandom":               (105, "otaku-culture"),
    # Cosplay
    "world-cosplay-summit":    (110, "cosplay"),
    "cosplay-history-japan":   (105, "cosplay"),
    "cosplay-usa-vs-japan":    (110, "cosplay"),
    "cosplay-as-profession":   (115, "cosplay"),
    "comiket-cosplay-culture": (110, "cosplay"),
    # Idol — individual legendary acts (classic era)
    "momoe-yamaguchi": (83, "idol"),
    "seiko-matsuda":   (79, "idol"),
    "akina-nakamori":  (81, "idol"),
    "kyoko-koizumi":   (89, "idol"),
    "miho-nakayama":   (90, "idol"),
    "shizuka-kudo":    (89, "idol"),
    "yoko-minamino":   (91, "idol"),
    "wink":            (93, "idol"),
    "onyanko-club":    (94, "idol"),
    "hikaru-genji":    (91, "idol"),
    "aya-matsuura":    (89, "idol"),
    "goto-maki":       (91, "idol"),
    # Idol — 48 Group
    "akb48":           (80, "idol"),
    "ske48":           (90, "idol"),
    "nmb48":           (91, "idol"),
    "hkt48":           (91, "idol"),
    "ngt48":           (95, "idol"),
    "stu48":           (96, "idol"),
    "atsuko-maeda":    (86, "idol"),
    "mayu-watanabe":   (87, "idol"),
    "rino-sashihara":  (87, "idol"),
    "jurina-matsui":   (89, "idol"),
    "haruna-kojima":   (90, "idol"),
    "minami-takahashi":(90, "idol"),
    # Idol — 46 Group
    "nogizaka46":  (81, "idol"),
    "sakurazaka46":(89, "idol"),
    "hinatazaka46":(90, "idol"),
    "keyakizaka46":(88, "idol"),
    # Idol — Hello! Project
    "morning-musume":(83, "idol"),
    "angerme":       (93, "idol"),
    "juice-juice":   (93, "idol"),
    "berryz-koubou": (92, "idol"),
    "c-ute":         (92, "idol"),
    # Idol — Stardust
    "momoiro-clover-z":      (86, "idol"),
    "team-syachihoko":       (95, "idol"),
    "shiritsu-ebisu-chuugaku":(94, "idol"),
    # Idol — other major female acts
    "babymetal":       (84, "idol"),
    "perfume":         (85, "idol"),
    "e-girls":         (90, "idol"),
    "tokyo-girls-style":(93, "idol"),
    "fairies":         (94, "idol"),
    "dempagumi-inc":   (93, "idol"),
    "bish":            (91, "idol"),
    "speed":           (91, "idol"),
    "niziu":           (88, "idol"),
    "twice":           (86, "idol"),
    # Idol — Johnny's / male idol acts
    "smap":         (80, "idol"),
    "arashi":       (81, "idol"),
    "kinki-kids":   (87, "idol"),
    "tokio":        (88, "idol"),
    "v6":           (89, "idol"),
    "kanjani8":     (90, "idol"),
    "news-johnnys": (90, "idol"),
    "kattun":       (90, "idol"),
    "hey-say-jump": (91, "idol"),
    "sixtones":     (90, "idol"),
    "snow-man":     (89, "idol"),
    "king-and-prince":(91, "idol"),
    "sexy-zone":    (91, "idol"),
    "be-first":     (91, "idol"),
    # Idol — cultural and historical topics
    "idol-history-1970s":          (102, "idol"),
    "idol-history-1980s":          (100, "idol"),
    "idol-history-1990s":          (100, "idol"),
    "idol-history-2000s":          (100, "idol"),
    "idol-history-2010s":          (100, "idol"),
    "idol-training-audition-system":(102, "idol"),
    "idol-graduation-system":      (103, "idol"),
    "idol-love-ban-rule":          (100, "idol"),
    "idol-scandal-culture":        (100, "idol"),
    "idol-senbatsu-elections":     (103, "idol"),
    "idol-handshake-events":       (105, "idol"),
    "wotagei-culture":             (103, "idol"),
    "idol-oshi-culture":           (100, "idol"),
    "idol-wota-psychology":        (103, "idol"),
    "idol-dark-side":              (103, "idol"),
    "chika-idol-scene":            (104, "idol"),
    "virtual-idol-culture":        (95,  "idol"),
    "idol-overseas-expansion":     (103, "idol"),
    "johnnys-entertainment-history":(95, "idol"),
    "idol-anime-connection":       (102, "idol"),
    "idol-fashion-aesthetics":     (105, "idol"),
    "idol-shashinshuu":            (107, "idol"),
    "idol-concert-culture":        (103, "idol"),
    "idol-fan-club-culture":       (105, "idol"),
    "2point5d-idol":               (100, "idol"),
    "regional-idol-boom":          (104, "idol"),
    "idol-label-history":          (106, "idol"),
    "idol-streaming-era":          (103, "idol"),
    "idol-vs-kpop":                (102, "idol"),
}


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


def load_entity(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main():
    # Load existing topics to preserve scores across re-runs
    existing = {}
    if OUTPUT.exists():
        try:
            existing = json.loads(OUTPUT.read_text())
        except Exception:
            pass

    # Collected: slug -> {"name": str, "type": str, "weight": int}
    # Lowest weight wins for duplicate slugs (franchise deduplication)
    collected = {}

    def merge(slug, name, weight, topic_type):
        if slug not in collected or collected[slug]["weight"] > weight:
            collected[slug] = {"name": name, "type": topic_type, "weight": weight}

    mal_available = MAL_ARCHIVE.exists() and any(MAL_ARCHIVE.iterdir())

    if not mal_available:
        print(f"MAL_Archive not found or empty at {MAL_ARCHIVE} — skipping automated passes.",
              file=sys.stderr)
    else:
        # --- Anime ---
        anime_entries = []
        for f in (MAL_ARCHIVE / "anime/full").glob("*.json"):
            d = load_entity(f)
            members = d.get("members", 0)
            title = (d.get("title_english") or d.get("title") or "").strip()
            if members >= THRESHOLDS["anime"] and title:
                anime_entries.append((title, members))

        max_anime = max(m for _, m in anime_entries) if anime_entries else 1
        for title, members in anime_entries:
            merge(to_slug(title), title, calc_weight(members, THRESHOLDS["anime"], max_anime), "anime")
        print(f"Anime: {len(anime_entries)} entries", file=sys.stderr)

        # --- Manga (excluding LN) ---
        manga_entries = []
        for f in (MAL_ARCHIVE / "manga/full").glob("*.json"):
            d = load_entity(f)
            if d.get("type") == "Light Novel":
                continue
            members = d.get("members", 0)
            title = (d.get("title_english") or d.get("title") or "").strip()
            if members >= THRESHOLDS["manga"] and title:
                manga_entries.append((title, members))

        max_manga = max(m for _, m in manga_entries) if manga_entries else 1
        for title, members in manga_entries:
            merge(to_slug(title), title, calc_weight(members, THRESHOLDS["manga"], max_manga), "manga")
        print(f"Manga: {len(manga_entries)} entries", file=sys.stderr)

        # --- Light Novels ---
        ln_entries = []
        for f in (MAL_ARCHIVE / "manga/full").glob("*.json"):
            d = load_entity(f)
            if d.get("type") != "Light Novel":
                continue
            members = d.get("members", 0)
            title = (d.get("title_english") or d.get("title") or "").strip()
            if members >= THRESHOLDS["ln"] and title:
                ln_entries.append((title, members))

        max_ln = max(m for _, m in ln_entries) if ln_entries else 1
        for title, members in ln_entries:
            merge(to_slug(title), title, calc_weight(members, THRESHOLDS["ln"], max_ln), "light-novel")
        print(f"Light Novels: {len(ln_entries)} entries", file=sys.stderr)

        # --- MAL Personnel (seiyuu, composers, directors, etc.) ---
        people_entries = []
        for f in (MAL_ARCHIVE / "people/full").glob("*.json"):
            d = load_entity(f)
            favorites = d.get("favorites", 0)
            name = (d.get("name") or "").strip()
            if favorites >= THRESHOLDS["people"] and name:
                people_entries.append((name, favorites))

        max_people = max(m for _, m in people_entries) if people_entries else 1
        for name, favorites in people_entries:
            merge(to_slug(name), name, calc_weight(favorites, THRESHOLDS["people"], max_people), "person")
        print(f"MAL Personnel: {len(people_entries)} entries", file=sys.stderr)

        # --- Visual Novels ---
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
            VN_THRESHOLD = 200
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

    # --- Manual entries (always applied; override type/weight for these slugs) ---
    for slug, (weight, topic_type) in MANUAL.items():
        # Manual entries may already exist from automated pass (e.g. a seiyuu slug).
        # Manual type/weight takes precedence for known manual slugs.
        name = collected.get(slug, {}).get("name") or slug_to_name(slug)
        collected[slug] = {"name": name, "type": topic_type, "weight": weight}

    # Build final topics, preserving existing scores
    topics = {}
    for slug, meta in sorted(collected.items()):
        topics[slug] = {
            "name":   meta["name"],
            "type":   meta["type"],
            "weight": meta["weight"],
            "score":  existing.get(slug, {}).get("score", 0),
        }

    OUTPUT.write_text(json.dumps(topics, indent=2, ensure_ascii=False))
    print(f"Generated {len(topics)} total entries -> {OUTPUT}")


if __name__ == "__main__":
    main()
