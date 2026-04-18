# Weight Generation

## Overview

`routine/generate_weights.py` populates `routine/topics.json` from MAL archive data,
VNDB dump, and manual entries. It is run manually on a machine that has the source
data, and the resulting `topics.json` is committed to the repo.

The script is safe to re-run at any time: **existing scores are always preserved**.
Only weights and names are updated. If a data source is absent, entries from that
source survive unchanged from the previous run.

## Running the Script

```bash
# From the repo root, with source data present:
python routine/generate_weights.py
```

Output goes to `routine/topics.json`. Stderr shows per-category entry counts.

## Data Sources

| Category | Source | Metric | Gate |
|---|---|---|---|
| Anime | `temp-data/mal-archives/anime/full.zip` | `favorites * (score or 7.0)` | favorites >= 500 |
| Manga | `temp-data/mal-archives/manga/full.zip` | `favorites * (score or 7.0)` | favorites >= 500 |
| Light Novel | same zip, `type == "Light Novel"` | `favorites * (score or 7.0)` | favorites >= 500 |
| People | `temp-data/mal-archives/people/full.zip` | `favorites` | favorites >= 1000 |
| Characters | `temp-data/mal-archives/characters/full.zip` | `favorites` | favorites >= 1500 |
| Producers | `temp-data/mal-archives/producers/full.zip` | `favorites` | favorites >= 1000 |
| Visual Novels | `vndb-db-*.tar.zst` in repo root | `c_votecount` | votes >= 100 |

`temp-data/` is gitignored. The zips are large and only needed at generation time.
The VNDB dump is also gitignored — place it in repo root, run the script, then delete it.

## Weight Formula

```python
metric = favorites * (mal_score or 7.0)   # for anime/manga/LN
# or just favorites for people/characters/producers/VN

weight = clamp(
    round(150 - (log10(metric) - log10(min_metric)) /
                (log10(max_metric) - log10(min_metric)) * 90),
    60, 150
)
```

This maps the metric distribution logarithmically to the 60-150 range:
- Highest metric in category → weight ~60 (most frequent)
- Lowest qualifying metric → weight ~150 (least frequent)

## Manual Entries

Manual topics (idol groups, otaku culture topics, anime studios, etc.) were defined
with explicit weights and baked into `topics.json` on the initial run. They are no
longer in the script — `topics.json` is now the source of truth for them.

After generation, manual topic weights were multiplied by 0.75 to make them appear
more frequently than the long tail of automated entries.

## Adding Future Data Sources

When new source data becomes available (e.g., a companies/studios MAL archive, or
an updated VNDB dump):

1. Place the data in `temp-data/mal-archives/{category}/full.zip` or repo root (VNDB)
2. Add a corresponding pass in `generate_weights.py` following the existing pattern
3. Run the script — new entries are added, existing scores preserved
4. Commit `topics.json`
5. Delete the source data files (they are gitignored, but keep the repo clean)

## Slug Generation

```python
slug = re.sub(r"[^a-z0-9\s-]", "", title.lower())
slug = re.sub(r"[\s]+", "-", slug.strip())
```

Kebab-case, ASCII only, no special characters. Duplicate slugs within a category
keep the lower weight (better metric wins).
