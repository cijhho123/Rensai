# Article Generation

## Overview

A remote Claude agent runs on a cron schedule, selects a topic, researches it online,
writes a Markdown article, and pushes it to the repo. GitHub Actions builds and deploys
the site automatically on every push.

Full prompt: `routine/article-prompt.md`

## Quality Standard

Articles are not summaries or recaps. Every piece takes a specific angle and defends
a real position. The target is writing that reads like a passionate, knowledgeable fan
who is also a sharp critical thinker — not Wikipedia, not a press release.

Examples of the intended level:
- Psychological portrait of a character (Asuka Langley Soryu's trauma coded through
  behavior and design)
- Deconstruction of a trope through a specific work (Akane Kurokawa dismantling the
  yandere archetype in Oshi no Ko)
- Industry retrospective with a thesis (how Gainax's collapse shaped every studio
  after it)
- Cultural analysis (the maid cafe as a formalization of parasocial desire)

## Workflow Per Run

1. `python routine/get_next_topic.py` — get the lowest-score topic slug
2. Read `topic-log/{topic}.txt` — check previously covered angles, do not repeat
3. Read `routine/recent.txt` — recency guard, avoid writing something too similar to the last 20 titles
4. Web research — primary sources, interviews, production history, fan discourse
5. If research is thin: fall back to MAL reviews, Reddit, fan wikis, translated interviews
6. Surface additional angles — write multiple articles per run if the research warrants it
7. Log thin news items to `routine/news-notes.txt` (one line each, harvested by weekly agent)
8. For each article:
   - Pick one specific angle
   - Determine category and build tags
   - Write 700-1100 words
   - Save to `content/post/YYYY-MM-DD-{slug}/index.md`
   - `git add` + `git commit -m "Daily: {title}"`
9. `git push origin main` — one push for all article commits
10. Update state in one final commit:
    - `python routine/update_topic_score.py {slug}` per topic written
    - Append to `topic-log/{topic}.txt`
    - Prepend to `routine/recent.txt` (trim to 20 lines)
    - `git add` + `git commit -m "State: ..."` + `git push`

## Categories

`Anime` | `Manga` | `Light Novel` | `Visual Novel` | `Seiyuu` |
`Anime Music` | `Figures & Merchandise` | `Cosplay` | `Idol` | `Otaku History` | `Otaku Culture` |
`Events & Collaborations`

## Angles

The prompt provides a reference list of angle types (character-analysis, retrospective,
deconstruction, biography, incident, anniversary, etc.) but explicitly frames them as
inspiration, not a closed set. The agent is instructed to use whatever angle the
material calls for.

## Article Format

```yaml
---
title: "Article Title Here"
description: "One sharp sentence — the specific claim or angle."
slug: topic-angle-slug
date: YYYY-MM-DDTHH:MM:SS+0000
categories:
    - Anime
tags:
    - tag-one
    - tag-two
---
```

Path: `content/post/YYYY-MM-DD-{slug}/index.md`

## State Files

| File | Updated by article agent |
|---|---|
| `routine/topics.json` | Score incremented per topic written |
| `topic-log/{slug}.txt` | One line appended per article |
| `routine/recent.txt` | Title prepended, trimmed to 20 lines |
| `routine/news-notes.txt` | Thin news items appended |
