---
name: notion
description: Fetch and interpret Notion content using the direct Notion API with bearer auth. Use this skill for reading Notion pages, recursively traversing blocks, resolving child databases, and extracting structured content such as template copy and attachment/file-id tables.
version: 1.0.0
compatibility: openclaw
tools:
  - Notion API
---

# Notion Operations

Use this skill for all direct Notion interactions.

## Authentication

Token source order:
1. `NOTION_API_KEY` environment variable
2. `~/.config/notion/api_key`

Headers:
- `Authorization: Bearer <NOTION_API_KEY>`
- `Notion-Version: 2025-09-03`
- `Content-Type: application/json` for write/update requests

## Read flow

1. Resolve the canonical page id.
2. Fetch page metadata using:
   - `GET /v1/pages/{page_id}`
3. Fetch top-level blocks using:
   - `GET /v1/blocks/{page_id}/children?page_size=100`
4. Recursively fetch children for any block with `has_children=true`.
5. Flatten `plain_text` from `rich_text` arrays for readable content.
6. If a relevant section is a `child_database`, switch from block traversal to database querying.

## Canonical example page

For:
- `Mail-content-for-Companies`
- URL: `https://app.notion.com/p/breaknco/Mail-content-for-Companies-2c79d65382d480c5932cc7c6e5c3c7c1?...`

Use page id:
- `2c79d65382d480c5932cc7c6e5c3c7c1`

## Important structure found on Mail-content-for-Companies

Top-level blocks include:
- `Uploaded Bigin Files`
- immediately followed by a `child_database` titled `attachments`
- `🧭 Index — find the right email`
- `Segmented Email Tunnel — Full Drafts`
- `Anchor-Based Email Tunnel — Non-Certification`
- `GRC by Maturity Stage`
- `Simplified — Non-Native English Markets`

## Child database rule

If the block under a relevant heading (for example `Uploaded Bigin Files`) is a `child_database`:
- do not treat it as plain text
- identify its block/database object id
- fetch database metadata first
- inspect the returned `data_sources` array
- when present, prefer querying the backing data source rows
- extract row properties such as:
  - file name
  - Bigin file id
  - other metadata columns

## Database and data source retrieval rule

Use this sequence for child databases and structured tables:

1. `GET /v1/databases/{database_id}`
   - confirm the database title
   - inspect `data_sources`
2. If `data_sources` is present, capture the backing `data_source_id`
3. Query rows using:
   - `POST /v1/data_sources/{data_source_id}/query`
4. Use an explicit JSON request body (an empty object `{}` is valid)
5. If you need to reduce properties, pass `filter_properties` in the **query string**, not in the JSON body

Important findings from this environment:
- `GET /v1/databases/{database_id}` works and returns `data_sources`
- `POST /v1/data_sources/{data_source_id}/query` works when called with the proper semantics
- `filter_properties` belongs in the URL query string, for example:

```http
POST /v1/data_sources/{data_source_id}/query?filter_properties[]=title
```

- using invalid `filter_properties` values returns a validation error
- when a full-row query is needed, omit `filter_properties` and map all returned properties

## Row extraction rule

When rows are returned from a data source query:
- preserve the property/header names exactly
- extract the corresponding values by property type
- for `title` and `rich_text`, flatten `plain_text`
- build a header -> value map for each row

Example from the `attachments` source:
- `File name` -> `Customers_already_certified.pdf`
- `Bigin file ID` -> `3m0rq41620ce5dc97439d9310bd8f489a5f22`

## Extraction rule

Use helpers that flatten rich text to `plain_text`.
For tables, parse child rows.
For child databases, query row properties rather than block text.

## Marketing-email-send integration rule

When `marketing-email-send` needs:
- template content
- attachment rows / Bigin file ids
- `Uploaded Bigin Files`

it should use this skill for all Notion-side interactions rather than inventing separate Notion fetching logic.
