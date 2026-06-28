---
name: marketing-email-send
description: Send outbound marketing emails from Zoho Bigin using company/contact context, Notion-based template selection, and pre-uploaded Bigin file attachments. Use when preparing or sending first-touch or test outbound emails where Codex must: (1) inspect Bigin account/contact details, (2) select the proper template from the Notion page 'Mail-content-for-Companies', (3) choose the correct attachment ID from the 'Uploaded Bigin Files' table on that Notion page, and (4) send the email from a configured Bigin sender.
---

# Marketing Email Send

Use this skill to select and send the right outbound email from Bigin.

## Workflow

1. Fetch the target contact, linked pipeline/deal record if relevant, and company/account details from Bigin.
   - Prefer using the `bigin-ops` skill patterns/scripts for CRM reads and writes against Bigin.
2. Fetch notes from both the pipeline record and the company/account record.
3. Merge the notes into one timeline, sort newest first, and produce a concise summary of the current context.
4. Write that summary back as a note on the pipeline record.
5. Read the Notion page for mail-content templates.
6. Apply the routing rules below to choose the right template family.
7. Read the `Uploaded Bigin Files` table on the same Notion page and map the chosen template family to the correct Bigin file ID.
   - Treat this table as mandatory source-of-truth for attachment ids in normal operation.
   - Do not skip this lookup when sending live or test emails if the table is available.
8. Use the summary plus recipient/company facts to personalize the subject/body.
9. Present a full human-review package before any send.
10. Only send through `zoho-bigin.Bigin_sendEmails` after explicit human confirmation.

## Bigin operation rule

- For CRM operations in this skill, prefer the established `bigin-ops` pathways for:
  - contact fetch/search
  - account fetch/search
  - pipeline/deal fetch/search
  - note write-back to pipeline
  - task reads when needed
- Reuse the exact working Bigin/MCP payload patterns already documented in `bigin-ops` rather than inventing separate CRM shapes here.

## Mandatory human review before send

- Never send an individual or bulk email immediately after draft generation.
- Before any send, present a human-review package that includes:
  - recipient name
  - recipient email
  - company/account name
  - linked pipeline/deal id when relevant
  - chosen template group and template family
  - attachment filename and resolved Bigin file id
  - subject line
  - full final email body
  - clear explanation of why that template was chosen
  - clear summary of any customizations made from CRM notes/company facts
- For bulk sends, provide the same review structure per recipient or as a structured batch preview.
- After presenting the review package, ask for explicit confirmation.
- Only send after a clear human approval such as “send”, “send now”, or equivalent explicit confirmation.
- If approval is ambiguous or partial, do not send.

## Template routing rules

Apply these rules in order:

- If the company is based in **India**, use the **Simplified** template group.
- If certification status is **unknown**, assume the company is **not certified**.
- Use the **existing team / in-house setup** template family only if the company appears **enterprise or mid-market** and is **likely already certified**.
- Otherwise, default to the **new to certification** family.
- Use the **already certified** family only when certification is known or strongly established.

## Known attachment mapping

Prefer reading the live Notion table first. If needed, use these current mappings as a fallback and verify against Notion:

- `Customers_already_certified.pdf`
- `Customers_new_to_certification.pdf`
- `Customers_with_inhouse_team.pdf`
- `packets_Sales_Deck.pdf`
- `Packets - Company.pdf` or its current replacement entry if the ID changed

## Bigin specifics

- `sendEmails.attachments[].id` must use a **Files API uploaded encrypted file ID**.
- Do **not** use record attachment IDs from account/contact file sections.
- If an attachment send fails with `There is no file exists with the given id`, re-upload the source PDF through the Bigin Files API flow and update the Notion table.

## Notion page usage

Use the page:
- `Mail-content-for-Companies`

### How to fetch from Notion

#### Auth
1. Use `NOTION_API_KEY` if present.
2. If not present, fall back to `~/.config/notion/api_key`.
3. Send headers:
   - `Authorization: Bearer <token>`
   - `Notion-Version: 2025-09-03`

#### Page lookup
4. Resolve the target page ID (for example the `Mail-content-for-Companies` page ID).
5. Fetch page metadata from `/v1/pages/{page_id}` to confirm title and freshness.

#### Block traversal
6. Fetch top-level page content from `/v1/blocks/{page_id}/children?page_size=100`.
7. For any block with `has_children: true`, fetch nested content from `/v1/blocks/{block_id}/children?page_size=100`.
8. Traverse recursively as needed for toggles, headings, and nested sections.

#### Text extraction
9. Extract template text from block types like headings, paragraphs, callouts, list items, and toggles using `rich_text` / `plain_text`.
10. Keep structure while extracting so section labels and code prefixes remain associated with the right body copy.

#### Database handling
11. If a relevant block is a `child_database`, treat it as a database-backed source rather than a plain block table.
12. Query database rows/properties using database APIs instead of assuming inline table rows.

### Current structure of this page

Parse the page in this order:

1. Read top-level child blocks of the page.
2. Find the section containing the mail template families.
3. Find the heading exactly named `Uploaded Bigin Files`.
4. Inspect the block immediately under that heading.
5. If it is a table, parse column 1 as file name and column 2 as Bigin file ID.
6. If it is a `child_database`, treat that database as the attachment source of truth and fetch its rows/properties via database APIs.
7. Match the chosen template family to its attachment file name.
8. If multiple similar rows exist, prefer the latest corrected row or the row whose file ID has already been proven in a successful send.
9. Prefer rows updated from raw Bigin attachment `$file_id` values over older uploaded-file IDs when both exist.

On this page, look for:
- the content blocks containing the template families
- the attachment source under `Uploaded Bigin Files` (table or child database)

## Attachment id rule

- Before sending, always fetch the attachment id from the `Uploaded Bigin Files` table on the same Notion page when that table is available.
- Use the chosen template family to select the attachment filename first, then resolve the exact Bigin file id from the table.
- Only fall back to hardcoded mappings if the Notion table is temporarily unavailable.
- When testing, still use the live table id unless the user explicitly asks for a no-attachment test.

## Notes and summary behavior

- Collect notes from both the company/account record and the relevant pipeline record.
- Sort note events with the latest first before summarizing.
- Summaries should capture the freshest relevant context: recent conversations, objections, priorities, stage signals, promised follow-ups, and known company situation.
- The saved summary note should be a consolidated view that includes contact details, company details, pipeline context, and the newest relevant note timeline.
- After creating the summary, write it back as a new note on the pipeline record so the latest outbound context is visible in CRM.
- Use `Bigin_addNotesToSpecificRecord` with the confirmed working shape: `body: {data: [{Note_Title, Note_Content}]}` and `path_variables: {module_api_name, id}`.
- Use the summary to refine the chosen template instead of sending a generic version when meaningful context exists.
- If no notes are available, fall back to the original template content fetched from Notion with no debug or internal-routing text exposed in the email body.

## Sender behavior

- Prefer the configured sender the user specifies.
- If testing, make it explicit in the subject/body that the email is a test.
- Keep personalization light and factual unless the user asks for stronger customization.
- When summary context exists, customize the email with proper recipient/company details and only add claims supported by CRM notes or known company facts.

## If attachment upload is needed

Use the proven direct Bigin flow:

1. Get a valid access token from the Zoho India accounts endpoint using the working client/refresh-token path.
2. Upload the PDF to `https://www.zohoapis.in/bigin/v2/files`.
3. Capture the returned encrypted file ID.
4. Update the Notion `Uploaded Bigin Files` table if the file is meant to be reused.

## Deterministic helpers

Use `scripts/plan_send.py` when you want a stable decision step for repeated sends.

Example:

```bash
printf '%s' '{"company_country":"India","certification_known":false,"market_segment":"startup","has_inhouse_team":false,"summary":"Recent founder note says they are exploring ISO 27001.","recipient_name":"Joseph","company_name":"BreakNCo","test_mode":true}' | python3 scripts/plan_send.py
```

The script returns:
- template group
- template family
- attachment filename key
- suggested subject
- customization hint

Use `scripts/build_bigin_payload.py` to turn resolved recipient/template/attachment inputs into a ready-to-send Bigin `sendEmails` body.

Example:

```bash
printf '%s' '{"recipient_email":"josh_tharakan@hotmail.com","recipient_name":"Joseph Tharakan","subject":"Test: For companies already certified","body":"Hi Joseph,\n\nThis is a test.\n\nBest,\nLitti","attachment_id":"<Bigin file id>"}' | python3 scripts/build_bigin_payload.py
```

Use `scripts/orchestrate_send.py` to standardize the full workflow inputs and outputs for:
- merging account + pipeline notes
- sorting latest first
- generating a working CRM summary
- selecting template family + attachment filename
- identifying next actions for the live send path

Example:

```bash
printf '%s' '{"contact_id":"1188539000000462001","account_id":"1188539000000667021","pipeline_record_id":"deal-123","recipient_name":"Joseph Tharakan","recipient_email":"josh_tharakan@hotmail.com","company_name":"BreakNCo","company_country":"India","certification_known":false,"certified":false,"market_segment":"startup","has_inhouse_team":false,"account_notes":[{"time":"2026-06-25T10:00:00Z","text":"Founder-led company exploring compliance."}],"pipeline_notes":[{"time":"2026-06-26T09:00:00Z","text":"Asked for test email and attachment validation."}],"uploaded_bigin_files":{"Customers_new_to_certification.pdf":"<Bigin file id>"},"test_mode":true}' | python3 scripts/orchestrate_send.py
```

## References

- Read `references/workflow.md` for the exact decision flow and reusable subject/body patterns.
