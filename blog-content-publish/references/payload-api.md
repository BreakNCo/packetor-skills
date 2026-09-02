# Payload / draft writes

This skill writes drafts via a **vendored Payload CLI** in `blog-content-publish/cms-tools/`, not HTTP. That CLI instantiates Payload with `getPayload()` and then `payload.create` / `payload.update` — the same Local API pattern as `packets-website/scripts/publish-test-article.ts`.

## Required environment

Set `DATABASE_URI` and `PAYLOAD_SECRET` in **one** of these places:

| Location | When to use |
| --- | --- |
| `packetor-skills/.env` | Recommended. Loaded automatically by `cms_env.py` for Python wrappers and `humanize.py` |
| Process environment | Always wins over `.env` file values |

Copy `packetor-skills/.env.example` → `.env` and fill in credentials. Humanizer keys in the same file are loaded the same way.

One-time install:

```bash
cd blog-content-publish/cms-tools && bun install
```

Optional override: `PACKETOR_SKILLS_ENV` for an explicit `.env` path.

`payloadBaseUrl` in `config/blog-content-config.json` is only used to print admin/preview URLs (`https://packets.build` in production).

## Commands

From `blog-content-publish/` (loads `packetor-skills/.env`):

```bash
printf '%s' '<json>' | python3 scripts/run_cms.py score
printf '%s' '<json>' | python3 scripts/run_cms.py draft
python3 scripts/run_cms.py link-targets
```

Or directly in `cms-tools/` after `bun install`:

```bash
printf '%s' '<json>' | bun run cms:score
printf '%s' '<json>' | bun run cms:draft
bun run cms:link-targets
```

Python wrappers set `NODE_ENV=production` and the vendored adapter has `push: false`, so this CLI will not alter the production schema.

`cms:draft` **hardcodes** `_status: "draft"` and `draft: true`. It rejects input whose `status` / `_status` is anything other than `draft`. Publishing is a manual action in `/admin`. Confirm with the user before calling `run_cms.py draft`.

Drafts do not require author, reviewer, or last-reviewed date. Those are enforced only when `_status === "published"` (`requireEeatOnPublish`).

Default Person slug for test drafts: `hello-packets`. Replace with a real specialist before publish.

## Keeping cms-tools in sync

`cms-tools/` is a **manual vendor** of `packets-website` source (see `cms-tools/SOURCE.md`), not a live reference. Re-copy and re-apply the documented edits when:

- `Articles` (or related collections) schema changes
- `seo-score.ts` weights or checks change
- IA marketing paths used for internal links change
- Payload adapter / collection set changes

`packets-website` still owns the admin SEO panel scorer. These copies are forks.

## REST note (not used here)

`Articles`, `People`, and `Categories` currently define **no `access` control** in `packets-website`, so Payload's default-permissive REST at `/api/articles` is likely unauthenticated. This skill avoids depending on that by using local script execution. Treat the missing access rules as a latent packets-website security gap — do not "fix" it from this skill.
