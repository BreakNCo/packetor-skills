# packetor-skills

Skills for the Packets agent agency ("openclaw") — a collection of Claude skills that power AI-driven operations and automations across the tools used to build and grow [Packets](https://packets.build).

## What is Packets?

Packets is a compliance automation platform for fast-growing teams. This repository contains the skills that enable AI agents to manage day-to-day operations across all tools in the Packets stack.

## Tools Covered

| Area | Tool |
|------|------|
| CRM / Revenue Ops | [Bigin](https://www.bigin.com/en-in/) |
| Sales & Prospecting | [Apollo](https://www.apollo.io) |
| Knowledge & Docs | [Notion](https://notion.so/) |
| Community | [Discord](https://discord.gg/) |
| CI/CD | [Antigravity](https://antigravity.google/) |
| Customer Support | [Zoho Desk](https://www.zoho.com/en-in/desk/) |
| Product Docs Site | [Docusaurus](https://docusaurus.io/) |
| Workflow Automation | [Trigger.dev](https://trigger.dev/) |
| Meetings | [Zoho Meeting](https://www.zoho.com/meeting/) |
| Email | [Zoho Mail](https://www.zoho.com/mail/) |

## Skills

| Skill | Folder | Description |
|-------|--------|-------------|
| bigin-research | [bigin-research/](./bigin-research/) | Research companies online and enrich Zoho Bigin Account records |
| bigin-ops | [bigin-ops/](./bigin-ops/) | Day-to-day CRM operations — notes, tasks, meetings, pipeline stages, contacts, accounts |
| audio-transcribe | [audio-transcribe/](./audio-transcribe/) | Convert audio/video files with ffmpeg and transcribe using OpenAI Whisper |

## Skill Structure

Each skill follows the openclaw/senpi format:

```
<skill-name>/
├── SKILL.md          # Instructions + YAML frontmatter (triggers, workflow, error codes)
├── config/           # JSON config (thresholds, field names, defaults)
├── scripts/          # Python scripts executed by cron or agent
└── references/       # Reference docs loaded into context as needed
```

## MCP Servers Required

Skills in this repo rely on the following MCP servers:

- **ZohoMCP** — Bigin CRM, Zoho Desk, Zoho Mail, Zoho Meeting
- **Firecrawl** — Web scraping and search
- **mcp-atlassian-azt** — Jira and Confluence
- **context7** — Library and API documentation
