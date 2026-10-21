# DevStack

A Substack-style reading site where each book becomes one long, detailed article. Built with Astro, deployed to GitHub Pages.

## Run it
```bash
npm install
npm run dev
```

## Add a book
Use the agent workflow in `docs/agent-prompt.md`: attach the PDF or EPUB in a Claude Code session and say
"Ingest this book." The ingestion agent extracts the text (`tools/extract.py`), writes the article, registers the topic,
tags, and navigation, validates, builds, and deploys.

## Deploy
1. Push `main` to this repository.
2. Repository Settings, Pages, Source: **GitHub Actions**.
3. `.github/workflows/deploy.yml` builds and publishes on every push to `main`.

Using another repo name or a custom domain? Set `SITE_URL` and `BASE_PATH` (see `astro.config.mjs`).

## Layout
See the project map in `docs/agent-prompt.md`.
