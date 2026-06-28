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

## Database / data source handling

For a `child_database` block:

1. Fetch database metadata:
   - `GET https://api.notion.com/v1/databases/{database_id}`
2. Read the returned `data_sources` array.
3. Capture the backing `data_source_id`.
4. Query rows with:
   - `POST https://api.notion.com/v1/data_sources/{data_source_id}/query`
5. Send an explicit JSON body, even if it is just `{}`.

### Important semantic details

- `filter_properties` belongs in the query string, not the JSON body.
- Example:

```http
POST /v1/data_sources/{data_source_id}/query?filter_properties[]=title
```

- If you want full rows with all headers/properties, omit `filter_properties`.
- When a property name is invalid in `filter_properties`, Notion returns a validation error.

## Row mapping

For each returned row:
- preserve the exact property names
- map headers to values by property type
- flatten `plain_text` for `title` and `rich_text`

Example proven attachment rows:

- `File name` -> `Customers_with_inhouse_team.pdf`
- `Bigin file ID` -> `3m0rqcf6ed2ecc39d4ec98379c83b7bf62b8d`

- `File name` -> `Customers_new_to_certification.pdf`
- `Bigin file ID` -> `3m0rq821e3d2169a14099b4fb95e047565026`

- `File name` -> `Customers_already_certified.pdf`
- `Bigin file ID` -> `3m0rq41620ce5dc97439d9310bd8f489a5f22`

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
- if it is a `child_database` titled `attachments`, fetch database metadata, resolve its backing data source, then query the data source rows
- map:
  - filename -> Bigin file id

## Why this matters

For `marketing-email-send`, this is the source of truth for:
- template body sections
- attachment filename resolution
- Bigin file ids used in `sendEmails.attachments[].id`
