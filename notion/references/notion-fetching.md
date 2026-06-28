# Notion Fetching Reference

## Direct API approach

Authentication:
- `NOTION_API_KEY`
- fallback: `~/.config/notion/api_key`

Headers:
- `Authorization: Bearer <NOTION_API_KEY>`
- `Notion-Version: 2025-09-03`

## Core flow

1. Fetch page metadata:
   - `GET https://api.notion.com/v1/pages/{page_id}`
2. Fetch top-level blocks:
   - `GET https://api.notion.com/v1/blocks/{page_id}/children?page_size=100`
3. For any block with `has_children=true`, recursively fetch:
   - `GET https://api.notion.com/v1/blocks/{block_id}/children?page_size=100`
4. Flatten `plain_text` from `rich_text` for readable content.
5. If a relevant block is `child_database`, query its rows rather than relying on block text.

## Mail-content-for-Companies canonical page

- Page title: `Mail-content-for-Companies`
- Page id: `2c79d65382d480c5932cc7c6e5c3c7c1`

## Known structure

Top-level content includes:
- `Uploaded Bigin Files`
- child database: `attachments`
- `🧭 Index — find the right email`
- `Segmented Email Tunnel — Full Drafts`
- `Anchor-Based Email Tunnel — Non-Certification`
- `GRC by Maturity Stage`
- `Simplified — Non-Native English Markets`

## Attachment extraction rule

For `Uploaded Bigin Files`:
- find the heading block with exact text `Uploaded Bigin Files`
- inspect the next block
- if it is a `child_database` titled `attachments`, query that database rows
- map:
  - filename -> Bigin file id

## Why this matters

For `marketing-email-send`, this is the source of truth for:
- template body sections
- attachment filename resolution
- Bigin file ids used in `sendEmails.attachments[].id`
