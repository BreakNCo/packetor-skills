"""
transcribe_core.py — shared audio transcription pipeline.

Provides the full improved transcription path:
  - ffmpeg conversion to mono 16kHz WAV
  - always-split into fixed-length chunks
  - silence detection (skip truly silent chunks)
  - verbose_json transcription per chunk
  - no_speech_prob hallucination filtering
  - merge into text / srt / vtt / verbose_json

Used by both audio-transcribe.py and call-to-crm.py.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# ffmpeg helpers
# ---------------------------------------------------------------------------

FFMPEG_CANDIDATES = [
    Path(__file__).resolve().parent.parent.parent.parent / "bin" / "ffmpeg",
    Path("/data/npm/lib/node_modules/ffmpeg-static/ffmpeg"),
]


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
    """Split a WAV file into fixed-length chunks. Returns sorted list of chunk paths."""
    ffcfg = config["ffmpeg"]
    ffmpeg_bin = resolve_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg binary could not be resolved")
    segment_time = ffcfg["chunkDurationSeconds"] - ffcfg["chunkOverlapSeconds"]
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
    """Return mean volume in dBFS. Returns -91.0 on error or silence."""
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
            try:
                return float(line.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
    return -91.0


def is_silent_chunk(audio_path: Path, threshold_db: float = -50.0) -> bool:
    """Return True if chunk mean volume is below threshold."""
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
) -> list:
    """
    Transcribe a single chunk using verbose_json to get per-segment no_speech_prob.
    Returns list of segment objects.
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


def filter_hallucinated_segments(segments: list, no_speech_threshold: float = 0.85) -> list:
    """Drop segments where no_speech_prob exceeds threshold."""
    kept, dropped = [], 0
    for seg in segments:
        prob = getattr(seg, "no_speech_prob", 0.0)
        if prob >= no_speech_threshold:
            print(
                f"[SKIP] Segment '{getattr(seg, 'text', '').strip()[:40]}' no_speech_prob={prob:.2f}",
                file=sys.stderr,
            )
            dropped += 1
        else:
            kept.append(seg)
    if dropped:
        print(f"[INFO] Dropped {dropped} hallucinated segment(s)", file=sys.stderr)
    return kept


def segments_to_text(segments: list) -> str:
    return " ".join(getattr(s, "text", "").strip() for s in segments).strip()


def merge_transcripts(all_segments: list[list], fmt: str, chunk_duration: float) -> str:
    """Merge segments from all chunks into the requested output format with corrected timestamps."""
    import json as _json

    if fmt == "verbose_json":
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
                def fmt_time(t, _offset=offset):
                    t += _offset
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
                def fmt_time(t, _offset=offset):
                    t += _offset
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
# Full pipeline entry point
# ---------------------------------------------------------------------------

def run_transcription(
    input_path: Path,
    temp_dir: Path,
    client,
    config: dict,
    language: str | None = None,
    translate: bool = False,
    fmt: str = "text",
) -> str:
    """
    Full transcription pipeline: convert → split → filter silence →
    transcribe with verbose_json → filter hallucinations → merge.

    Returns the transcript string in the requested format.
    Raises RuntimeError on failure.
    """
    wcfg = config["whisper"]
    chunk_duration = config["ffmpeg"]["chunkDurationSeconds"]
    silence_threshold_db = wcfg.get("silenceThresholdDb", -50.0)
    no_speech_threshold = wcfg.get("noSpeechThreshold", 0.85)

    # 1. Convert to WAV
    converted = temp_dir / "converted.wav"
    convert_audio(input_path, converted, config)
    print(
        f"[INFO] Converted audio size: {converted.stat().st_size // 1024}KB; "
        f"splitting into {chunk_duration}s chunks",
        file=sys.stderr,
    )

    # 2. Always split into chunks
    chunks_dir = temp_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    chunks = split_audio(converted, chunks_dir, config)
    if not chunks:
        chunks = [converted]

    # 3. Transcribe each chunk
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

    # 4. Merge
    return merge_transcripts(all_segments, fmt=fmt, chunk_duration=chunk_duration)
