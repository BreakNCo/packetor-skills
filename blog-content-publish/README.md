# blog-content-publish

Create SEO-optimized blog drafts for [packets.build](https://packets.build) and save them to Payload CMS as **drafts only**. A human reviews and publishes in `/admin`.

This skill lives in `packetor-skills` and does **not** require a `packets-website` checkout. CMS reads/writes use a vendored CLI in `cms-tools/`.

## What it does

```
keyword → plan → research → write → [humanize] → internal links → SEO score → save draft
```

- Targets the **Articles** collection (blog posts), not marketing pages.
- Never sets `_status: "published"`.
- Default author/reviewer slug is `hello-packets` (placeholder — replace before publish).

## Requirements

| Tool | Purpose |
| --- | --- |
| **Python 3** | Orchestration scripts (`scripts/`) |
| **Bun** | Vendored Payload CLI (`cms-tools/`) |
| **Firecrawl MCP** | Research (when using an agent in Cursor / Claude) |
| **Postgres credentials** | Same `DATABASE_URI` + `PAYLOAD_SECRET` as production Payload |

Optional: humanizer API keys or QuillBot login (see below).

## Setup

### 1. Clone and install the CMS CLI

From the `packetor-skills` repo root:

```bash
cd blog-content-publish/cms-tools
bun install
```

You only need to do this once (or after dependency updates).

### 2. Configure environment

Copy the example env file at the repo root:

```bash
cp ../.env.example ../.env
```

Edit `packetor-skills/.env`:

```bash
DATABASE_URI=postgresql://...   # Payload Postgres (production or dev)
PAYLOAD_SECRET=...            # Payload secret
```

Shell environment variables override `.env` if both are set.

Optional humanizer keys can go in the same file — `humanize.py` and the CMS wrappers load them automatically.

### 3. Verify the install

From `blog-content-publish/`:

```bash
# Scorer only — no database needed
printf '%s' '{"title":"Test","slug":"test","excerpt":"At least fifty characters for the meta description floor check.","bodyHtml":"<h1>Test</h1><p>Body.</p>","authorSlug":"hello-packets","reviewerSlug":"hello-packets","featuredImageAlt":"alt","seo":{"primaryKeyword":"test","metaTitle":"Test","metaDescription":"At least fifty characters for the meta description floor check.","canonicalPath":"/blog/test"}}' \
  | python3 scripts/run_cms.py score

# Link targets — needs DATABASE_URI + PAYLOAD_SECRET
python3 scripts/run_cms.py link-targets | head
```

If you see `CMS_TOOLS_NOT_INSTALLED`, run `bun install` in `cms-tools/` again.

## Using with an agent

In Cursor or Claude Code, invoke the skill by describing the task, for example:

> Write a blog draft for primary keyword "SOC 2 for AI startups" with notes: focus on the security questionnaire AI section. Humanizer: llm. Save as draft.

The agent follows [SKILL.md](./SKILL.md): plan → Firecrawl research → write HTML → optional humanize → insert links → score (target ≥ 85) → save draft.

**Dry run:** ask for a dry run to get HTML + SEO score without writing to CMS.

**Before saving:** confirm you want a draft saved — the skill is designed to ask first.

## Using the scripts manually

Run commands from `blog-content-publish/`.

### Plan an article

```bash
printf '%s' '{"keyword":"SOC 2 for AI startups","notes":"questionnaire AI section"}' \
  | python3 scripts/plan_article.py
```

### Humanize prose (optional)

Default is in-agent rewrite (`llm`). To call a provider:

```bash
printf '%s' '{"provider":"llm","text":"<prose without any links>"}' \
  | python3 scripts/humanize.py
```

Humanize **before** adding `<a href>` links.

### Get internal link suggestions

```bash
printf '%s' '{"primaryKeyword":"SOC 2 for AI startups","category":"soc-2-for-ai-companies"}' \
  | python3 scripts/fetch_link_targets.py
```

### Score a draft (no CMS write)

```bash
printf '%s' '<score-json>' | python3 scripts/run_cms.py score
```

Include `title`, `slug`, `excerpt`, `bodyHtml`, `authorSlug`, `reviewerSlug`, `featuredImageAlt`, and `seo.*` fields. Target score: **≥ 85** (see [references/seo-checklist.md](./references/seo-checklist.md)).

### Save as draft

```bash
printf '%s' '<draft-json>' | python3 scripts/run_cms.py draft
```

Required: `title`, `slug`, `excerpt`, `bodyHtml`, `categorySlug`. Optional: `tags[]`, `relatedArticleSlugs[]`.

After a successful write, open the draft in Payload admin at `https://packets.build/admin` (path is in the JSON response).

## Supported HTML

The converter only accepts: `h1`, `h2`, `h3`, `p`, `a`, `ul`, `li`, `strong`, `em`. Other tags cause a hard error — strip them before scoring or saving.

Use exactly **one** `<h1>` in the body.

## Humanizers

| Provider | How to enable |
| --- | --- |
| `llm` (default) | No credentials — agent rewrites in chat |
| `none` | Pass-through |
| `smodin`, `wordai`, `spinrewriter`, `writehuman`, `stealthwriter` | API keys in `.env` (see `.env.example`) |
| `quillbot` | `QUILLBOT_EMAIL` + `QUILLBOT_PASSWORD` + `pip install quillbot` in a `.venv` |
| `manual:phrasly`, `manual:humanizer-tech`, etc. | No automation — paste into Toolzbuy dashboard |

Toolzbuy dashboard sessions are **not** API credentials. If an API provider is missing keys, the script skips and suggests `llm`.

## Configuration

Defaults live in [config/blog-content-config.json](./config/blog-content-config.json):

- `targetSeoScore`: 85
- `humanizerDefault`: `llm`
- `defaultAuthorSlug` / `defaultReviewerSlug`: `hello-packets`
- Blog categories and CTA paths

## Troubleshooting

| Error | Fix |
| --- | --- |
| `CMS_TOOLS_NOT_INSTALLED` | `cd cms-tools && bun install` |
| `CMS_ENV_MISSING` | Set `DATABASE_URI` and `PAYLOAD_SECRET` in `packetor-skills/.env` |
| `BUN_NOT_FOUND` | Install [Bun](https://bun.sh) |
| `Unsupported HTML tag` | Remove unsupported tags from `bodyHtml` |
| `Refusing non-draft status` | Do not send `status` / `_status` other than `draft` |
| Humanizer `status: skipped` | Add the missing env var or use `llm` |
| `Category "…" not found` | Use a seeded category slug (`soc-2-for-ai-companies`, `iso-27001-for-ai-companies`, `india-compliance`, `ai-governance`) |

## Further reading

- [SKILL.md](./SKILL.md) — full agent workflow and error codes
- [references/payload-api.md](./references/payload-api.md) — how CMS writes work
- [references/seo-checklist.md](./references/seo-checklist.md) — scorer weights
- [references/positioning-guardrails.md](./references/positioning-guardrails.md) — tone and banned phrases
- [cms-tools/SOURCE.md](./cms-tools/SOURCE.md) — syncing vendored code from `packets-website`
