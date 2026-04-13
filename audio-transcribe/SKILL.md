---
name: audio-transcribe
description: Convert audio files to the correct format using ffmpeg and transcribe them using OpenAI Whisper API. Use this skill when asked to transcribe a meeting, call recording, voice note, or any audio/video file into text.
version: 1.0.0
compatibility: openclaw
tools: []
---

# Audio Transcribe

Converts audio or video files to a Whisper-compatible format via ffmpeg, splits them into 1-minute chunks, then transcribes each chunk with the OpenAI Whisper API and merges the results. Outputs plain text, timestamped SRT, or structured JSON.

## When to Use

- Transcribe a meeting recording, sales call, or support call
- Convert a voice note to text
- Generate subtitles (SRT) from a video
- Transcribe any audio/video file regardless of format (mp4, mov, m4a, webm, mkv, wav, mp3, etc.)

## When NOT to Use

- Real-time/live transcription — Whisper is file-based only
- Files larger than 500MB — split first or use `--chunk` mode
- Non-audio files (PDFs, images) — use a different skill

## Prerequisites

**System dependencies:**
- `ffmpeg` — must be installed and on PATH (`brew install ffmpeg` on Mac)

**Environment variables:**
- `OPENAI_API_KEY` — OpenAI API key with Whisper access

**Python dependencies:**
- `openai>=1.0.0` — `pip install openai`

## Workflow

The agent runs `audio-transcribe.py`. The script handles all ffmpeg conversion and Whisper API calls internally. The agent only needs to provide the input file path and desired output format.

### 1. Convert with ffmpeg
Input file is converted to mono 16kHz WAV (optimal for Whisper) using ffmpeg. The original file is never modified.

### 2. Split into 1-minute chunks
Every file is split into 60-second chunks using ffmpeg segment before transcription. This keeps requests small and makes long or messy recordings more resilient.

### 3. Transcribe with Whisper
Each chunk is sent to `openai.audio.transcriptions.create` with the configured model (`whisper-1`). Timestamps are requested when output format is `srt` or `verbose_json`.

### 4. Output
Chunk transcripts are merged in order and written to the output file (or stdout). The temp converted file is cleaned up automatically.

## Script Usage

```bash
# Basic transcription to text
python3 audio-transcribe.py --input meeting.mp4

# Save to file
python3 audio-transcribe.py --input call.m4a --output call.txt

# SRT subtitles
python3 audio-transcribe.py --input recording.mp4 --format srt --output recording.srt

# Specify language (faster, more accurate)
python3 audio-transcribe.py --input audio.mp3 --language en

# Verbose JSON (includes word-level timestamps)
python3 audio-transcribe.py --input audio.wav --format verbose_json --output result.json

# Translate to English (from any language)
python3 audio-transcribe.py --input french-call.mp4 --translate
```

## Output Formats

| Format | Description |
|--------|-------------|
| `text` | Plain transcript (default) |
| `srt` | Subtitles with timestamps |
| `vtt` | WebVTT subtitles |
| `verbose_json` | Full JSON with word-level timestamps and confidence |

## Error Handling

All errors return structured JSON to stdout. Logs go to stderr only.

Common codes:
- `FFMPEG_NOT_FOUND` — ffmpeg not installed or not on PATH
- `INPUT_NOT_FOUND` — input file does not exist
- `FILE_TOO_LARGE` — file exceeds limit even after conversion (use `--chunk`)
- `OPENAI_AUTH_FAILED` — invalid or missing `OPENAI_API_KEY`
- `TRANSCRIPTION_FAILED` — Whisper API error, check stderr for details
