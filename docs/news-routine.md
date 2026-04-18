# Weekly News Routine

## Overview

Once per week a remote Claude agent writes a news roundup covering the past 7 days
across all blog categories.

Full prompt: `routine/news-prompt.md`

## Coverage

8-12 items per roundup, 900-1400 words total, across all categories:

- **Anime**: adaptations, studio news, production controversies, streaming deals
- **Manga**: new series, final chapters, author news, magazine changes
- **Light Novels**: new volumes, adaptation announcements, author milestones
- **Visual Novels**: new releases, localizations, remasters, developer news
- **Seiyuu**: casting news, live events, graduations, deaths
- **Anime Music**: album/single releases, artist announcements, notable tie-ups
- **Figures & Merchandise**: major figure announcements, collab drops, limited releases
- **Cosplay**: competition results, notable cosplayer news, event announcements
- **Idol**: group announcements, graduations, scandals, concert news
- **Otaku History & Culture**: anniversary milestones, exhibitions, cultural shifts

No single category dominates. A seiyuu passing is as valid a lead item as a major
anime announcement.

## Workflow

1. Web research — find the most significant news from the past 7 days, independently,
   with no prior constraints to avoid biasing the search
2. Write the roundup (900-1400 words, one H2 section per item, inline sources)
3. `git add` + `git commit` + `git push`
4. Read `routine/news-notes.txt` — sanity check for items article agents logged this
   week; the article is already published, this step is read-only
5. Write today's date to `routine/last-news-post.txt`
6. Clear `routine/news-notes.txt` (write empty file — refills during the coming week)
7. `git add` + `git commit` + `git push`

## News-Notes Pipeline

Article agents (running hourly) append thin news items to `routine/news-notes.txt`
as they encounter them during research:

```
Format: "YYYY-MM-DD: {one sentence summary} — {source URL}"
```

The news agent reads this file *after* writing its own article to avoid biasing its
independent research. After the sanity check, it clears the file so it refills fresh
for the next week.

## Article Format

```yaml
---
title: "This Week in Anime & Manga - Month Day, Year"
description: "Weekly roundup of notable anime, manga, and otaku culture news."
slug: weekly-news-YYYY-MM-DD
date: YYYY-MM-DDTHH:MM:SS+0000
categories:
    - Weekly News
tags:
    - news
    - weekly
    - spring-2026
    - any-franchises-or-people-mentioned
---
```

Path: `content/post/YYYY-MM-DD-weekly-news/index.md`
