#!/usr/bin/env python3
"""
Audio Transcribe v1.0.0

Converts audio/video files using ffmpeg and transcribes with OpenAI Whisper.

Usage:
    python3 audio-transcribe.py --input meeting.mp4
    python3 audio-transcribe.py --input call.m4a --output call.txt
    python3 audio-transcribe.py --input video.mp4 --format srt --output video.srt
    python3 audio-transcribe.py --input audio.mp3 --language en --translate

Output: transcript to stdout (or --output file), status JSON on error
Logs:   stderr only
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from transcribe_config import load_config, get_openai_key, out


# ---------------------------------------------------------------------------
# ffmpeg helpers
# ---------------------------------------------------------------------------

def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def convert_audio(input_path: Path, output_path: Path, config: dict) -> None:
    """Convert any audio/video file to mono WAV at 16kHz using ffmpeg."""
    ffcfg = config["ffmpeg"]
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-ar", str(ffcfg["sampleRate"]),
        "-ac", str(ffcfg["channels"]),
        "-acodec", ffcfg["codec"],
        str(output_path),
    ]
    print(f"[ffmpeg] Converting {input_path.name} → {output_path.name}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed:\n{result.stderr}")


def split_audio(input_path: Path, output_dir: Path, config: dict) -> list[Path]:
    """
    Split a WAV file into chunks using ffmpeg segment.
    Returns list of chunk paths in order.
    """
    ffcfg = config["ffmpeg"]
    duration = ffcfg["chunkDurationSeconds"]
    overlap = ffcfg["chunkOverlapSeconds"]
    segment_time = duration - overlap

    pattern = str(output_dir / "chunk_%03d.wav")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-f", "segment",
        "-segment_time", str(segment_time),
        "-ar", str(ffcfg["sampleRate"]),
        "-ac", str(ffcfg["channels"]),
        "-acodec", ffcfg["codec"],
        "-reset_timestamps", "1",
        pattern,
    ]
    print(f"[ffmpeg] Splitting into {segment_time}s chunks", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg split failed:\n{result.stderr}")

    chunks = sorted(output_dir.glob("chunk_*.wav"))
    print(f"[ffmpeg] Created {len(chunks)} chunks", file=sys.stderr)
    return chunks


# ---------------------------------------------------------------------------
# Whisper helpers
# ---------------------------------------------------------------------------

def transcribe_file(
    audio_path: Path,
    client,
    model: str,
    language: str | None,
    fmt: str,
    translate: bool,
    temperature: float,
) -> str:
    """Send a single file to Whisper API. Returns transcript string."""
    print(f"[whisper] Transcribing {audio_path.name} ({audio_path.stat().st_size // 1024}KB)", file=sys.stderr)

    with open(audio_path, "rb") as f:
        kwargs = dict(
            model=model,
            file=f,
            response_format=fmt,
            temperature=temperature,
        )
        if language:
            kwargs["language"] = language

        if translate:
            response = client.audio.translations.create(**kwargs)
        else:
            response = client.audio.transcriptions.create(**kwargs)

    # response is a string for text/srt/vtt, object for verbose_json
    if fmt == "verbose_json":
        import json as _json
        return _json.dumps(response.model_dump(), indent=2)
    return str(response)


def merge_transcripts(parts: list[str], fmt: str) -> str:
    """Merge transcript chunks. For SRT, renumber entries sequentially."""
    if fmt != "srt":
        return "\n\n".join(p.strip() for p in parts if p.strip())

    merged = []
    counter = 1
    for part in parts:
        for block in part.strip().split("\n\n"):
            lines = block.strip().splitlines()
            if len(lines) >= 2:
                lines[0] = str(counter)
                merged.append("\n".join(lines))
                counter += 1
    return "\n\n".join(merged)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(
    input_path: Path,
    output_path: Path | None,
    fmt: str,
    language: str | None,
    translate: bool,
    config: dict,
) -> dict:

    # Validate input
    if not input_path.exists():
        return {"status": "error", "code": "INPUT_NOT_FOUND", "path": str(input_path)}

    if not check_ffmpeg():
        return {"status": "error", "code": "FFMPEG_NOT_FOUND", "hint": "Install ffmpeg: brew install ffmpeg"}

    # OpenAI client
    try:
        api_key = get_openai_key()
    except EnvironmentError as e:
        return {"status": "error", "code": "OPENAI_AUTH_FAILED", "hint": str(e)}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        return {"status": "error", "code": "MISSING_DEPENDENCY", "hint": "pip install openai"}

    wcfg = config["whisper"]
    ocfg = config["output"]
    max_bytes = wcfg["maxFileSizeBytes"]

    temp_dir = Path(tempfile.mkdtemp(prefix="audio-transcribe-"))

    try:
        # 1. Convert to WAV
        converted = temp_dir / "converted.wav"
        convert_audio(input_path, converted, config)

        file_size = converted.stat().st_size

        # 2. Split if over limit
        if file_size > max_bytes:
            print(f"[INFO] File {file_size // (1024*1024)}MB > limit, splitting", file=sys.stderr)
            chunks_dir = temp_dir / "chunks"
            chunks_dir.mkdir()
            chunks = split_audio(converted, chunks_dir, config)
        else:
            chunks = [converted]

        # 3. Transcribe each chunk
        parts = []
        for chunk in chunks:
            try:
                text = transcribe_file(
                    chunk, client,
                    model=wcfg["model"],
                    language=language,
                    fmt=fmt,
                    translate=translate,
                    temperature=wcfg["temperature"],
                )
                parts.append(text)
            except Exception as e:
                print(f"[WARN] Chunk {chunk.name} failed: {e}", file=sys.stderr)
                parts.append("")

        # 4. Merge
        transcript = merge_transcripts(parts, fmt)

        # 5. Output
        if output_path:
            output_path.write_text(transcript, encoding="utf-8")
            print(f"[INFO] Written to {output_path}", file=sys.stderr)
        else:
            print(transcript)

        return {
            "status": "ok",
            "input": str(input_path),
            "output": str(output_path) if output_path else "stdout",
            "format": fmt,
            "chunks": len(chunks),
            "language": language or "auto-detected",
            "translated": translate,
        }

    except Exception as e:
        return {"status": "error", "code": "TRANSCRIPTION_FAILED", "error": str(e)}

    finally:
        if ocfg.get("cleanupTempFiles", True):
            import shutil as _shutil
            _shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Audio Transcribe — ffmpeg + OpenAI Whisper")
    parser.add_argument("--input", required=True, help="Input audio/video file path")
    parser.add_argument("--output", help="Output file path (default: stdout)")
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

    # Only print JSON status on error (transcript already printed in run())
    if result["status"] != "ok" or args.output:
        out(result)


if __name__ == "__main__":
    main()
