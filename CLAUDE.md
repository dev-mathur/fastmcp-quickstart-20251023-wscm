# DevStack: operating notes

DevStack is a static Astro site (GitHub Pages) where every book becomes one long-form article.
The full multi-agent operating prompt is in `docs/agent-prompt.md`. Read it at the start of a session.

## Commands
- `npm run dev` / `npm run preview`
- `npm run validate` (content rules; also runs before every build)
- `npm run build`
- Ingestion: `python tools/extract.py <book.pdf|epub> --out work/<slug>` (see tools/requirements.txt)

## Rules that must not break
- Every internal link goes through `url()` from `src/lib/paths.ts` (site lives under `/devstack/`).
- Topics come from `src/data/taxonomy.json`; navigation is generated from content. A new book needs no code changes.
- Article `title` must equal `book.title` exactly; the angle goes in `subtitle`.
- Article structure: `## Overview`, `## Chapter Summaries` (or one `## Part ...` H2 per part), `## Themes and Analysis`, `## Test Yourself`.
- Every chapter has its own `### Chapter N: Exact Title` subheading, in book order, with a detailed present-tense summary
  and a closing `> **Key takeaway.** ...`. The validator fails the build on a missing chapter heading and warns under 100 words.
- Articles: `src/content/books/<kebab-slug>.md`, no H1, no H4, pull quotes 15 words or fewer, recall questions as `<details><summary>` blocks.
- Never commit `work/`, source PDFs/EPUBs, or extracted chapter text.
- Sample articles carry `sample: true`. Delete them after the first real ingest.
- A change is done only when `npm run validate` and `npm run build` pass.
