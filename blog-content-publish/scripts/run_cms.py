#!/usr/bin/env python3
"""Run vendored cms-tools Bun scripts with env loaded from packetor-skills/.env.

Usage:
  printf '%s' '<json>' | python3 scripts/run_cms.py score
  printf '%s' '<json>' | python3 scripts/run_cms.py draft
  python3 scripts/run_cms.py link-targets

Stdin JSON is forwarded to score/draft. link-targets takes no stdin.
Stdout is the Bun script JSON (banner lines from `bun run` are stripped when present).
"""

from __future__ import annotations

import json
import subprocess
import sys

from cms_env import (
    cms_env_status,
    cms_tools_dir,
    cms_tools_installed,
    extract_json,
    missing_cms_env_hint,
    subprocess_env,
)

COMMANDS = {
    "score": ["bun", "run", "cms:score"],
    "draft": ["bun", "run", "cms:draft"],
    "link-targets": ["bun", "run", "cms:link-targets"],
}

NEEDS_DB = {"draft", "link-targets"}


def preflight(command: str) -> dict[str, str]:
    tools = cms_tools_dir()
    if not tools.exists():
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "CMS_TOOLS_MISSING",
                    "hint": f"Expected vendored CLI at {tools}",
                }
            )
        )
        raise SystemExit(1)
    if not cms_tools_installed():
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "CMS_TOOLS_NOT_INSTALLED",
                    "hint": "Run `cd blog-content-publish/cms-tools && bun install` once.",
                }
            )
        )
        raise SystemExit(1)

    env = subprocess_env()
    if command in NEEDS_DB and (not env.get("DATABASE_URI") or not env.get("PAYLOAD_SECRET")):
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "CMS_ENV_MISSING",
                    "hint": missing_cms_env_hint(),
                    "status": cms_env_status(),
                },
                indent=2,
            )
        )
        raise SystemExit(1)
    return env


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print("Usage: run_cms.py score|draft|link-targets", file=sys.stderr)
        return 2

    command = sys.argv[1]
    env = preflight(command)
    stdin_data = None if command == "link-targets" else sys.stdin.read()

    try:
        proc = subprocess.run(
            COMMANDS[command],
            cwd=str(cms_tools_dir()),
            input=stdin_data,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
    except FileNotFoundError:
        print(json.dumps({"ok": False, "error": "BUN_NOT_FOUND", "hint": "Install bun"}))
        return 1

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode != 0:
        detail = stdout or stderr
        try:
            parsed = extract_json(detail)
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "CMS_COMMAND_FAILED",
                        "command": command,
                        "detail": detail,
                        "stderr": stderr,
                    },
                    indent=2,
                )
            )
        return proc.returncode or 1

    try:
        parsed = extract_json(stdout)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        if stdout:
            print(stdout)
        elif stderr:
            print(stderr, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
