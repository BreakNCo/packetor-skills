---
name: blog-content-publish
description: Create, SEO-optimize, optionally humanize, internally link, and save a draft blog article to Packets Payload CMS. Use when given a keyword or topic for packets.build blog content. Never publishes.
version: 1.1.0
compatibility: openclaw
tools:
  - firecrawl
---

# Blog content publish

Keyword → research → write → optional humanize → internal links → SEO score → **save as draft** in Payload. A human always reviews and publishes in `/admin`.

**This skill never sets `_status: "published"`.** `cms-tools/scripts/create-draft-article.ts` hardcodes `_status: "draft"` and rejects any other status. Publishing is a manual `/admin` action.

## When to Use

- "Write a blog draft for 'SOC 2 for AI startups'"
- "SEO-optimize this keyword and save it to Payload as a draft"
- "Create a Packets blog post from these notes"
- Any request to produce packets.build article content that should land in CMS as a draft

## When NOT to Use

- Publishing or scheduling a live post — stop after draft; the user publishes
- Website marketing pages (`/solutions/*`, homepage copy) — not the Articles collection
- LinkedIn / Reddit / email content — different skills
- Bulk generating dozens of posts in one go without review

## Prerequisites

**Repo:** this skill only (`packetor-skills/blog-content-publish`). CMS writes use the vendored CLI in `cms-tools/` — a `packets-website` checkout is **not** required.

**One-time install:**

```bash
cd blog-content-publish/cms-tools && bun install
```

**Environment:** set `DATABASE_URI` and `PAYLOAD_SECRET` in `packetor-skills/.env` (or the process environment). Shell env vars win over `.env` file values. Humanizer keys in the same `.env` are loaded automatically.

**MCP:** Firecrawl for research. Writing uses the model selected in Cursor / Claude UI — no extra LLM key required.

**Optional humanizer credentials (own accounts / API keys, never Toolzbuy session cookies):**

| Provider | Env |
| --- | --- |
| Smodin | `SMODIN_API_KEY` |
| WordAI | `WORDAI_EMAIL`, `WORDAI_API_KEY` |
| Spin Rewriter | `SPINREWRITER_EMAIL`, `SPINREWRITER_API_KEY` |
| WriteHuman | `WRITEHUMAN_API_KEY` |
| StealthWriter | `STEALTHWRITER_API_KEY` |
| QuillBot (unofficial SDK) | `QUILLBOT_EMAIL`, `QUILLBOT_PASSWORD` |

QuillBot also needs `pip install quillbot` into a workspace `.venv` (one-time; the script no-ops the venv re-exec if none exists).

**Python:** stdlib only except the optional `quillbot` extra.

## Pipeline

```
[1] plan_article.py         keyword/notes → slug/category/title/outline/searchIntent
      ↓
[2] Agent research          Firecrawl MCP tools, called directly
      ↓
[3] Agent writes prose HTML h1/h2/h3/p/strong/em only — no links yet
      ↓
[4] humanize.py [optional]  rewrite pass on prose (llm/none/API-provider/manual:*)
      ↓
[5] fetch_link_targets.py   ranks CTA + internal + published articles
      ↓
[6] Agent inserts links     internal links, external citations, CTA, FAQ section
      ↓
[7] run_cms.py score        dry-run score, no CMS write
      ↓
[8] Agent iterates 5–7      until score >= config.targetSeoScore (default 85), max 3 passes
      ↓
[9] run_cms.py draft        upsert as _status: "draft" (ask the user first)
      ↓
[10] Report to user         adminUrl + score + failed checks + placeholder-author reminder
```

Humanizing **never** runs over `<a href>` markup. Links go in after the rewrite.

### Dry-run mode

If the user asks for a dry run, or has not confirmed a CMS write: stop after step 7. Do **not** call `run_cms.py draft`. Return the HTML, score, and checklist.

## Script usage

Run Python from `blog-content-publish/` (or with paths as shown). JSON on stdin.

```bash
printf '%s' '{"keyword":"SOC 2 for AI startups","notes":"questionnaire AI section"}' \
  | python3 scripts/plan_article.py
```

```bash
printf '%s' '{"provider":"llm","text":"<prose without links>"}' \
  | python3 scripts/humanize.py
```

```bash
printf '%s' '{"primaryKeyword":"SOC 2 for AI startups","category":"soc-2-for-ai-companies"}' \
  | python3 scripts/fetch_link_targets.py
```

Vendored CMS CLI (from `blog-content-publish/` — loads `packetor-skills/.env`):

```bash
printf '%s' '<score json>' | python3 scripts/run_cms.py score
printf '%s' '<draft json>' | python3 scripts/run_cms.py draft
python3 scripts/run_cms.py link-targets
```

## Humanizer flags

Default: `llm` (`config.humanizerDefault`). Honour `--humanizer <provider>` from the user.

| Flag | Behaviour |
| --- | --- |
| `llm` | Script returns rewrite instructions; the agent rewrites in-context |
| `none` | Pass-through |
| `smodin` / `wordai` / `spinrewriter` / `writehuman` / `stealthwriter` | HTTP API; skip + suggest `llm` if env vars missing |
| `quillbot` | Unofficial SDK; own QuillBot login only |
| `manual:phrasly` / `manual:humanizer-tech` / `manual:toolzbuy-ai-humanizer` | Dashboard instructions, no automation |

Toolzbuy Advance includes browser sessions for several humanizers. Those sessions are **not** API credentials. If an API provider skips, fall back to `llm` unless the user asked for `manual:*`.

## Writing template

Supported HTML only (the Lexical converter **throws** on anything else): `h1`, `h2`, `h3`, `p`, `a`, `ul`, `li`, `strong`, `em`.

```html
<h1>{primary keyword, naturally phrased}</h1>
<p>Hook — security questionnaire / deal stall for AI-native SaaS.</p>
<h2>...</h2>
<p>...</p>
<h2>Frequently asked questions</h2>
<h3>Question?</h3>
<p>Answer.</p>
<p>CTA with <a href="/audit-readiness">free audit score</a>.</p>
```

Length: roughly 1200–1800 words. Exactly one H1. Read `references/positioning-guardrails.md` before drafting. Read `references/seo-checklist.md` before scoring.

Default author/reviewer slug: `hello-packets` (placeholder). **Flag this in the final report.** Replace with a named specialist Person before anyone publishes.

## Score JSON (cms:score stdin)

Include `title`, `slug`, `excerpt`, `bodyHtml`, `authorSlug`, `reviewerSlug`, `featuredImageAlt`, and `seo.primaryKeyword` / `metaTitle` / `metaDescription` / `canonicalPath`.

## Draft JSON (`run_cms.py draft` stdin)

Same fields plus `categorySlug`, optional `tags[]` and `relatedArticleSlugs[]`. Do not send `status`/`_status` other than `draft`.

## Error handling

Scripts print JSON. Logs belong on stderr.

| Code / error | What to do |
| --- | --- |
| `keyword is required` | Ask the user for a primary keyword |
| `CMS_TOOLS_NOT_INSTALLED` | Run `cd blog-content-publish/cms-tools && bun install` |
| `LINK_TARGETS_FAILED` / missing `DATABASE_URI` | Set `DATABASE_URI` and `PAYLOAD_SECRET` in `packetor-skills/.env`; do not save a draft with zero internal links |
| `Unsupported HTML tag` | Strip the tag; converter allowlist is strict |
| `Refusing non-draft status` | Remove publish flags from the payload |
| Humanizer `status: skipped` | Use `llm` fallback; tell the user which env var was missing |

## Example invocation

> Write a blog draft for primary keyword "SOC 2 for AI startups" with notes: focus on the security questionnaire AI section, compare to tool-only approaches. Humanizer: llm. Save as draft.

## References

- `references/seo-checklist.md` — scorer weights and FAQ note
- `references/positioning-guardrails.md` — banned words and beachhead
- `references/payload-api.md` — vendored cms-tools writes, not REST
- `cms-tools/SOURCE.md` — how to re-sync from packets-website
