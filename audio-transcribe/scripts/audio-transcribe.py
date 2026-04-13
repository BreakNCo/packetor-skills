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

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
FFMPEG_CANDIDATES = [
    WORKSPACE_ROOT / "bin" / "ffmpeg",
    Path("/data/npm/lib/node_modules/ffmpeg-static/ffmpeg"),
]

from transcribe_config import load_config, get_openai_key, out


# ---------------------------------------------------------------------------
# ffmpeg helpers
# ---------------------------------------------------------------------------

def resolve_ffmpeg() -> str | None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    for candidate in FFMPEG_CANDIDATES:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def check_ffmpeg() -> bool:
    return resolve_ffmpeg() is not None


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


def convert_audio(input_path: Path, output_path: Path, config: dict) -> None:
    """Convert any audio/video file to mono WAV at 16kHz using ffmpeg."""
    ffcfg = config["ffmpeg"]
    ffmpeg_bin = resolve_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg binary could not be resolved")
    cmd = [
        ffmpeg_bin, "-y",
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
    ffmpeg_bin = resolve_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg binary could not be resolved")
    duration = ffcfg["chunkDurationSeconds"]
    overlap = ffcfg["chunkOverlapSeconds"]
    segment_time = duration - overlap

    pattern = str(output_dir / "chunk_%03d.wav")
    cmd = [
        ffmpeg_bin, "-y",
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


def get_mean_volume_db(audio_path: Path) -> float:
    """
    Return the mean volume of an audio file in dBFS using ffmpeg volumedetect.
    Returns a large negative number (e.g. -91.0) on error or silence.
    """
    ffmpeg_bin = resolve_ffmpeg()
    if not ffmpeg_bin:
        return -91.0
    cmd = [
        ffmpeg_bin,
        "-i", str(audio_path),
        "-af", "volumedetect",
        "-vn", "-sn", "-dn",
        "-f", "null", "/dev/null",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "mean_volume" in line:
            # e.g. "  mean_volume: -29.4 dB"
            try:
                return float(line.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
    return -91.0


def is_silent_chunk(audio_path: Path, threshold_db: float = -50.0) -> bool:
    """Return True if the chunk is effectively silent (mean volume below threshold)."""
    vol = get_mean_volume_db(audio_path)
    print(f"[volume] {audio_path.name}: {vol:.1f} dB (threshold {threshold_db} dB)", file=sys.stderr)
    return vol < threshold_db


# ---------------------------------------------------------------------------
# Whisper helpers
# ---------------------------------------------------------------------------

def transcribe_chunk_verbose(
    audio_path: Path,
    client,
    model: str,
    language: str | None,
    translate: bool,
    temperature: float,
) -> list[dict]:
    """
    Transcribe a single chunk using verbose_json to get per-segment no_speech_prob.
    Returns list of segment dicts (start, end, text, no_speech_prob).
    """
    print(f"[whisper] Transcribing {audio_path.name} ({audio_path.stat().st_size // 1024}KB)", file=sys.stderr)
    with open(audio_path, "rb") as f:
        kwargs = dict(
            model=model,
            file=f,
            response_format="verbose_json",
            temperature=temperature,
            timestamp_granularities=["segment"],
        )
        if language:
            kwargs["language"] = language
        if translate:
            response = client.audio.translations.create(**kwargs)
        else:
            response = client.audio.transcriptions.create(**kwargs)
    return response.segments or []


def filter_hallucinated_segments(
    segments: list[dict],
    no_speech_threshold: float = 0.6,
) -> list[dict]:
    """
    Drop segments where no_speech_prob exceeds the threshold — these are
    Whisper hallucinations on silence or low-quality audio.
    """
    kept, dropped = [], 0
    for seg in segments:
        prob = getattr(seg, "no_speech_prob", 0.0)
        if prob >= no_speech_threshold:
            print(f"[SKIP] Segment '{getattr(seg, 'text', '').strip()[:40]}' no_speech_prob={prob:.2f}", file=sys.stderr)
            dropped += 1
        else:
            kept.append(seg)
    if dropped:
        print(f"[INFO] Dropped {dropped} hallucinated segment(s)", file=sys.stderr)
    return kept


def segments_to_text(segments: list[dict]) -> str:
    return " ".join(getattr(s, "text", "").strip() for s in segments).strip()


def segments_to_srt(segments: list[dict], offset_seconds: float = 0.0) -> str:
    def fmt_time(t: float) -> str:
        t += offset_seconds
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    lines = []
    for i, seg in enumerate(segments, 1):
        start = getattr(seg, "start", 0.0)
        end = getattr(seg, "end", 0.0)
        text = getattr(seg, "text", "").strip()
        lines.append(f"{i}\n{fmt_time(start)} --> {fmt_time(end)}\n{text}")
    return "\n\n".join(lines)


def segments_to_vtt(segments: list[dict], offset_seconds: float = 0.0) -> str:
    def fmt_time(t: float) -> str:
        t += offset_seconds
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"

    lines = ["WEBVTT", ""]
    for seg in segments:
        start = getattr(seg, "start", 0.0)
        end = getattr(seg, "end", 0.0)
        text = getattr(seg, "text", "").strip()
        lines.append(f"{fmt_time(start)} --> {fmt_time(end)}\n{text}")
    return "\n\n".join(lines)


def merge_transcripts(all_segments: list[list[dict]], fmt: str, chunk_duration: float) -> str:
    """
    Merge segments from all chunks into the requested output format.
    Timestamps are offset per chunk so they reflect position in the full audio.
    """
    import json as _json

    if fmt == "verbose_json":
        # Flatten with corrected timestamps
        flat = []
        for i, segs in enumerate(all_segments):
            offset = i * chunk_duration
            for seg in segs:
                d = seg.__dict__.copy() if hasattr(seg, "__dict__") else dict(seg)
                d["start"] = d.get("start", 0.0) + offset
                d["end"] = d.get("end", 0.0) + offset
                flat.append(d)
        return _json.dumps({"segments": flat}, indent=2)

    if fmt == "srt":
        parts = []
        counter = 1
        for i, segs in enumerate(all_segments):
            offset = i * chunk_duration
            for seg in segs:
                def fmt_time(t):
                    t += offset
                    h, rem = divmod(t, 3600)
                    m, s = divmod(rem, 60)
                    ms = int((s % 1) * 1000)
                    return f"{int(h):02}:{int(m):02}:{int(s):02},{ms:03}"
                start = getattr(seg, "start", 0.0)
                end = getattr(seg, "end", 0.0)
                text = getattr(seg, "text", "").strip()
                parts.append(f"{counter}\n{fmt_time(start)} --> {fmt_time(end)}\n{text}")
                counter += 1
        return "\n\n".join(parts)

    if fmt == "vtt":
        lines = ["WEBVTT", ""]
        for i, segs in enumerate(all_segments):
            offset = i * chunk_duration
            for seg in segs:
                def fmt_time(t):
                    t += offset
                    h, rem = divmod(t, 3600)
                    m, s = divmod(rem, 60)
                    ms = int((s % 1) * 1000)
                    return f"{int(h):02}:{int(m):02}:{int(s):02}.{ms:03}"
                start = getattr(seg, "start", 0.0)
                end = getattr(seg, "end", 0.0)
                text = getattr(seg, "text", "").strip()
                lines.append(f"{fmt_time(start)} --> {fmt_time(end)}\n{text}")
        return "\n\n".join(lines)

    # Default: plain text
    parts = [segments_to_text(segs) for segs in all_segments if segs]
    return "\n\n".join(p for p in parts if p)


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
        return {
            "status": "error",
            "code": "FFMPEG_NOT_FOUND",
            "hint": (
                "No ffmpeg found on PATH or in fallback locations. "
                "Expected one of: /data/workspace/bin/ffmpeg or "
                "/data/npm/lib/node_modules/ffmpeg-static/ffmpeg"
            ),
        }

    # OpenAI client
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

    wcfg = config["whisper"]
    ocfg = config["output"]
    max_bytes = wcfg["maxFileSizeBytes"]

    temp_dir = Path(tempfile.mkdtemp(prefix="audio-transcribe-"))

    try:
        # 1. Convert to WAV
        converted = temp_dir / "converted.wav"
        convert_audio(input_path, converted, config)

        file_size = converted.stat().st_size
        chunk_duration = config["ffmpeg"]["chunkDurationSeconds"]
        print(
            f"[INFO] Converted audio size: {file_size // 1024}KB; splitting into {chunk_duration}s chunks",
            file=sys.stderr,
        )

        # 2. Always split into chunkDurationSeconds-sized chunks before Whisper.
        chunks_dir = temp_dir / "chunks"
        chunks_dir.mkdir()
        chunks = split_audio(converted, chunks_dir, config)
        if not chunks:
            chunks = [converted]

        # 3. Transcribe each chunk using verbose_json internally so we can
        #    filter hallucinated segments by no_speech_prob, regardless of the
        #    requested output format.
        silence_threshold_db = wcfg.get("silenceThresholdDb", -50.0)
        no_speech_threshold = wcfg.get("noSpeechThreshold", 0.6)
        all_segments = []
        for chunk in chunks:
            if is_silent_chunk(chunk, threshold_db=silence_threshold_db):
                print(f"[SKIP] {chunk.name} is silent, skipping to avoid hallucination", file=sys.stderr)
                all_segments.append([])
                continue
            try:
                segs = transcribe_chunk_verbose(
                    chunk, client,
                    model=wcfg["model"],
                    language=language,
                    translate=translate,
                    temperature=wcfg["temperature"],
                )
                segs = filter_hallucinated_segments(segs, no_speech_threshold=no_speech_threshold)
                all_segments.append(segs)
            except Exception as e:
                print(f"[WARN] Chunk {chunk.name} failed: {e}", file=sys.stderr)
                all_segments.append([])

        # 4. Merge into the requested output format
        transcript = merge_transcripts(all_segments, fmt, chunk_duration=chunk_duration)

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
    ensure_openai_runtime()
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
