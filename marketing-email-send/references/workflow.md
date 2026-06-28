# Marketing Email Send Workflow

## Inputs

Typical inputs:
- contact name or Bigin contact id
- company/account name or id
- sender identity
- whether to send a test or live outbound email

## Decision flow

1. Resolve the Bigin contact.
2. Resolve the linked company/account.
3. Resolve the linked pipeline/deal record when available.
4. Pull notes from the company/account and pipeline/deal records.
5. Merge notes into a single timeline and sort newest first.
6. Produce a concise working summary from that timeline.
7. Build the saved CRM note as a consolidated outbound view containing:
   - Contact
   - Company
   - Pipeline/latest context
   - Recommended email path
8. Write the summary back as a new note on the pipeline/deal record using `Bigin_addNotesToSpecificRecord` with:
   - `path_variables.id` = pipeline record id
   - `path_variables.module_api_name` = `Pipelines`
   - `body.data` = array containing `{Note_Title, Note_Content}`
9. Read company geography and any evidence of certification/setup.
9. Choose template family:
   - India + unknown certification -> simplified new-to-certification
   - India + certified -> simplified already-certified
   - India + certified + enterprise/mid-market + in-house -> simplified in-house
   - non-India + unknown certification -> new-to-certification
   - non-India + certified -> already-certified
   - non-India + certified + enterprise/mid-market + in-house -> in-house
10. Read the exact template copy from Notion.
11. Choose the matching attachment from the `Uploaded Bigin Files` table.
12. Resolve the exact Bigin file id from that table before building the send payload.
13. If notes exist, fill placeholders with recipient/company facts and customize lightly using the summary.
14. If notes do not exist, use the original Notion template copy with only normal recipient/company placeholder filling and no internal/debug wording.
14.1. Do not automatically add body lines such as "This is a test outbound email from Packets" or "This is a test follow-up from Packets" unless the human explicitly asks for that wording.
15. Build a human-review package before any send.
16. Wait for explicit human approval.
17. Build the send payload.
18. Send via Bigin only after approval.

## Suggested subject line patterns

- New to certification:
  - `3 questions to answer before you start ISO 27001`
  - `Where do you stand before starting ISO 27001?`
- Already certified:
  - `Keeping governance running after certification`
  - `For companies already certified`
- In-house team:
  - `For companies with an in-house team`
  - `When the tools are in place but governance is still fragmented`
- Generic company collateral:
  - `Packets company one-pager`
  - `Packets sales deck`

## Attachment mapping pattern

Preferred mapping:
- new-to-certification -> `Customers_new_to_certification.pdf`
- already-certified -> `Customers_already_certified.pdf`
- in-house team -> `Customers_with_inhouse_team.pdf`
- general collateral -> `Packets - Company.pdf` or `packets_Sales_Deck.pdf`

Always verify the file ID from the Notion table before sending.

Important finding:
- For files already attached to a Bigin company/account record, prefer the raw `getAttachments` API `$file_id` over record attachment `id` and over older unstable uploaded-file IDs.
- `sendEmails.attachments[].id` works with the attachment `$file_id` returned by the raw attachments API.
- Record attachment `id` alone does not work for `sendEmails.attachments[].id`.

## Exact Notion parsing instructions

For the current page structure:

1. Fetch the top-level child blocks of the Notion page.
2. Identify the heading block whose plain text is exactly `Uploaded Bigin Files`.
3. The next table block under that heading is the source of truth for reusable attachment IDs.
4. Read the table rows.
5. Interpret cells as:
   - column 1 = file name
   - column 2 = Bigin file ID
6. Build a file-name -> file-id map from that table.
7. For template text, continue scanning the other page blocks for the relevant template family sections and variants.
8. If notes are absent, use the exact template body from Notion as the fallback email body.
9. If notes are present, use the Notion template as the base and customize lightly.
10. Resolve the chosen attachment filename to the live Bigin file id from the table before sending.

## Summary guidance

Saved note format should aim to look like:

```text
Contact:
- Name: ...
- Role/title: ...
- Email: ...
- Other relevant contact facts: ...

Company:
- Name: ...
- Geography: ...
- Known company context: ...

Pipeline / latest context:
- Stage or motion: ...
- Latest notes summary: ...
- Blockers / timing / follow-up: ...

Recommended email path:
- Template family: ...
- Attachment: ...
- Why: ...
```

Confirmed note write-back payload shape:

```json
{
  "body": {
    "data": [
      {
        "Note_Title": "Outbound summary",
        "Note_Content": "..."
      }
    ]
  },
  "path_variables": {
    "module_api_name": "Pipelines",
    "id": "<pipeline_record_id>"
  }
}
```

Prioritize these signals in the summary:
- latest contact or founder conversation
- current pipeline stage and motion
- objections or blockers
- urgency / timing / follow-up commitments
- certification posture if mentioned
- reasons a more tailored opening or CTA would help

Keep summaries concise and useful for the next outbound step.

## Human review package requirements

Before sending any individual or bulk email, present:

- recipient name
- recipient email
- company name
- linked pipeline/deal id when relevant
- chosen template group and template family
- attachment filename
- resolved Bigin file id
- subject line
- full final email body
- explanation of why this template was selected
- explanation of what customization was added from CRM context or company facts

Then ask for explicit confirmation before sending.

Examples of acceptable confirmation:
- "send"
- "send now"
- "approved, send"

Without explicit approval, do not send.

## Failure handling

### If sendEmails returns invalid attachment id
- Prefer the raw `getAttachments` API `$file_id` for company-record PDFs when available.
- If no usable `$file_id` is available, re-upload the source PDF through Bigin Files API.
- Update the Notion table row with the best current sendable ID.
- Retry the send.

### If certification status is unclear
- Treat as not certified.

### If template choice is ambiguous
- Prefer the safer, simpler template.
- If India-based, prefer the simplified group.
