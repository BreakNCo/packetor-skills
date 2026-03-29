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

| Skill | Description |
|-------|-------------|
| [Bigin Company Research](./Bigin%20Company%20Research.md) | Research companies via web and update records in Zoho Bigin CRM |

## How Skills Work

Each skill is a markdown file that instructs Claude agents on how to perform a specific operational task. Skills define:

- **When to use** — trigger conditions and applicable scenarios
- **Prerequisites** — required MCP servers and environment variables
- **Workflow** — step-by-step process with tool call examples
- **Field mappings** — how external data maps to tool fields
- **Examples** — real usage scenarios
- **Troubleshooting** — common issues and fixes

## MCP Servers Required

Skills in this repo rely on the following MCP servers:

- **ZohoMCP** — Bigin CRM, Zoho Desk, Zoho Mail, Zoho Meeting
- **Firecrawl** — Web scraping and search
- **mcp-atlassian-azt** — Jira and Confluence
- **context7** — Library and API documentation
