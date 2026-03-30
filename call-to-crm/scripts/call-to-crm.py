#!/usr/bin/env python3
"""
Call to CRM v1.0.0

Transcription pipeline only:
  audio file → ffmpeg conversion → Whisper transcription

CRM reasoning, Bigin lookup, stage decisions, and note/task writing
are intentionally handled by the agent after transcript generation.

Usage:
    python3 call-to-crm.py --input call.mp4
    python3 call-to-crm.py --input call.mp4 --account "Acme Corp"
    python3 call-to-crm.py --input call.mp4 --deal-id "<bigin_deal_id>"
    python3 call-to-crm.py --input call.mp4 --dry-run
    python3 call-to-crm.py --input call.mp4 --language en

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

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"

from call_to_crm_config import load_config, get_openai_key, out


# ---------------------------------------------------------------------------
# Step 1 & 2: Audio conversion via ffmpeg
# ---------------------------------------------------------------------------

def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def ensure_openai_runtime() -> None:
    """Re-exec into the workspace venv if system python lacks openai."""
    if os.environ.get("PACKETOR_CALL_TO_CRM_VENV") == "1":
        return
    try:
        import openai  # noqa: F401
        return
    except ImportError:
        pass

    if VENV_PYTHON.exists():
        env = os.environ.copy()
        env["PACKETOR_CALL_TO_CRM_VENV"] = "1"
        os.execve(str(VENV_PYTHON), [str(VENV_PYTHON), __file__, *sys.argv[1:]], env)


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
# Main pipeline
# ---------------------------------------------------------------------------

def run(
    input_path: Path,
    account_hint: str | None,
    deal_id: str | None,
    dry_run: bool,
    language: str | None,
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
        return {
            "status": "error",
            "code": "MISSING_DEPENDENCY",
            "hint": f"Install openai in system python or create workspace venv at {VENV_PYTHON}",
        }

    temp_dir = Path(tempfile.mkdtemp(prefix="call-to-crm-"))
    report: dict = {
        "status": "ok",
        "mode": "transcription_only",
        "steps": {},
        "account_hint": account_hint,
        "deal_id": deal_id,
    }

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

        report["transcript"] = transcript
        report["steps"]["crm"] = "deferred_to_agent"
        report["instructions"] = {
            "next": [
                "Summarize transcript in CRM language",
                "Find matching Bigin account/deal",
                "Update pipeline only if clearly justified",
                "Add note to Pipeline record only unless explicitly asked otherwise",
                "Create follow-up tasks only for concrete next actions",
            ]
        }
        return report

    finally:
        if config["pipeline"].get("cleanupTempFiles", True):
            shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ensure_openai_runtime()
    parser = argparse.ArgumentParser(description="Call to CRM — audio → transcript → Bigin")
    parser.add_argument("--input", required=True, help="Audio/video file path")
    parser.add_argument("--account", help="Optional Bigin account name hint for the agent")
    parser.add_argument("--deal-id", help="Optional Bigin deal ID hint for the agent")
    parser.add_argument("--language", help="Audio language code e.g. en, hi (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="Transcribe only, no CRM writes")
    args = parser.parse_args()

    config = load_config()

    result = run(
        input_path=Path(args.input),
        account_hint=args.account,
        deal_id=args.deal_id,
        dry_run=args.dry_run,
        language=args.language,
        config=config,
    )
    out(result)


if __name__ == "__main__":
    main()
