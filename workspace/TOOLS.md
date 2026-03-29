# Tools — Packets Agent Cheat Sheet

Environment-specific notes for each tool. Read this file at session start.

## MCP Servers

### ZohoMCP
- **Provides:** Bigin CRM, Zoho Desk, Zoho Mail, Zoho Meeting
- **Auth:** OAuth credentials configured at setup
- **Tool prefix:** `mcp__ZohoMCP__Bigin_*`, `mcp__ZohoMCP__Desk_*`, etc.
- Always use `module_api_name: "Accounts"` for company records in Bigin
- Always use `module_api_name: "Contacts"` for person records in Bigin

### Firecrawl
- **Provides:** Web scraping and search
- **Auth:** `FIRECRAWL_API_KEY` env var
- **Tool prefix:** `mcp__firecrawl__firecrawl_*`
- Prefer `firecrawl_scrape` when URL is known; use `firecrawl_search` when it's not
- Limit search results to 3-5 to control token cost

### mcp-atlassian-azt
- **Provides:** Jira and Confluence
- **Auth:** Atlassian API token configured at setup
- **Tool prefix:** `mcp__mcp-atlassian-azt__jira_*`, `mcp__mcp-atlassian-azt__confluence_*`
- Use Jira for sprint and ticket management
- Use Confluence for internal documentation

### context7
- **Provides:** Up-to-date library and API documentation
- Use when you need current docs for any tool or framework

## Cron (OpenClaw Gateway Scheduler)

### Schedule types
- `"at"` — one-shot: `{ "kind": "at", "at": "2026-02-01T16:00:00Z" }`
- `"every"` — recurring: `{ "kind": "every", "everyMs": 86400000 }` (ms)
- `"cron"` — cron expression: `{ "kind": "cron", "expr": "0 9 * * 1-5", "tz": "Asia/Kolkata" }`

### Session targets
- `"main"` — shared context, use sparingly
- `"isolated"` — fresh context, cheaper, default for background jobs

### Payload format
```json
{ "kind": "agentTurn", "message": "Your prompt here" }
```

### Remove a cron
Use `cron.remove` with `{ "name": "JobName" }`.

## Shell Tools Available

- `python3` — for running skill scripts
- `rg` (ripgrep) — recursive by default, do NOT pass `-R` or `-r`
- `node -e` — use for JSON processing (no `jq` available)
- `grep` — fallback search

## Key Directories

- `OPENCLAW_WORKSPACE_DIR` — workspace root (default: `~/.openclaw/workspace`)
- `skills/bigin/state/` — Bigin skill state files
- `memory/` — session and long-term memory files
