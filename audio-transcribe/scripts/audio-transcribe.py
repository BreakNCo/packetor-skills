#!/usr/bin/env python3
"""
Audio Transcribe v1.1.0

Converts audio/video files using ffmpeg and transcribes with OpenAI Whisper.

Usage:
    python3 audio-transcribe.py --input meeting.mp4 --language en
    python3 audio-transcribe.py --input call.m4a --output call.txt --language en
    python3 audio-transcribe.py --input video.mp4 --format srt --language en
    python3 audio-transcribe.py --input audio.mp3 --language en --translate

Output: transcript saved alongside input file (or --output path), status JSON to stdout
Logs:   stderr only
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"

from transcribe_config import load_config, get_openai_key, out
from transcribe_core import check_ffmpeg, run_transcription


def ensure_openai_runtime() -> None:
    if os.environ.get("PACKETOR_AUDIO_TRANSCRIBE_VENV") == "1":
        return
    try:
        import openai  # noqa: F401
        return
    except ImportError:
        pass
    if VENV_PYTHON.exists():
        env = os.environ.copy()
        env["PACKETOR_AUDIO_TRANSCRIBE_VENV"] = "1"
        os.execve(str(VENV_PYTHON), [str(VENV_PYTHON), __file__, *sys.argv[1:]], env)


def run(
    input_path: Path,
    output_path: Path | None,
    fmt: str,
    language: str | None,
    translate: bool,
    config: dict,
) -> dict:

    if not input_path.exists():
        return {"status": "error", "code": "INPUT_NOT_FOUND", "path": str(input_path)}

    if not check_ffmpeg():
        return {
            "status": "error",
            "code": "FFMPEG_NOT_FOUND",
            "hint": (
                "No ffmpeg found on PATH or in fallback locations. "
                "Expected one of: /data/workspace/bin/ffmpeg or "
                "/data/npm/lib/node_modules/ffmpeg-static/ffmpeg"
            ),
        }

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

    ocfg = config["output"]
    temp_dir = Path(tempfile.mkdtemp(prefix="audio-transcribe-"))

    try:
        transcript = run_transcription(
            input_path=input_path,
            temp_dir=temp_dir,
            client=client,
            config=config,
            language=language,
            translate=translate,
            fmt=fmt,
        )

        # Save to file — default to <input_stem>.<ext> alongside the input
        ext_map = {"text": "txt", "srt": "srt", "vtt": "vtt", "verbose_json": "json"}
        if output_path is None:
            output_path = input_path.with_suffix("." + ext_map.get(fmt, "txt"))

        output_path.write_text(transcript, encoding="utf-8")
        print(f"[INFO] Written to {output_path}", file=sys.stderr)

        return {
            "status": "ok",
            "input": str(input_path),
            "output": str(output_path),
            "format": fmt,
            "language": language or "auto-detected",
            "translated": translate,
        }

    except Exception as e:
        return {"status": "error", "code": "TRANSCRIPTION_FAILED", "error": str(e)}

    finally:
        if ocfg.get("cleanupTempFiles", True):
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    ensure_openai_runtime()
    parser = argparse.ArgumentParser(description="Audio Transcribe — ffmpeg + OpenAI Whisper")
    parser.add_argument("--input", required=True, help="Input audio/video file path")
    parser.add_argument("--output", help="Output file path (default: alongside input file)")
    parser.add_argument("--format", choices=["text", "srt", "vtt", "verbose_json"], default=None,
                        help="Output format (default: text)")
    parser.add_argument("--language", help="Audio language code e.g. en, hi, fr (default: auto-detect)")
    parser.add_argument("--translate", action="store_true", help="Translate to English")
    args = parser.parse_args()

    config = load_config()
    fmt = args.format or config["whisper"]["defaultFormat"]

    result = run(
        input_path=Path(args.input),
        output_path=Path(args.output) if args.output else None,
        fmt=fmt,
        language=args.language,
        translate=args.translate,
        config=config,
    )
    out(result)


if __name__ == "__main__":
    main()
