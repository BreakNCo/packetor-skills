# Bigin Field Mapping Reference

Maps scraped/extracted fields from Firecrawl to Zoho Bigin Accounts module API field names.

## Field Map

| Scraped Key | Bigin API Field | Notes |
|-------------|----------------|-------|
| `company_name` | `Account_Name` | Skipped if already populated (configurable) |
| `description` | `Description` | 2-3 sentence company overview |
| `industry` | `Industry` | Primary industry vertical |
| `employee_count` | `Employees` | Number or range (e.g. "50-200") |
| `phone` | `Phone` | Main contact number |
| `twitter_url` | `Twitter_Url` | Full URL or handle |
| `headquarters_city` | `Billing_City` | HQ city |
| `headquarters_state` | `Billing_State` | HQ state/region |
| `headquarters_country` | `Billing_Country` | HQ country |
| `linkedin_url` | `Company_Linkedin_Url` | LinkedIn company page |
| `technologies` | `Technologies` | Comma-separated tech stack |
| `founded_year` | `Founded_Year` | 4-digit year |
| `funding` | `Total_Funding` | e.g. "Series B, $20M (2024)" |
| `iso_certifications` | _(none)_ | No free-text field. `ISO_27001_Likelihood` is a picklist (`Already Has` / `Less Likely` / `Highly Likely` / `In Progress`) — set only with evidence; put certification details in the note |

> Verified against this Bigin org's field metadata. `Industry` is a restricted picklist (use `Large Enterprise` / `Small/Medium Enterprise`); `Employees` and `Founded_Year` are integers; `Technologies` is max 255 chars.

## Skip Logic

Fields listed in `config.research.skipFieldsIfPopulated` are never overwritten if the record already has a value. Defaults: `Account_Name`, `Website`.

Set `config.research.alwaysOverwrite: true` to disable this protection.

## Notes Format

Research notes are added with title from `config.bigin.noteTitle` and include:
- Timestamp (UTC ISO)
- Source URL
- List of fields updated
- Tag prefix from `config.research.noteSourceTag` (default: `[Auto-Research]`)

## Bigin Module

All operations target `config.bigin.module` (default: `Accounts`). To use Contacts module instead, update this config value.
