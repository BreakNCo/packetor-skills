# bigin-company-research

Research companies using web search and automatically update their details in Zoho Bigin CRM.

## When to Use

✅ **Use this skill when:**
- User asks to research a company and update Bigin
- Need to enrich existing Bigin contacts/accounts with latest company information
- Want to gather company details before creating new Bigin records
- Need to verify or update company information (website, technologies, employee count, funding, etc.)

## When NOT to Use

❌ **Do NOT use this skill for:**
- Simple Bigin record lookups (use direct Bigin MCP tools instead)
- Company research without Bigin updates (just use web search)
- Bulk operations on many companies (use batch processing instead)
- Real-time data requiring authentication (financial data, private company info)

## Prerequisites

**Required MCP Servers:**
1. **Firecrawl MCP** - For web scraping and search
2. **Zoho Bigin MCP** - For CRM updates

**Environment Variables:**
- `FIRECRAWL_API_KEY` - Get from https://firecrawl.dev
- Zoho Bigin OAuth credentials (configured via ZohoMCP server)

## Workflow

### 1. Search for Company in Bigin

First, search if the company already exists in Bigin:

```bash
# Use Bigin searchRecords with company name
mcp__ZohoMCP__Bigin_searchRecords(
  module_api_name: "Accounts",
  word: "<company_name>"
)
```

### 2. Research Company Online

Use Firecrawl to gather company information:

```bash
# Method A: Direct website scrape if URL is known
mcp__firecrawl__firecrawl_scrape(
  url: "https://company-website.com",
  formats: ["markdown"],
  extract: {
    "company_name": "Company legal name",
    "description": "What the company does",
    "industry": "Primary industry",
    "employee_count": "Number of employees",
    "founded_year": "Year founded",
    "headquarters": "HQ location",
    "technologies": "Tech stack used",
    "linkedin_url": "LinkedIn company page",
    "twitter_url": "Twitter/X handle",
    "funding": "Latest funding info"
  }
)

# Method B: Web search if URL is unknown
mcp__firecrawl__firecrawl_search(
  query: "<company_name> company information",
  limit: 5
)
```

### 3. Extract Key Information

From web research, extract and structure:

**Essential Fields:**
- Company name
- Website URL
- Industry/sector
- Description
- Employee count
- Founded year
- Headquarters location
- LinkedIn company URL
- Technologies used

**Optional Fields:**
- Twitter/social media
- Phone number
- Funding information
- Recent news
- Key executives
- ISO certifications
- Office locations

### 4. Update or Create Bigin Record

**If company exists** (from step 1), update the account:

```bash
mcp__ZohoMCP__Bigin_updateSpecificRecord(
  module_api_name: "Accounts",
  id: "<found_account_id>",
  data: {
    "Account_Name": "Company Name",
    "Website": "https://company.com",
    "Description": "What they do...",
    "Industry": "Technology",
    "Employees": 120,
    "Phone": "+1234567890",
    "Account_Type": "Customer",
    "Twitter": "https://twitter.com/company",
    "Billing_City": "City",
    "Billing_State": "State",
    "Billing_Country": "Country"
  }
)
```

**If company doesn't exist**, create new account:

```bash
mcp__ZohoMCP__Bigin_addRecords(
  module_api_name: "Accounts",
  data: [{
    "Account_Name": "Company Name",
    "Website": "https://company.com",
    "Description": "What they do...",
    "Industry": "Technology",
    "Employees": 120,
    "Phone": "+1234567890",
    "Account_Type": "Prospect"
  }]
)
```

### 5. Add Research Note

Always add a note documenting the research:

```bash
mcp__ZohoMCP__Bigin_addNotesToSpecificRecord(
  module_api_name: "Accounts",
  id: "<account_id>",
  data: [{
    "Note_Title": "Company Research - <current_date>",
    "Note_Content": "Automated research findings:\n- Technologies: ...\n- Employee count: ...\n- Recent developments: ...\n- Sources: [list URLs]"
  }]
)
```

## Field Mapping Guide

**Bigin Account Fields:**

| Bigin Field | Web Search Target | Example |
|-------------|-------------------|---------|
| `Account_Name` | Company legal name | "Exponential Digital Solutions Pvt.Ltd." |
| `Website` | Primary domain | "https://10xds.com" |
| `Description` | About section, mission | "RPA and AI automation services" |
| `Industry` | Sector, vertical | "Information Technology" |
| `Employees` | Team size, headcount | 120 |
| `Phone` | Contact number | "+91 47 1254 4210" |
| `Twitter` | Social media | "https://twitter.com/company" |
| `Billing_City` | HQ city | "Ernakulam" |
| `Billing_State` | HQ state/region | "Kerala" |
| `Billing_Country` | HQ country | "India" |

**Custom Fields (if available):**
- `Technologies` - Tech stack
- `Company_Linkedin_Url` - LinkedIn page
- `Founded_Year` - Year established
- `Funding_Info` - Latest round
- `ISO_Certifications` - Compliance certs

## Usage Examples

### Example 1: Research and Update Existing Company

```
User: "Research and update 10xds in Bigin"

Steps:
1. Search Bigin for "10xds" → Found account ID 1188539000000440219
2. Get their website from Bigin → https://10xds.com
3. Scrape website for latest info
4. Search LinkedIn for employee count
5. Update Bigin account with new data
6. Add research note with sources
7. Report summary to user
```

### Example 2: Research New Company and Create Record

```
User: "Research Acme Corp and add to Bigin"

Steps:
1. Search Bigin for "Acme Corp" → Not found
2. Web search for "Acme Corp company"
3. Scrape their website
4. Extract LinkedIn, tech stack, location
5. Create new account in Bigin
6. Add research note
7. Report new account ID to user
```

### Example 3: Enrich Contact's Company

```
User: "Update the company details for Samil Kumar"

Steps:
1. Get Samil's contact record
2. Find linked account: "Exponential Digital Solutions"
3. Get account ID: 1188539000000440219
4. Research company website
5. Update account fields
6. Link research note
7. Confirm update with user
```

## Best Practices

**Data Quality:**
- Always verify company name matches Bigin record
- Cross-reference information from multiple sources
- Note the research date in the note
- Include source URLs in the research note
- Don't overwrite good data with empty/uncertain values

**Privacy & Compliance:**
- Only research publicly available information
- Respect robots.txt and rate limits
- Don't scrape contact emails (use dedicated sources)
- Follow GDPR for EU companies

**Error Handling:**
- If website is unreachable, try LinkedIn or Crunchbase
- If search returns multiple companies, ask user to clarify
- If critical fields are missing, flag for manual review
- Always report what was updated and what couldn't be found

**Efficiency:**
- Cache recent research (don't re-scrape within 7 days)
- Batch multiple companies if requested
- Use parallel searches when possible
- Prioritize official sources (company website > news articles)

## Common Commands

### Search Company in Bigin
```javascript
await bigin.searchRecords("Accounts", { word: "company name" })
```

### Scrape Company Website
```javascript
await firecrawl.scrape({
  url: "https://company.com",
  formats: ["markdown"],
  extract: { /* schema */ }
})
```

### Web Search for Company
```javascript
await firecrawl.search({
  query: "Company Name headquarters employees",
  limit: 5
})
```

### Update Bigin Account
```javascript
await bigin.updateSpecificRecord("Accounts", accountId, {
  Website: "https://company.com",
  Description: "...",
  // ... other fields
})
```

### Add Research Note
```javascript
await bigin.addNotesToSpecificRecord("Accounts", accountId, [{
  Note_Title: `Research - ${new Date().toISOString().split('T')[0]}`,
  Note_Content: "Findings:\n- ..."
}])
```

## Troubleshooting

**Issue: Company not found in Bigin**
- Try searching by website domain or LinkedIn URL
- Ask user if company goes by different name
- Offer to create new record

**Issue: Website scraping fails**
- Check if site blocks scrapers
- Try alternative sources (LinkedIn, Crunchbase)
- Use web search to find company info

**Issue: Duplicate companies found**
- Show user both records with details
- Ask which one to update
- Suggest merging duplicates

**Issue: Bigin field mapping unclear**
- Use getFieldsMetadata to check available fields
- Fall back to adding info in Description or Notes
- Flag custom field requirements for admin

## Notes

- **Rate Limits**: Firecrawl has usage limits. Don't research >10 companies in quick succession.
- **Data Freshness**: Web data may be outdated. Always note the research date.
- **Manual Review**: Flag significant changes (>50% employee change, different industry) for user confirmation.
- **Contact Privacy**: This skill updates accounts, not individual contacts. For contact-level updates, research appropriately.
- **API Quotas**: Bigin API has daily limits. Monitor usage in high-volume scenarios.
- **Skill Trigger**: Use commands like `/research [company]` or "research and update [company] in Bigin"

## Advanced: Multi-Source Research

For comprehensive company profiles, combine multiple sources:

1. **Company Website** - Official info, products, services
2. **LinkedIn** - Employee count, recent hires, key people
3. **Crunchbase** - Funding, investors, acquisition history
4. **Product Hunt** - Product launches, user feedback
5. **GitHub** - Open source projects, tech stack
6. **News Search** - Recent developments, partnerships
7. **Social Media** - Company culture, marketing approach

Create a scoring system for data confidence:
- ✅ High (official website, verified profile)
- ⚠️ Medium (news article, third-party directory)
- ❓ Low (unverified source, old data)

Include confidence scores in research notes.
