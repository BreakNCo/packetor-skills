# Agent skills for packetor-skills

Each platform discovers skills from its own folder; all entries are symlinks to the canonical skill folder at the repo root (scripts, config, and references stay in one place).

| Platform | Discovery path |
| -------- | -------------- |
| **Claude Code** | `.claude/skills/<folder>/SKILL.md` |
| **Cursor** | `.cursor/skills/<folder>/SKILL.md` |
| **Codex / WARP** | `.agents/skills/<folder>/SKILL.md` |

## Skills

| Folder | `name` (YAML) | Purpose |
| ------ | ------------- | ------- |
| [`audio-transcribe`](audio-transcribe/SKILL.md) | `audio-transcribe` | ffmpeg + OpenAI Whisper transcription for calls, meetings, voice notes |
| [`bigin-ops`](bigin-ops/SKILL.md) | `bigin-ops` | Day-to-day Zoho Bigin CRM — notes, tasks, meetings, pipeline, contacts |
| [`bigin-research`](bigin-research/SKILL.md) | `bigin-company-research` | Web research + Bigin account enrichment (Firecrawl, GooseWorks, Apollo) |
| [`call-to-crm`](call-to-crm/SKILL.md) | `call-to-crm` | End-to-end: audio → Whisper → GPT summary → Bigin note + pipeline + tasks |
| [`marketing-email-send`](marketing-email-send/SKILL.md) | `marketing-email-send` | Outbound email from Bigin with Notion template + attachment selection |

**Claude Code:** skills auto-load from `.claude/skills/` when you work in this repo. Trigger by describing the task (e.g. *process this call recording in Bigin*) or reference the skill name.

**Cursor:** invoke via the skill picker or say e.g. *use **call-to-crm***.

## Layout

```
packetor-skills/
├── <skill-name>/          # canonical skill (SKILL.md + scripts + config)
├── .claude/skills/        # Claude Code discovery (symlinks)
├── .cursor/skills/        # Cursor discovery (symlinks)
└── .agents/skills/        # Codex / WARP discovery (symlinks)
```

When adding a skill: create `<skill-name>/SKILL.md` at the repo root, then symlink it into all three discovery folders:

```bash
for dir in .claude/skills .cursor/skills .agents/skills; do
  ln -sf "../../<skill-name>" "${dir}/<skill-name>"
done
```

Update this README and the root `README.md` skills table.
