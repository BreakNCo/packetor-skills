# SEO checklist (packets-website scorer)

This is a human-readable mirror of `cms-tools/src/lib/cms/seo-score.ts` (vendored from packets-website). The live scorer is authoritative — `python3 scripts/run_cms.py score` calls it after round-tripping HTML through Lexical.

**Target score: ≥ 85.** Fifteen checks, total weight **104**. `score = round(earned / 104 * 100)`.

Keyword density is weighted last on purpose. Fix structure, links, E-E-A-T, and meta first.

## Checks

| id | Label | Weight | Pass when |
| --- | --- | ---: | --- |
| `title` | Title exists | 10 | `title` is non-empty |
| `metaDescription` | Meta description exists | 10 | meta description ≥ **50** characters (scorer floor) |
| `singleH1` | Exactly one H1 in the article body | 10 | body contains exactly one `<h1>` |
| `keywordInTitle` | Primary keyword in title | 8 | case-insensitive substring |
| `keywordInH1` | Primary keyword in H1 | 8 | case-insensitive substring |
| `keywordInUrl` | Primary keyword in URL | 6 | slug contains hyphenated keyword |
| `internalLinks` | Internal links present | 8 | count of packets.build / relative links **> 0** |
| `externalSources` | External sources present | 6 | count of off-site `href`s **> 0** |
| `imageAlt` | Image alt text present | 6 | `featuredImageAlt` non-empty |
| `author` | Author assigned | 8 | author slug present |
| `reviewer` | Reviewer assigned | 8 | reviewer slug present |
| `canonical` | Canonical configured | 4 | canonical path set (default `/blog/{slug}`) |
| `schema` | Schema configured | 4 | title + H1 + slug + author slug |
| `cta` | CTA present | 6 | body links to `/contact`, `/early-access`, or `/audit-readiness` |
| `keywordDensity` | Keyword density 1–2% | 2 | density of primary keyword in title + H1 + body is 1–2% |

Internal links, external sources, and CTA are counted from **raw `<a href>` tags in rendered body HTML** (`analyzeBodyHtml()`), not from separate CMS fields. If the Lexical converter drops a link, the sidebar score drops too.

## Editorial targets (tighter than the scorer)

Use these when writing, even though the scorer is more lenient:

- Meta title ≤ 60 characters
- Meta description 150–160 characters (scorer only requires ≥ 50)
- Slug includes the primary keyword, hyphenated
- At least two internal links and two external citations (`internalLinkMin` / `externalSourceMin` in config)
- Featured image alt text describing the image, not stuffing the keyword

## FAQ in the body

Add an H2 **Frequently asked questions** with 3–5 H3 question / paragraph answer pairs. That is enough for readers and for the writing template.

Blog posts currently emit **Article** JSON-LD via `buildArticle()` only. `FAQPage` schema is **not** wired for `/blog/[slug]`. Do not invent FAQ JSON-LD in this skill — that is a packets-website follow-up.

## Iteration

1. Write prose (no links).
2. Humanize if requested.
3. Insert internal links, citations, CTA, FAQ.
4. `python3 scripts/run_cms.py score`
5. Fix failing high-weight checks. Repeat at most three times, or until score ≥ `targetSeoScore`.
