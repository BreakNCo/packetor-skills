# Memory — Long-term Agent Notes

Curated facts that persist across sessions. Add entries here when you learn something important about the user, product, or operations that isn't derivable from code or tool state.

## Format

```
## YYYY-MM-DD — Topic
<fact or decision and why it matters>
```

---

## 2026-03-30 — Core identity and mandate
Packetor is the assistant identity for Josh and Packets. Packetor should operate with an owner/operator mindset and act as a high-agency all-rounder across marketing, outbound, inbound, founder-led growth, operations, and co-founder-level work. The mandate is to help make Packets a billion-dollar company while optimizing hard for leverage and getting more for less.

## 2026-03-30 — User preference for operating style
Josh wants a cool, highly intelligent, extraordinary-judgment assistant persona that materially cares about Packets succeeding and behaves like it has stakes in the outcome.

## 2026-03-30 — CRM note placement preference
Call and meeting notes should be added only to Pipeline records unless Josh explicitly says otherwise.

## 2026-03-30 — Packets skills loaded into working context
Loaded and reviewed the current Packets skills from `/data/workspace/packetor-skills`: `audio-transcribe`, `bigin-ops`, `bigin-research`, and `call-to-crm`, plus the repo workspace files (`workspace/AGENTS.md`, `workspace/SOUL.md`, `workspace/USER.md`, `workspace/IDENTITY.md`, `workspace/MEMORY.md`). Operationally important takeaways: use `audio-transcribe` for ffmpeg + Whisper transcription, `bigin-ops` for direct Bigin CRUD, `bigin-research` for web research + Bigin enrichment when Firecrawl is available, and `call-to-crm` for end-to-end call transcription → CRM summary → Pipeline note/tasks.

## 2026-03-30 — Local MCP/Bigin integration state
A local workspace install of `mcporter` was created under `/data/workspace/.local` with a shim at `/data/workspace/bin/mcporter`. The configured MCP server name is `zoho-bigin` (from `/data/workspace/config/mcporter.json`), not `ZohoMCP` as assumed by the Packets scripts. The `bigin-ops` wrapper was repaired to work with the current schema by using explicit `path_variables/query_params/body` payloads and an explicit mcporter config path.

## 2026-03-30 — GitHub auth convention
Future sessions should use the environment variable `GITHUB_PAT_TOKEN` for authenticated GitHub operations. Do not store or repeat the token value in memory files.
