"""Load skill credentials from packetor-skills .env files."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent
CMS_TOOLS = SKILL_ROOT / "cms-tools"

CMS_ENV_KEYS = ("DATABASE_URI", "PAYLOAD_SECRET")

HUMANIZER_ENV_KEYS = (
    "SMODIN_API_KEY",
    "SMODIN_API_URL",
    "SMODIN_API_HOST",
    "WORDAI_EMAIL",
    "WORDAI_API_KEY",
    "WORDAI_API_URL",
    "SPINREWRITER_EMAIL",
    "SPINREWRITER_API_KEY",
    "SPINREWRITER_API_URL",
    "WRITEHUMAN_API_KEY",
    "WRITEHUMAN_API_URL",
    "STEALTHWRITER_API_KEY",
    "STEALTHWRITER_API_URL",
    "QUILLBOT_EMAIL",
    "QUILLBOT_PASSWORD",
)


def _parse_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].strip()
        if "=" not in stripped:
            continue
        key, _, raw = stripped.partition("=")
        key = key.strip()
        value = raw.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            out[key] = value
    return out


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def extract_json(raw: str) -> object:
    """Parse the first JSON value in mixed CLI output (Payload logs, bun banners)."""
    cleaned = ANSI_RE.sub("", raw)
    decoder = json.JSONDecoder()
    for i, ch in enumerate(cleaned):
        if ch not in "{[":
            continue
        # Skip Payload timestamps like [20:23:00]
        if ch == "[" and i + 1 < len(cleaned) and cleaned[i + 1].isdigit():
            continue
        try:
            obj, _ = decoder.raw_decode(cleaned, i)
            return obj
        except json.JSONDecodeError:
            continue
    raise json.JSONDecodeError("No JSON in subprocess output", cleaned, 0)


def dotenv_paths() -> list[Path]:
    explicit = os.environ.get("PACKETOR_SKILLS_ENV")
    paths: list[Path] = []
    if explicit:
        paths.append(Path(explicit).expanduser().resolve())
    paths.extend(
        [
            REPO_ROOT / ".env",
            SKILL_ROOT / ".env",
        ]
    )
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def load_skill_env_from_files() -> dict[str, str]:
    """Values from .env files (earlier paths win)."""
    merged: dict[str, str] = {}
    for path in dotenv_paths():
        for key, value in _parse_dotenv(path).items():
            if key not in merged and value:
                merged[key] = value
    return merged


def apply_dotenv_to_os() -> None:
    """Fill os.environ from .env when keys are not already set."""
    for key, value in load_skill_env_from_files().items():
        if not os.environ.get(key):
            os.environ[key] = value


def subprocess_env() -> dict[str, str]:
    """Process env plus .env values, with NODE_ENV=production for Payload CLI."""
    apply_dotenv_to_os()
    env = os.environ.copy()
    env.setdefault("NODE_ENV", "production")
    return env


def cms_env_status() -> dict[str, object]:
    apply_dotenv_to_os()
    from_files = load_skill_env_from_files()
    keys = CMS_ENV_KEYS + HUMANIZER_ENV_KEYS
    return {
        "dotenvPathsChecked": [str(p) for p in dotenv_paths()],
        "fromProcessEnv": {k: bool(os.environ.get(k)) for k in CMS_ENV_KEYS},
        "fromDotenv": {k: k in from_files for k in CMS_ENV_KEYS},
        "resolved": {k: bool(subprocess_env().get(k)) for k in CMS_ENV_KEYS},
        "humanizerFromDotenv": {k: k in from_files for k in HUMANIZER_ENV_KEYS if k in from_files},
        "cmsKeys": list(keys[:2]),
    }


def missing_cms_env_hint() -> str:
    paths = ", ".join(str(p) for p in dotenv_paths())
    return (
        "Set DATABASE_URI and PAYLOAD_SECRET in the process environment, "
        f"or in packetor-skills/.env (checked: {paths})."
    )


def cms_tools_dir() -> Path:
    return CMS_TOOLS


def cms_tools_installed() -> bool:
    return (CMS_TOOLS / "node_modules" / "payload").is_dir()
