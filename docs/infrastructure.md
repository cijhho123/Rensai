# Infrastructure

## Site

- **Framework**: Hugo with the Stack theme
- **Hosting**: GitHub Pages
- **Deploy**: GitHub Actions — triggers on every push to `main`, runs `hugo --minify`,
  publishes to the `gh-pages` branch automatically
- **Repo**: https://github.com/cijhho123/Rensai

## Scheduled Agents

Two remote Claude Code agents (CCR) run on Anthropic's cloud infrastructure.
Each trigger spawns a fully isolated remote session that clones the repo, runs the
routine, commits, and pushes. The session has no persistent state between runs —
all state lives in the repo itself.

| Agent | Prompt |
|---|---|
| Article generation | `routine/article-prompt.md` |
| Weekly news | `routine/news-prompt.md` |

Manage triggers at: https://claude.ai/code/scheduled

## Repo Auth

Agents authenticate to GitHub via a PAT embedded in the git source URL:
`https://{PAT}@github.com/cijhho123/Rensai`

The PAT requires Contents read+write permission on the repo.

## Tools Available to Agents

`Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, `WebSearch`, `WebFetch`

No MCP connectors. Web search uses the built-in WebSearch/WebFetch tools.

## Content Pipeline

```
Remote agent runs
    -> selects topic from topics.json
    -> researches online (WebSearch / WebFetch)
    -> writes article to content/post/YYYY-MM-DD-{slug}/index.md
    -> commits + pushes to main
    -> GitHub Actions triggers Hugo build
    -> site published to GitHub Pages
```

## File Layout

```
routine/
    topics.json           # all topics: slug -> {name, type, weight, score}
    get_next_topic.py     # selection script
    update_topic_score.py # score update script (auto-adds unknown slugs)
    generate_weights.py   # regenerates topics.json from source data (run manually)
    article-prompt.md     # prompt for the hourly article agent
    news-prompt.md        # prompt for the weekly news agent
    recent.txt            # last 20 article titles (recency guard)
    last-news-post.txt    # ISO date of last news post
    news-notes.txt        # thin news items buffered from article agents to weekly news

topic-log/
    {slug}.txt            # one line per covered angle, created lazily by article agent

content/
    post/
        YYYY-MM-DD-{slug}/
            index.md      # Hugo page bundle — one directory per article

docs/                     # design documentation (this folder)
```
