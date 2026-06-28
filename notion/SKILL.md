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
- query the database rows
- extract row properties such as:
  - file name
  - Bigin file id
  - other metadata columns

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
