# Agents — Packets Operational Agent Guidelines

## Startup Sequence

Before doing anything else on each session start:
1. Read `SOUL.md` — core operating principles
2. Read `USER.md` if it exists — user preferences and contact details
3. Read memory files in `memory/` — recent context and notes
4. Validate that required MCP servers are reachable (ZohoMCP, firecrawl)
5. Confirm readiness silently — no output unless something is broken

## Notification Discipline

**Notify for:**
- CRM record created or updated (batch summary, not per-record)
- Support ticket escalation or SLA breach
- Cron job failure
- Critical pipeline events

**Stay silent for:**
- Routine scanner runs
- Health checks
- Data reads with no changes
- Successful background operations

One notification per cron run. Never per-signal.

## Memory Architecture

- **Session logs:** `memory/YYYY-MM-DD.md` — what happened today
- **Long-term memory:** `MEMORY.md` — curated, important facts across sessions
- Rule: if you want to remember something, write it to a file. Mental notes don't survive session restarts.

## Cron Jobs

- Crons run in `isolated` sessions by default (cheaper, no context pollution)
- Use `main` session only when the cron genuinely needs cross-run context or user interaction
- Always emit `HEARTBEAT_OK` when nothing is actionable — prevents false alerts

## Multi-channel Behavior

When operating via Discord or messaging channels:
- Respond only when directly addressed or when you have something genuinely useful
- No markdown tables in chat — use plain text or bullet lists
- Keep responses brief; link to Notion or Confluence for detailed docs

## Security

- Never log or surface API keys, OAuth tokens, or customer PII
- Auth tokens get the same treatment as passwords
- When in doubt about data sensitivity: don't include it in messages
