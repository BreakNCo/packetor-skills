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

## Agent Skill Discovery

Skills live at the repo root (`<skill-name>/SKILL.md`) and are symlinked into platform discovery folders:

- **Claude Code** — `.claude/skills/`
- **Cursor** — `.cursor/skills/`
- **Codex / WARP** — `.agents/skills/`

When working in this repo, Claude Code auto-loads skills from `.claude/skills/`. Trigger by task description (e.g. *transcribe this call*, *research Acme in Bigin*, *process call recording into CRM*) — the `description` field in each skill's YAML frontmatter drives matching.

See [`.cursor/skills/README.md`](.cursor/skills/README.md) for the full skill index.

## Adding New Skills

1. Create a skill folder at the repo root: `<skill-name>/SKILL.md` plus optional `config/`, `scripts/`, `references/` (see existing skills)
2. Follow the skill format above (YAML frontmatter with `name` and `description` is required)
3. Register for agent discovery (Claude Code, Cursor, Codex):
   ```bash
   for dir in .claude/skills .cursor/skills .agents/skills; do
     mkdir -p "$dir"
     ln -sf "../../<skill-name>" "${dir}/<skill-name>"
   done
   ```
4. Update the skills table in `README.md` and `.cursor/skills/README.md`
