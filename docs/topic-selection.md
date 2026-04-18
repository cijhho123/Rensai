# Topic Selection System

## Data Model

All topics live in a single file: `routine/topics.json`.
Each key is a kebab-case slug. Each value has four fields:

```json
{
  "clannad": {
    "name": "Clannad",
    "type": ["anime", "manga", "visual-novel"],
    "weight": 90,
    "score": 0
  }
}
```

| Field | Purpose |
|---|---|
| `name` | Display name used in logging |
| `type` | Array of relevant mediums: `anime`, `manga`, `light-novel`, `visual-novel`, `person`, `character`, `producer`, `idol`, `anime-music`, `otaku-culture`, `otaku-history`, `cosplay`, `figures`. Topics spanning multiple mediums have multiple entries. |
| `weight` | Score increment per article written. Lower = more frequent. |
| `score` | Accumulated total. Selection picks from the lowest-score pool. |

## Selection Algorithm

`routine/get_next_topic.py`:
1. Load all topics
2. Find the minimum score across all entries
3. Collect every topic at that minimum
4. Return one at random (prints slug, name, and types)

This is a weighted round-robin. Low-weight topics return to the minimum pool faster
than high-weight ones, so they appear proportionally more often over time.

## Score Update

After writing an article, run:
```
python routine/update_topic_score.py {slug}
```

This increments `score += weight` for that slug. If the slug does not exist in
`topics.json`, it is auto-created with `weight=100, score=0, type=["anime"]` as defaults.

## Initial State

On first deploy:
- All non-manual topics: `score = 1`
- All manual topics (otaku-culture, idol, anime-music, etc.): `score = 0`
- Specific high-priority franchises (Evangelion, Attack on Titan, Higurashi, Rascal
  Does Not Dream): `score = 0`

This ensures the blog opens with curated cultural topics and priority franchises
before cycling into the full automated catalogue. Long-tail entries (below main
thresholds) start with score 150-600 and weight 250-1200, so they trickle in gradually.

## Adding New Topics

**Option A — Manually**: edit `topics.json` directly and add an entry with the desired
weight and `score = 0`.

**Option B — Via `update_topic_score.py`**: pass any new slug to the script; it will
be auto-created with default weight 100.

**Option C — Re-run `generate_weights.py`**: when new source data is available (new
MAL archive zips, VNDB dump). Existing scores are preserved; only weights and names
are updated. See `docs/weight-generation.md`.
