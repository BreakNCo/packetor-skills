# Packetor Skills

This repository contains skills for the Packets agent agency ("openclaw") — AI agent skills that manage operations and automations across all tools used to build and grow [Packets](https://packets.build), a compliance automation platform for fast-growing teams.

## Repository Purpose

Skills are markdown files that instruct Claude agents how to perform specific operational tasks. Each skill covers a workflow end-to-end: when to use it, what tools are needed, how to execute it, and how to handle errors.

## Skill Format

Every skill is a markdown file structured as:

- **When to Use / When NOT to Use** — trigger conditions
- **Prerequisites** — required MCP servers and environment variables
- **Workflow** — step-by-step process with tool call examples
- **Field Mapping Guide** — how data maps to tool fields
- **Usage Examples** — real scenarios
- **Best Practices** — data quality, privacy, efficiency
- **Troubleshooting** — common issues and fixes

## Tools in Scope

| Area | Tool |
|------|------|
| CRM / Revenue Ops | Bigin |
| Sales & Prospecting | Apollo |
| Knowledge & Docs | Notion |
| Community | Discord |
| CI/CD | Antigravity |
| Customer Support | Zoho Desk |
| Product Docs Site | Docusaurus |
| Workflow Automation | Trigger.dev |
| Meetings | Zoho Meeting |
| Email | Zoho Mail |

## MCP Servers Used

Skills reference the following MCP servers:

- **ZohoMCP** — Bigin CRM, Zoho Desk, Zoho Mail, Zoho Meeting
- **Firecrawl** — Web scraping and search
- **mcp-atlassian-azt** — Jira and Confluence
- **context7** — Library and API documentation

## Adding New Skills

1. Create a new markdown file named `<tool>-<action>.md` (e.g. `apollo-prospect-search.md`)
2. Follow the skill format above
3. Update the skills table in `README.md`
