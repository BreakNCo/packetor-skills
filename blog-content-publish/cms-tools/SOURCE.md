# cms-tools vendor source

Manually vendored from `packets-website` at git SHA `19f439a` (not a live submodule).

If Articles schema, `seo-score.ts` weights, collection set, or IA page paths change in `packets-website`, re-copy the matching files here and re-apply the edits below.

## Deliberate edits vs packets-website

1. `src/payload.config.ts` — `push: false` on the Postgres adapter; no `admin` block; no `Users` collection (CLI uses Local API only). Default `NODE_ENV` to `production` if unset. Logger writes to stderr so stdout stays JSON.
2. `src/collections/Articles.ts` — removed `next/cache` `revalidatePath` hook and the admin-only `seoScore` UI field.
3. `Users.ts` is kept on disk but not registered, in case Payload later requires an auth collection.
4. CLI scripts that boot Payload call `process.exit(0)` after writing JSON so the Postgres pool does not keep the process alive.

`Media.upload.staticDir` still points at `public/media/` relative to this package. Draft writes do not upload files; create that directory only if a later skill version starts attaching featured images.
