---
name: call-to-crm
description: End-to-end skill: take an audio/video recording of a call or meeting, convert it with ffmpeg, transcribe with OpenAI Whisper, then hand the transcript to the agent for CRM reasoning and Bigin updates. Use this skill when someone shares a call recording, meeting file, or voice note and wants CRM updated.
version: 1.0.0
compatibility: openclaw
tools:
  - ZohoMCP
---

# Call to CRM

Single end-to-end pipeline: audio attachment → ffmpeg conversion → OpenAI Whisper transcription → agent CRM summary/reasoning → Bigin account/deal lookup → pipeline update → structured note → follow-up tasks.

## When to Use

- "Here's the recording of my call with Acme — update the CRM"
- "Transcribe this meeting and add notes to the deal"
- "Process this voice note and create follow-ups"
- Any audio or video file that represents a customer interaction

## When NOT to Use

- Transcription only with no CRM update → use `audio-transcribe` skill
- CRM updates with no audio → use `bigin-ops` skill
- Live/real-time calls — Whisper is file-based only

## Prerequisites

**System dependencies:**
- `ffmpeg` — `brew install ffmpeg`

**Environment variables:**
- `OPENAI_API_KEY` — OpenAI API key (Whisper/transcription access)

**MCP Server:**
- `ZohoMCP` — Bigin CRM read/write

**Python dependencies:**
- `pip install openai`

## Pipeline (7 steps)

```
[1] Receive audio file path
      ↓
[2] ffmpeg → convert to mono 16kHz WAV (split if >25MB)
      ↓
[3] Whisper → full transcript
      ↓
[4] Agent → structured CRM summary
    { account_name, contact_name, summary, stage_change,
      key_points[], action_items[], sentiment }
      ↓
[5] Bigin lookup → find Account + Deal by name
      ↓
[6] Bigin update → pipeline stage (if stage_change present)
      ↓
[7] Bigin note → add structured call note
      ↓
[8] Bigin tasks → create follow-up tasks when concrete next actions are present
```

## Script Usage

```bash
# Basic — provide audio and company name
python3 call-to-crm.py --input call.mp4 --account "Acme Corp"

# Auto-detect account from transcript (no --account needed)
python3 call-to-crm.py --input meeting.m4a

# With known deal ID — skip lookup
python3 call-to-crm.py --input call.mp4 --deal-id "<bigin_deal_id>"

# Dry run — transcribe only, no CRM writes
python3 call-to-crm.py --input call.mp4 --dry-run

# Override language for faster transcription
python3 call-to-crm.py --input hindi-call.mp4 --language hi
```

## CRM Summary Schema

The agent should produce this JSON before any Bigin writes:

```json
{
  "account_name": "Acme Corp",
  "contact_name": "Jane Smith",
  "call_date": "2026-03-29",
  "duration_minutes": 32,
  "sentiment": "positive",
  "stage_change": "Proposal/Price Quote",
  "summary": "Discussed Q2 compliance requirements. Customer interested in Enterprise plan. Requested formal proposal by end of week.",
  "key_points": [
    "Compliance deadline is June 30",
    "Decision maker is CTO, not procurement",
    "Budget approved up to $50k"
  ],
  "action_items": [
    { "task": "Send formal proposal", "owner": "sales@packets.build", "due_days": 2 },
    { "task": "Schedule technical demo with CTO", "owner": "sales@packets.build", "due_days": 5 }
  ]
}
```

## Note Format in Bigin

Notes are added with the title `[Call] YYYY-MM-DD — <account>` and structured body:

```
[Auto] Call summary — 2026-03-29
Duration: 32 min | Sentiment: Positive

Summary:
Discussed Q2 compliance requirements...

Key Points:
• Compliance deadline is June 30
• Decision maker is CTO, not procurement

Action Items:
• Send formal proposal (due: 2026-03-31)
• Schedule technical demo with CTO (due: 2026-04-03)
```

## Agent responsibilities after transcription

The Python script should stop at transcript generation. After that, the agent should:

1. read the transcript output
2. summarize the call in CRM language
3. decide account/deal matching strategy
4. decide stage change only if clearly justified
5. add a note to the **Pipeline record only** unless explicitly instructed otherwise
6. create follow-up task(s) only when the conversation contains concrete next actions, commitments, or agreed follow-ups

## Task creation rules

Create follow-up tasks when the conversation clearly includes:
- an agreed next meeting or demo
- a promise to send material, proposal, pricing, or documents
- a concrete callback/follow-up request
- an action that has an obvious owner and realistic next step

Do **not** create tasks for:
- vague interest
- generic “we’ll see”
- exploratory discussion with no commitment
- weak signals without a real next action

## Error Handling

All errors return structured JSON. Logs to stderr only.

Common codes:
- `FFMPEG_NOT_FOUND` — install ffmpeg
- `INPUT_NOT_FOUND` — file path doesn't exist
- `OPENAI_AUTH_FAILED` — check OPENAI_API_KEY
- `ACCOUNT_NOT_FOUND` — no matching Bigin account; note stored but no deal update
- `DEAL_NOT_FOUND` — account found but no open deal; note added to account
- `TRANSCRIPTION_FAILED` — Whisper error
- `SUMMARY_FAILED` — agent-side summarization failed after transcription
