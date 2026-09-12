#!/usr/bin/env python3
"""Pluggable humanizer dispatch for blog-content-publish.

Stdin JSON: {provider, text}
Stdout JSON: {provider, rewrittenText?, instructions?, status, reason?}

API providers skip (never crash) when credentials are missing.
QuillBot uses the unofficial SDK and the user's own account — not Toolzbuy session state.
Run this on prose only, before inserting <a href> markup.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cms_env import apply_dotenv_to_os

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent
VENV_CANDIDATES = [
    SKILL_ROOT.parent / ".venv" / "bin" / "python",
    SKILL_ROOT.parent.parent / ".venv" / "bin" / "python",
]

LLM_INSTRUCTIONS = (
    "Rewrite the following prose so it sounds like a specialist wrote it, not a chatbot. "
    "Vary sentence length. Cut filler and stock transitions. Keep every fact, number, "
    "product claim, and keyword unchanged. Do not add headings, links, or HTML. "
    "Do not invent customers, certifications, or statistics."
)

MANUAL_TOOLS = {
    "phrasly": {
        "label": "Phrasly AI",
        "url": "https://app.toolzbuy.com",
        "hint": "Writer's Pack / individual Toolzbuy tool. No public API — paste prose, copy result.",
    },
    "humanizer-tech": {
        "label": "Humanizer.tech AI",
        "url": "https://app.toolzbuy.com",
        "hint": "On Toolzbuy Advance as a dashboard session. No public API.",
    },
    "toolzbuy-ai-humanizer": {
        "label": "Toolzbuy AI Humanizer",
        "url": "https://app.toolzbuy.com",
        "hint": "Generic Advance-plan humanizer label. Dashboard only.",
    },
}


def ensure_quillbot_runtime() -> None:
    if os.environ.get("PACKETOR_QUILLBOT_VENV") == "1":
        return
    try:
        import quillbot  # noqa: F401
        return
    except ImportError:
        pass
    for python in VENV_CANDIDATES:
        if python.exists():
            env = os.environ.copy()
            env["PACKETOR_QUILLBOT_VENV"] = "1"
            os.execve(str(python), [str(python), str(SCRIPT_PATH)], env)


def skipped(provider: str, reason: str) -> dict:
    return {
        "provider": provider,
        "status": "skipped",
        "reason": reason,
        "fallbackSuggestion": "llm",
    }


def json_post(url: str, payload: dict, headers: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def form_post(url: str, fields: dict) -> dict:
    encoded = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def first_text(data: object, keys: tuple[str, ...]) -> str | None:
    if isinstance(data, str) and data.strip():
        return data
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
            if isinstance(value, list) and value:
                nested = first_text(value[0], keys)
                if nested:
                    return nested
        for value in data.values():
            nested = first_text(value, keys)
            if nested:
                return nested
    if isinstance(data, list) and data:
        return first_text(data[0], keys)
    return None


def humanize_smodin(text: str) -> dict:
    key = os.environ.get("SMODIN_API_KEY")
    if not key:
        return skipped("smodin", "SMODIN_API_KEY is not set")
    url = os.environ.get(
        "SMODIN_API_URL",
        "https://rewriter-paraphraser-text-changer-multi-language.p.rapidapi.com/rewrite",
    )
    host = os.environ.get("SMODIN_API_HOST", "rewriter-paraphraser-text-changer-multi-language.p.rapidapi.com")
    data = json_post(
        url,
        {"text": text, "language": "en", "strength": 2},
        {"x-rapidapi-key": key, "x-rapidapi-host": host},
    )
    rewritten = first_text(data, ("rewrite", "text", "result", "output"))
    if not rewritten:
        return skipped("smodin", f"Unexpected Smodin response keys: {list(data)[:8]}")
    return {"provider": "smodin", "status": "ok", "rewrittenText": rewritten}


def humanize_wordai(text: str) -> dict:
    email = os.environ.get("WORDAI_EMAIL")
    key = os.environ.get("WORDAI_API_KEY")
    if not email or not key:
        return skipped("wordai", "WORDAI_EMAIL and WORDAI_API_KEY are required")
    url = os.environ.get("WORDAI_API_URL", "https://wai.wordai.com/api/rewrite")
    data = json_post(url, {"email": email, "key": key, "input": text, "rewrite_num": 1}, {})
    rewritten = first_text(data, ("text", "output", "rewrite", "result"))
    if not rewritten:
        return skipped("wordai", f"Unexpected WordAI response keys: {list(data)[:8]}")
    return {"provider": "wordai", "status": "ok", "rewrittenText": rewritten}


def humanize_spinrewriter(text: str) -> dict:
    email = os.environ.get("SPINREWRITER_EMAIL")
    key = os.environ.get("SPINREWRITER_API_KEY")
    if not email or not key:
        return skipped("spinrewriter", "SPINREWRITER_EMAIL and SPINREWRITER_API_KEY are required")
    url = os.environ.get("SPINREWRITER_API_URL", "https://www.spinrewriter.com/action/api")
    data = form_post(
        url,
        {
            "email_address": email,
            "api_key": key,
            "action": "unique_variation",
            "text": text,
        },
    )
    rewritten = first_text(data, ("response", "text", "result"))
    if not rewritten:
        return skipped("spinrewriter", f"Unexpected Spin Rewriter response: {data.get('status')}")
    return {"provider": "spinrewriter", "status": "ok", "rewrittenText": rewritten}


def humanize_writehuman(text: str) -> dict:
    key = os.environ.get("WRITEHUMAN_API_KEY")
    if not key:
        return skipped("writehuman", "WRITEHUMAN_API_KEY is not set")
    url = os.environ.get("WRITEHUMAN_API_URL", "https://api.writehuman.ai/v1/humanize")
    data = json_post(url, {"text": text, "tone": "blog", "language": "en"}, {"Authorization": f"Bearer {key}"})
    rewritten = first_text(data, ("text", "result", "output", "humanized"))
    if not rewritten:
        return skipped("writehuman", f"Unexpected WriteHuman response keys: {list(data)[:8]}")
    return {"provider": "writehuman", "status": "ok", "rewrittenText": rewritten}


def humanize_stealthwriter(text: str) -> dict:
    key = os.environ.get("STEALTHWRITER_API_KEY")
    if not key:
        return skipped("stealthwriter", "STEALTHWRITER_API_KEY is not set")
    url = os.environ.get("STEALTHWRITER_API_URL", "https://stealthwriter.io/api/v1/humanize")
    data = json_post(url, {"text": text, "n": 1, "level": 2, "style": "casual"}, {"Authorization": f"Bearer {key}"})
    rewritten = first_text(data, ("text", "output", "result"))
    if not rewritten:
        return skipped("stealthwriter", f"Unexpected StealthWriter response keys: {list(data)[:8]}")
    return {"provider": "stealthwriter", "status": "ok", "rewrittenText": rewritten}


def humanize_quillbot(text: str) -> dict:
    email = os.environ.get("QUILLBOT_EMAIL")
    password = os.environ.get("QUILLBOT_PASSWORD")
    if not email or not password:
        return skipped("quillbot", "QUILLBOT_EMAIL and QUILLBOT_PASSWORD are required (own account, not Toolzbuy)")
    ensure_quillbot_runtime()
    try:
        from quillbot import QuillBot
        from quillbot.endpoints import ParaphraseMode
    except ImportError:
        return skipped("quillbot", "quillbot package not installed. pip install quillbot into the workspace .venv")
    bot = QuillBot(email=email, password=password)
    result = bot.paraphrase(text, mode=ParaphraseMode.HUMANIZER)
    rewritten = getattr(result, "text", None) or first_text(result if isinstance(result, dict) else {}, ("text",))
    if not rewritten:
        return skipped("quillbot", "QuillBot returned no text")
    return {"provider": "quillbot", "status": "ok", "rewrittenText": rewritten}


def humanize_manual(provider: str, text: str) -> dict:
    key = provider.split(":", 1)[1] if ":" in provider else provider
    meta = MANUAL_TOOLS.get(key)
    if not meta:
        return skipped(provider, f"Unknown manual tool '{key}'. Known: {', '.join(MANUAL_TOOLS)}")
    return {
        "provider": provider,
        "status": "manual",
        "instructions": (
            f"Paste the prose into {meta['label']} ({meta['url']}). {meta['hint']} "
            "Copy the result back unchanged except for voice. Do not humanize after links are inserted."
        ),
        "dashboardUrl": meta["url"],
        "text": text,
    }


def dispatch(provider: str, text: str) -> dict:
    if provider == "none":
        return {"provider": "none", "status": "ok", "rewrittenText": text}
    if provider == "llm":
        return {"provider": "llm", "status": "ok", "instructions": LLM_INSTRUCTIONS, "text": text}
    if provider.startswith("manual:") or provider in MANUAL_TOOLS:
        return humanize_manual(provider if provider.startswith("manual:") else f"manual:{provider}", text)
    handlers = {
        "smodin": humanize_smodin,
        "wordai": humanize_wordai,
        "spinrewriter": humanize_spinrewriter,
        "writehuman": humanize_writehuman,
        "stealthwriter": humanize_stealthwriter,
        "quillbot": humanize_quillbot,
    }
    handler = handlers.get(provider)
    if not handler:
        return skipped(provider, f"Unknown provider '{provider}'")
    try:
        return handler(text)
    except urllib.error.HTTPError as exc:
        return skipped(provider, f"HTTP {exc.code}: {exc.reason}")
    except Exception as exc:  # noqa: BLE001 — providers must not block the pipeline
        return skipped(provider, str(exc))


def main() -> int:
    apply_dotenv_to_os()
    raw = sys.stdin.read().strip()
    if not raw:
        print("Provide JSON on stdin.", file=sys.stderr)
        return 2
    data = json.loads(raw)
    provider = str(data.get("provider") or "llm").strip().lower()
    text = str(data.get("text") or "")
    if not text.strip() and provider not in {"none", "llm"}:
        print(json.dumps(skipped(provider, "text is required")))
        return 2
    print(json.dumps(dispatch(provider, text), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
