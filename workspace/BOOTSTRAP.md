# Bootstrap — Packets Agent Startup Gate

Run this check at the start of every session before taking any action.

## Steps (all silent — zero output unless error)

### 1. Read core files
- `SOUL.md` — operating principles
- `TOOLS.md` — tool cheat sheet
- `USER.md` — user preferences (skip if not found)
- `memory/` — recent session notes (latest file)

### 2. Validate MCP connectivity
Attempt a lightweight read from each required MCP server:
- ZohoMCP: call `mcp__ZohoMCP__Bigin_getModules` (no params)
- Firecrawl: no startup check needed (stateless)

If ZohoMCP fails: output exactly —
> "ZohoMCP connection failed. Please check Zoho OAuth credentials and restart."

Then respond `NO_REPLY` and stop.

### 3. Set state = READY
If all checks pass: respond `NO_REPLY`. Do not output anything.

## Exception: First-time Setup

If `USER.md` does not exist, prompt the user once:
> "I'm ready. To personalise your setup, what's your name and preferred notification channel (Discord/email)?"

Then create `USER.md` from their response using the `USER.md.template`.
