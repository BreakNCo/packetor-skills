#!/usr/bin/env python3
"""
Apollo async phone reveal — trigger + poll via ngrok webhook server.

Flow:
  1. Trigger Apollo /people/match with reveal_phone_number=true and webhook_url=<ngrok>/
  2. Apollo sends the enriched payload to the webhook server (running on the ngrok machine)
  3. Webhook server stores the result in memory, exposes it at GET <ngrok>/result/<person_id>
  4. This script polls that endpoint until the result is ready, then prints it as JSON

Output JSON (printed to stdout):
  {
    "id": "<apollo_person_id>",
    "email": "work@company.com",
    "personal_emails": ["personal@gmail.com"],
    "phone_numbers": [{"sanitized_number": "+911234567890", "type": "mobile"}],
    "primary_phone": "+911234567890",
    "source": "webhook" | "sync" | "timeout"
  }

Usage:
    python3 apollo_phone_reveal.py \
        --api-key  <APOLLO_API_KEY> \
        --webhook-url  https://abc123.ngrok-free.app \
        --person-id  <apollo_id_from_phase1_search> \
        [--first-name John] \
        [--organization "Acme Corp"] \
        [--timeout 60] \
        [--poll-interval 3]
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

APOLLO_BASE = "https://api.apollo.io/api/v1"


def apollo_post(path: str, payload: dict, api_key: str) -> dict:
    url = f"{APOLLO_BASE}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "x-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def http_get(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def http_delete(url: str):
    try:
        req = urllib.request.Request(url, method="DELETE")
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception:
        pass


def extract_phones(person: dict) -> list[dict]:
    return person.get("phone_numbers") or []


def extract_primary_phone(person: dict) -> str:
    org = person.get("organization") or {}
    pp = org.get("primary_phone") or {}
    return pp.get("sanitized_number") or pp.get("number") or org.get("phone") or ""


def build_result(person: dict, source: str) -> dict:
    return {
        "id": person.get("id", ""),
        "email": person.get("email") or "",
        "personal_emails": person.get("personal_emails") or [],
        "phone_numbers": extract_phones(person),
        "primary_phone": extract_primary_phone(person),
        "source": source,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--webhook-url", required=True,
                        help="ngrok public URL, e.g. https://abc123.ngrok-free.app")
    parser.add_argument("--person-id", required=True)
    parser.add_argument("--first-name", default="")
    parser.add_argument("--organization", default="")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--poll-interval", type=int, default=3)
    args = parser.parse_args()

    webhook_base = args.webhook_url.rstrip("/")

    # Clean up any stale result from a previous run
    http_delete(f"{webhook_base}/result/{args.person_id}")

    # Build the Apollo request payload
    payload = {
        "id": args.person_id,
        "reveal_personal_emails": True,
        "reveal_phone_number": True,
        "webhook_url": webhook_base + "/",
    }
    if args.first_name:
        payload["first_name"] = args.first_name
    if args.organization:
        payload["organization_name"] = args.organization

    # Trigger the reveal call
    try:
        response = apollo_post("/people/match", payload, args.api_key)
    except Exception as e:
        print(json.dumps({"error": str(e), "id": args.person_id}))
        sys.exit(1)

    # Apollo sometimes returns phones synchronously (cached result)
    person = response.get("person") or {}
    if extract_phones(person):
        print(json.dumps(build_result(person, "sync")))
        return

    # Poll the webhook server's /result/<id> endpoint
    result_url = f"{webhook_base}/result/{args.person_id}"
    deadline = time.time() + args.timeout

    while time.time() < deadline:
        data = http_get(result_url)
        if data and data.get("ready"):
            payload_received = data["data"]
            person2 = payload_received.get("person") or payload_received
            # Clean up the stored result
            http_delete(result_url)
            print(json.dumps(build_result(person2, "webhook")))
            return
        time.sleep(args.poll_interval)

    # Timed out — return what we have (email + org phone, no personal phone)
    result = build_result(person, "timeout")
    result["error"] = f"webhook did not fire within {args.timeout}s"
    print(json.dumps(result))


if __name__ == "__main__":
    main()
