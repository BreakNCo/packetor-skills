"""
Audio Transcribe skill — shared config and utilities.
"""

import json
import os
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config" / "transcribe-config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "ffmpeg": {
            "sampleRate": 16000,
            "channels": 1,
            "codec": "pcm_s16le",
            "format": "wav",
            "chunkDurationSeconds": 60,
            "chunkOverlapSeconds": 0,
        },
        "whisper": {
            "model": "whisper-1",
            "defaultLanguage": None,
            "defaultFormat": "text",
            "maxFileSizeBytes": 26214400,
            "temperature": 0,
        },
        "output": {
            "defaultFormat": "text",
            "cleanupTempFiles": True,
            "tempDir": "/tmp/audio-transcribe",
        },
    }


def get_openai_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise EnvironmentError("OPENAI_API_KEY is not set")
    return key


def out(data: dict) -> None:
    print(json.dumps(data, indent=2))
