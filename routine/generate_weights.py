# routine/generate_weights.py
# Run from the Rensai repo root on the machine with MAL_Archive data.
# Requires: pip install zstandard
# MAL_Archive path: C:/Users/benka/git/MAL_Archive/data/raw
# VNDB dump: vndb-db-*.tar.zst (in repo root)
# Outputs: routine/weights.json

import json
import math
import re
import sys
from pathlib import Path

MAL_ARCHIVE = Path("C:/Users/benka/git/MAL_Archive/data/raw")
OUTPUT = Path("routine/weights.json")

THRESHOLDS = {
    "anime":   10_000,
    "manga":   5_000,
    "ln":      3_000,
    "people":  500,
}

MANUAL = {
    # Anime Music
    "anison-composers": 95,
    "anime-op-ed": 90,
    "anime-soundtracks": 100,
    "anime-movie-soundtracks": 105,
    "anison-history": 100,
    "vocaloid-culture": 95,
    "idol-anime-music": 105,
    "seiyuu-who-sing": 110,
    "anime-bands": 110,
    "anison-labels": 115,
    # Otaku History/Culture
    "otaku-history-1980s": 100,
    "otaku-history-1990s": 100,
    "otaku-history-2000s": 100,
    "moe-culture": 100,
    "fansub-era": 110,
    "akihabara-culture": 100,
    "comiket-history": 100,
    "otaku-bashing": 110,
    "isekai-boom": 100,
    "vtuber-culture": 90,
    "idol-culture": 95,
    "fujoshi-culture": 105,
    "anime-overseas-spread": 100,
    "doujinshi-culture": 105,
    "light-novel-boom": 105,
    "anime-piracy-history": 110,
    "gacha-and-anime-franchises": 105,
    # Otaku Districts & Physical Spaces
    "akihabara-electronics-to-anime": 102,
    "akihabara-2008-and-after": 104,
    "nakano-broadway": 103,
    "ikebukuro-otome-road": 102,
    "nipponbashi-den-den-town": 103,
    "otaku-tourism": 102,
    "anime-location-pilgrimages": 103,
    # Maid Cafes & Concept Cafes
    "maid-cafe-history": 101,
    "maid-cafe-industry": 103,
    "maid-cafe-overseas": 104,
    "butler-cafe-culture": 105,
    "concept-cafe-evolution": 103,
    "anime-themed-cafes": 103,
    # Arcades & Game Centers
    "game-center-culture": 101,
    "rhythm-game-culture": 102,
    "crane-game-culture": 103,
    "arcade-fighting-game-scene": 103,
    "arcade-decline-and-survival": 104,
    # Otaku Retail & Collecting
    "doujinshi-shops": 103,
    "figure-collecting-culture": 101,
    "retro-anime-goods-collecting": 103,
    "blind-box-culture": 102,
    "gashapon-history": 103,
    # Japanese Fashion & Street Culture
    "lolita-fashion": 100,
    "gothic-lolita": 103,
    "sweet-lolita": 103,
    "classic-lolita": 104,
    "wa-lolita": 106,
    "jirai-kei": 101,
    "menhera-kei": 103,
    "yami-kawaii": 102,
    "decora-fashion": 104,
    "fairy-kei": 105,
    "otome-kei": 105,
    "mori-girl": 106,
    "dolly-kei": 107,
    "gyaru-culture": 101,
    "kogal": 103,
    "ganguro": 103,
    "himegyaru": 104,
    "visual-kei-fashion": 102,
    "harajuku-fashion-history": 100,
    "fruits-magazine": 104,
    "ura-harajuku": 105,
    "angura-kei": 107,
    "kawaii-as-cultural-export": 100,
    "anime-fashion-collabs": 103,
    "maid-fashion-and-cafes": 103,
    # Anime Production Industry
    "anime-production-committee-system": 100,
    "anime-labor-conditions": 101,
    "anime-overseas-production": 103,
    "cel-to-digital-transition": 102,
    "ova-era-history": 101,
    "cgi-in-anime-history": 102,
    "anime-streaming-revolution": 100,
    "anime-disc-sales-culture": 104,
    "anime-production-pipeline": 103,
    # Notable Anime Studios
    "gainax-history": 98,
    "kyoto-animation-history": 97,
    "studio-ghibli-legacy": 96,
    "mappa-controversy": 101,
    "trigger-studio": 102,
    "shaft-studio": 101,
    "madhouse-golden-era": 102,
    "toei-animation-history": 99,
    "sunrise-and-gundam": 99,
    "production-ig-history": 101,
    "wit-studio": 103,
    "bones-studio": 101,
    # Online Platforms & Communities
    "niconico-douga-history": 99,
    "pixiv-and-fan-art-culture": 100,
    "narou-web-novel-platform": 100,
    "2channel-otaku-culture": 103,
    "twitter-anime-fandom": 103,
    "mal-and-anime-list-culture": 104,
    # Manga Industry Structure
    "shonen-jump-history": 98,
    "manga-magazine-ecosystem": 101,
    "manga-editor-culture": 103,
    "manga-magazine-decline": 102,
    "tankobon-vs-magazine-reading": 104,
    # Seiyuu Industry Structure
    "seiyuu-training-schools": 103,
    "seiyuu-agency-system": 103,
    "seiyuu-live-events": 101,
    "seiyuu-radio-shows": 104,
    # Anime Conventions & Events
    "comiket-economics": 101,
    "animejapan-and-tokyo-game-show": 102,
    "anime-expo-history": 103,
    "anime-conventions-global": 103,
    "wonder-festival-history": 103,
    # Touhou Project
    "touhou-project": 96,
    "touhou-music-scene": 100,
    "touhou-and-comiket": 101,
    # Adult content — analytical/historical coverage only
    "ero-manga-history": 103,
    "hentai-ova-boom": 104,
    "h-game-industry": 102,
    "galge-and-dating-sim-history": 103,
    "doujinshi-adult-market": 103,
    "japan-obscenity-law-history": 102,
    "adult-content-creators-gone-mainstream": 104,
    "eroge-to-mainstream-vn": 102,
    "r18-doujinshi-and-fandom": 105,
    # Cosplay
    "world-cosplay-summit": 110,
    "cosplay-history-japan": 105,
    "cosplay-usa-vs-japan": 110,
    "cosplay-as-profession": 115,
    "comiket-cosplay-culture": 110,
    # Idol — individual legendary acts (classic era)
    "momoe-yamaguchi": 83,
    "seiko-matsuda": 79,
    "akina-nakamori": 81,
    "kyoko-koizumi": 89,
    "miho-nakayama": 90,
    "shizuka-kudo": 89,
    "yoko-minamino": 91,
    "wink": 93,
    "onyanko-club": 94,
    "hikaru-genji": 91,
    "aya-matsuura": 89,
    "goto-maki": 91,
    # Idol — 48 Group
    "akb48": 80,
    "ske48": 90,
    "nmb48": 91,
    "hkt48": 91,
    "ngt48": 95,
    "stu48": 96,
    "atsuko-maeda": 86,
    "mayu-watanabe": 87,
    "rino-sashihara": 87,
    "jurina-matsui": 89,
    "haruna-kojima": 90,
    "minami-takahashi": 90,
    # Idol — 46 Group
    "nogizaka46": 81,
    "sakurazaka46": 89,
    "hinatazaka46": 90,
    "keyakizaka46": 88,
    # Idol — Hello! Project
    "morning-musume": 83,
    "angerme": 93,
    "juice-juice": 93,
    "berryz-koubou": 92,
    "c-ute": 92,
    # Idol — Stardust
    "momoiro-clover-z": 86,
    "team-syachihoko": 95,
    "shiritsu-ebisu-chuugaku": 94,
    # Idol — other major female acts
    "babymetal": 84,
    "perfume": 85,
    "e-girls": 90,
    "tokyo-girls-style": 93,
    "fairies": 94,
    "dempagumi-inc": 93,
    "bish": 91,
    "speed": 91,
    "niziu": 88,
    "twice": 86,
    # Idol — Johnny's / male idol acts
    "smap": 80,
    "arashi": 81,
    "kinki-kids": 87,
    "tokio": 88,
    "v6": 89,
    "kanjani8": 90,
    "news-johnnys": 90,
    "kattun": 90,
    "hey-say-jump": 91,
    "sixtones": 90,
    "snow-man": 89,
    "king-and-prince": 91,
    "sexy-zone": 91,
    "be-first": 91,
    # Idol — cultural and historical topics
    "idol-history-1970s": 102,
    "idol-history-1980s": 100,
    "idol-history-1990s": 100,
    "idol-history-2000s": 100,
    "idol-history-2010s": 100,
    "idol-training-audition-system": 102,
    "idol-graduation-system": 103,
    "idol-love-ban-rule": 100,
    "idol-scandal-culture": 100,
    "idol-senbatsu-elections": 103,
    "idol-handshake-events": 105,
    "wotagei-culture": 103,
    "idol-oshi-culture": 100,
    "idol-wota-psychology": 103,
    "idol-dark-side": 103,
    "chika-idol-scene": 104,
    "virtual-idol-culture": 95,
    "idol-overseas-expansion": 103,
    "johnnys-entertainment-history": 95,
    "idol-anime-connection": 102,
    "idol-fashion-aesthetics": 105,
    "idol-shashinshuu": 107,
    "idol-concert-culture": 103,
    "idol-fan-club-culture": 105,
    "2point5d-idol": 100,
    "regional-idol-boom": 104,
    "idol-label-history": 106,
    "idol-streaming-era": 103,
    "idol-vs-kpop": 102,
}


def to_slug(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s-]", "", title)
    return re.sub(r"[\s]+", "-", title.strip())


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
    weights = {}

    if not MAL_ARCHIVE.exists():
        print(f"MAL_Archive not found at {MAL_ARCHIVE} — skipping automated passes.", file=sys.stderr)
        print("Writing manual-only weights.json.", file=sys.stderr)
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
            slug = to_slug(title)
            w = calc_weight(members, THRESHOLDS["anime"], max_anime)
            if slug not in weights or weights[slug] > w:
                weights[slug] = w
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
            slug = to_slug(title)
            w = calc_weight(members, THRESHOLDS["manga"], max_manga)
            if slug not in weights or weights[slug] > w:
                weights[slug] = w
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
            slug = to_slug(title)
            w = calc_weight(members, THRESHOLDS["ln"], max_ln)
            if slug not in weights or weights[slug] > w:
                weights[slug] = w
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
            slug = to_slug(name)
            w = calc_weight(favorites, THRESHOLDS["people"], max_people)
            if slug not in weights or weights[slug] > w:
                weights[slug] = w
        print(f"MAL Personnel: {len(people_entries)} entries", file=sys.stderr)

        # --- Visual Novels (from VNDB dump in repo root) ---
        vndb_dumps = sorted(Path(".").glob("vndb-db-*.tar.zst"))
        if vndb_dumps:
            try:
                import zstandard
                import tarfile as tarlib
            except ImportError:
                print("zstandard not installed — skipping VN pass. Run: pip install zstandard", file=sys.stderr)
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
                                    vid, lang, official, title, latin = cols[0], cols[1], cols[2], cols[3], cols[4]
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
                slug = to_slug(title)
                w = calc_weight(votes, VN_THRESHOLD, max_vn)
                if slug not in weights or weights[slug] > w:
                    weights[slug] = w
                vn_count += 1
            print(f"Visual Novels: {vn_count} entries", file=sys.stderr)
        else:
            print("No VNDB dump found — skipping VN pass.", file=sys.stderr)

    # --- Manual entries (always applied, override automated weights for manual slugs) ---
    for slug, w in MANUAL.items():
        weights[slug] = w

    weights = dict(sorted(weights.items()))
    OUTPUT.write_text(json.dumps(weights, indent=2, ensure_ascii=False))
    print(f"Generated {len(weights)} total entries -> {OUTPUT}")


if __name__ == "__main__":
    main()
