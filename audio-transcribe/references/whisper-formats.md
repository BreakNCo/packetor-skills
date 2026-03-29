# Whisper Output Formats & Supported Audio

## Output Formats

| Format | Flag | Best for |
|--------|------|----------|
| `text` | `--format text` | Plain transcript, notes, CRM updates |
| `srt` | `--format srt` | Video subtitles, Zoom recordings |
| `vtt` | `--format vtt` | Web video subtitles (HTML5) |
| `verbose_json` | `--format verbose_json` | Word-level timestamps, confidence scores |

## Supported Input Formats

ffmpeg handles virtually any format. Common ones:

| Format | Extension | Notes |
|--------|-----------|-------|
| MP4 video | `.mp4` | Zoom, Loom, screen recordings |
| QuickTime | `.mov` | Mac screen recordings |
| WebM | `.webm` | Google Meet, browser recordings |
| Matroska | `.mkv` | General video |
| MP3 audio | `.mp3` | Podcasts, voice notes |
| M4A audio | `.m4a` | iPhone voice memos, Apple |
| WAV audio | `.wav` | Uncompressed, already compatible |
| OGG | `.ogg` | Open-source audio |
| FLAC | `.flac` | Lossless audio |

All formats are converted to mono 16kHz WAV before sending to Whisper.

## Language Codes

Specify `--language` for faster, more accurate results:

| Language | Code |
|----------|------|
| English | `en` |
| Hindi | `hi` |
| Tamil | `ta` |
| French | `fr` |
| Spanish | `es` |
| German | `de` |
| Japanese | `ja` |
| Chinese | `zh` |
| Arabic | `ar` |

Omit `--language` to let Whisper auto-detect.

## File Size Limits

- Whisper API max: **25MB per request**
- The script auto-converts to 16kHz mono WAV which is much smaller than the original
- Files still over 25MB after conversion are auto-split into 10-minute chunks with 2-second overlap to avoid cutting mid-word

## Whisper Models

Only `whisper-1` is available via the OpenAI API. It supports 99 languages and achieves near-human accuracy on clear speech.

## Cost

OpenAI charges per minute of audio: ~$0.006/minute as of early 2026.
A 1-hour meeting costs approximately $0.36.
