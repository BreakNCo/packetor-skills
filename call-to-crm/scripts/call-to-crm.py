#!/usr/bin/env python3
"""
Call to CRM v1.0.0

End-to-end pipeline:
  audio file → ffmpeg conversion → Whisper transcription
  → GPT-4o CRM summary → Bigin account/deal lookup
  → pipeline stage update → structured note → follow-up tasks

Usage:
    python3 call-to-crm.py --input call.mp4
    python3 call-to-crm.py --input call.mp4 --account "Acme Corp"
    python3 call-to-crm.py --input call.mp4 --deal-id "<bigin_deal_id>"
    python3 call-to-crm.py --input call.mp4 --dry-run
    python3 call-to-crm.py --input call.mp4 --language en --task-due-days 3

Output: JSON to stdout
Logs:   stderr only
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

from call_to_crm_config import (
    load_config,
    get_openai_key,
    find_account,
    find_open_deal,
    update_deal_stage,
    add_note_to_record,
    create_task,
    due_date_str,
    now_iso,
    out,
)


# ---------------------------------------------------------------------------
# Step 1 & 2: Audio conversion via ffmpeg
# ---------------------------------------------------------------------------

def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def convert_audio(input_path: Path, output_path: Path, config: dict) -> None:
    fc = config["ffmpeg"]
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-ar", str(fc["sampleRate"]),
        "-ac", str(fc["channels"]),
        "-acodec", fc["codec"],
        str(output_path),
    ]
    print(f"[ffmpeg] Converting {input_path.name}", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{r.stderr}")


def split_audio(input_path: Path, out_dir: Path, config: dict) -> list[Path]:
    fc = config["ffmpeg"]
    segment_time = fc["chunkDurationSeconds"] - fc["chunkOverlapSeconds"]
    pattern = str(out_dir / "chunk_%03d.wav")
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-f", "segment", "-segment_time", str(segment_time),
        "-ar", str(fc["sampleRate"]), "-ac", str(fc["channels"]),
        "-acodec", fc["codec"], "-reset_timestamps", "1",
        pattern,
    ]
    print(f"[ffmpeg] Splitting into {segment_time}s chunks", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg split failed:\n{r.stderr}")
    chunks = sorted(out_dir.glob("chunk_*.wav"))
    print(f"[ffmpeg] {len(chunks)} chunks created", file=sys.stderr)
    return chunks


# ---------------------------------------------------------------------------
# Step 3: Whisper transcription
# ---------------------------------------------------------------------------

def transcribe(chunks: list[Path], client, config: dict, language: str | None) -> str:
    wc = config["whisper"]
    parts = []
    for chunk in chunks:
        print(f"[whisper] Transcribing {chunk.name} ({chunk.stat().st_size // 1024}KB)", file=sys.stderr)
        with open(chunk, "rb") as f:
            kwargs = dict(model=wc["model"], file=f, response_format="text", temperature=wc["temperature"])
            if language:
                kwargs["language"] = language
            resp = client.audio.transcriptions.create(**kwargs)
        parts.append(str(resp).strip())
    return "\n\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Step 4: GPT-4o CRM summary
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a CRM assistant for Packets, a compliance automation platform.
Given a call transcript, extract structured information for a CRM note.

Return ONLY valid JSON matching this schema exactly:
{
  "account_name": "string or null",
  "contact_name": "string or null",
  "call_date": "YYYY-MM-DD",
  "duration_minutes": integer or null,
  "sentiment": "positive" | "neutral" | "negative",
  "stage_change": "string or null (exact Bigin stage name, null if no change implied)",
  "summary": "2-4 sentence summary in past tense, CRM language",
  "key_points": ["string", ...],
  "action_items": [
    { "task": "string", "owner": "string or null", "due_days": integer }
  ]
}

Valid stage values (use exact spelling):
Qualification, Needs Analysis, Value Proposition, Identify Decision Makers,
Proposal/Price Quote, Negotiation/Review, Closed Won, Closed Lost

Rules:
- Only set stage_change if the transcript clearly implies the deal moved to a new stage
- action_items only for concrete, explicit next steps (not vague follow-ups)
- due_days: realistic urgency — urgent=1, normal=3, relaxed=7
- Return null for any field you cannot determine from the transcript
"""


def summarise(transcript: str, client, config: dict) -> dict:
    gc = config["gpt"]
    print("[gpt] Generating CRM summary", file=sys.stderr)
    resp = client.chat.completions.create(
        model=gc["model"],
        temperature=gc["temperature"],
        max_tokens=gc["maxTokens"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Transcript:\n\n{transcript[:12000]}"},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


# ---------------------------------------------------------------------------
# Step 7: Build note content
# ---------------------------------------------------------------------------

def build_note_content(summary: dict, transcript: str | None = None) -> str:
    today = date.today().isoformat()
    sentiment = summary.get("sentiment", "unknown").capitalize()
    duration = summary.get("duration_minutes")
    duration_str = f"{duration} min" if duration else "unknown duration"

    lines = [
        f"[Auto] Call summary — {today}",
        f"Duration: {duration_str} | Sentiment: {sentiment}",
        "",
        "Summary:",
        summary.get("summary", "No summary available."),
    ]

    key_points = summary.get("key_points", [])
    if key_points:
        lines += ["", "Key Points:"]
        for p in key_points:
            lines.append(f"• {p}")

    action_items = summary.get("action_items", [])
    if action_items:
        lines += ["", "Action Items:"]
        for item in action_items:
            due = (date.today() + timedelta(days=item.get("due_days", 3))).isoformat()
            owner = item.get("owner") or "unassigned"
            lines.append(f"• {item['task']} (due: {due}, owner: {owner})")

    if transcript:
        lines += ["", "--- Full Transcript ---", transcript[:3000]]
        if len(transcript) > 3000:
            lines.append(f"[truncated — {len(transcript)} chars total]")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(
    input_path: Path,
    account_hint: str | None,
    deal_id: str | None,
    dry_run: bool,
    language: str | None,
    task_due_days: int,
    config: dict,
) -> dict:

    # Validate input
    if not input_path.exists():
        return {"status": "error", "code": "INPUT_NOT_FOUND", "path": str(input_path)}
    if not check_ffmpeg():
        return {"status": "error", "code": "FFMPEG_NOT_FOUND", "hint": "brew install ffmpeg"}

    try:
        api_key = get_openai_key()
    except EnvironmentError as e:
        return {"status": "error", "code": "OPENAI_AUTH_FAILED", "hint": str(e)}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        return {"status": "error", "code": "MISSING_DEPENDENCY", "hint": "pip install openai"}

    temp_dir = Path(tempfile.mkdtemp(prefix="call-to-crm-"))
    report: dict = {"status": "ok", "steps": {}}

    try:
        # ── Step 2: Convert ───────────────────────────────────────────────
        converted = temp_dir / "converted.wav"
        try:
            convert_audio(input_path, converted, config)
            report["steps"]["ffmpeg"] = "ok"
        except Exception as e:
            return {"status": "error", "code": "FFMPEG_FAILED", "error": str(e)}

        # ── Split if needed ───────────────────────────────────────────────
        max_bytes = config["pipeline"]["maxFileSizeBytes"]
        if converted.stat().st_size > max_bytes:
            chunks_dir = temp_dir / "chunks"
            chunks_dir.mkdir()
            chunks = split_audio(converted, chunks_dir, config)
        else:
            chunks = [converted]

        # ── Step 3: Transcribe ────────────────────────────────────────────
        try:
            transcript = transcribe(chunks, client, config, language)
            report["steps"]["transcription"] = "ok"
            report["transcript_chars"] = len(transcript)
        except Exception as e:
            return {"status": "error", "code": "TRANSCRIPTION_FAILED", "error": str(e)}

        # ── Step 4: Summarise ─────────────────────────────────────────────
        summary = {}
        try:
            summary = summarise(transcript, client, config)
            report["steps"]["summary"] = "ok"
            report["summary"] = summary
        except Exception as e:
            print(f"[WARN] GPT summary failed: {e}", file=sys.stderr)
            report["steps"]["summary"] = f"failed: {e}"
            if not config["pipeline"].get("fallbackToRawTranscriptOnSummaryFail", True):
                return {"status": "error", "code": "SUMMARY_FAILED", "error": str(e)}
            summary = {"summary": transcript[:500], "key_points": [], "action_items": []}

        if dry_run:
            report["dry_run"] = True
            report["transcript"] = transcript
            return report

        # ── Step 5: Find Bigin account ────────────────────────────────────
        account_name = account_hint or summary.get("account_name")
        account = None
        if account_name:
            account = find_account(account_name, config)

        if account:
            account_id = account.get("id")
            report["steps"]["account_lookup"] = f"found: {account.get('Account_Name')}"
        else:
            account_id = None
            report["steps"]["account_lookup"] = f"not found: {account_name}"

        # ── Step 5b: Find open deal ───────────────────────────────────────
        deal = None
        if deal_id:
            deal = {"id": deal_id}
            report["steps"]["deal_lookup"] = f"provided: {deal_id}"
        elif account_id:
            deal = find_open_deal(account_id, config)
            report["steps"]["deal_lookup"] = f"found: {deal.get('Deal_Name')}" if deal else "no open deal"

        target_id = deal.get("id") if deal else account_id
        target_module = config["bigin"]["dealModule"] if deal else config["bigin"]["accountModule"]

        if not target_id:
            report["steps"]["bigin_write"] = "skipped — no account or deal found"
            report["transcript"] = transcript
            return report

        # ── Step 6: Update pipeline stage ────────────────────────────────
        stage_change = summary.get("stage_change")
        if stage_change and deal:
            ok = update_deal_stage(deal["id"], stage_change, config)
            report["steps"]["stage_update"] = f"{'ok' if ok else 'failed'}: {stage_change}"
        else:
            report["steps"]["stage_update"] = "skipped"

        # ── Step 7: Add note ──────────────────────────────────────────────
        note_title = f"{config['bigin']['noteTitle']} {date.today().isoformat()} — {account_name or 'Call'}"
        note_content = build_note_content(summary, transcript)
        ok = add_note_to_record(target_module, target_id, note_title, note_content, config)
        report["steps"]["note"] = "ok" if ok else "failed"

        # ── Step 8: Create follow-up tasks ────────────────────────────────
        tasks_created = []
        for item in summary.get("action_items", []):
            days = item.get("due_days", task_due_days)
            due = due_date_str(days)
            task_id = create_task(
                target_id,
                item["task"],
                due,
                item.get("owner"),
                config,
            )
            tasks_created.append({
                "task": item["task"],
                "due": due,
                "id": task_id,
                "created": task_id is not None,
            })
        report["steps"]["tasks"] = f"{len([t for t in tasks_created if t['created']])} created"
        report["tasks"] = tasks_created

        return report

    finally:
        if config["pipeline"].get("cleanupTempFiles", True):
            shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Call to CRM — audio → transcript → Bigin")
    parser.add_argument("--input", required=True, help="Audio/video file path")
    parser.add_argument("--account", help="Bigin account name hint (auto-detected if omitted)")
    parser.add_argument("--deal-id", help="Specific Bigin deal ID (skips lookup)")
    parser.add_argument("--language", help="Audio language code e.g. en, hi (default: auto)")
    parser.add_argument("--task-due-days", type=int, default=3, help="Default task due days (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Transcribe and summarise only, no CRM writes")
    args = parser.parse_args()

    config = load_config()
    # Override task due days from CLI
    config["bigin"]["defaultTaskDueDays"] = args.task_due_days

    result = run(
        input_path=Path(args.input),
        account_hint=args.account,
        deal_id=args.deal_id,
        dry_run=args.dry_run,
        language=args.language,
        task_due_days=args.task_due_days,
        config=config,
    )
    out(result)


if __name__ == "__main__":
    main()
