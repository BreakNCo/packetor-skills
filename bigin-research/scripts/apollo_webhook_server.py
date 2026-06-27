#!/usr/bin/env python3
"""
Apollo phone reveal webhook receiver.

Runs on the ngrok machine. Apollo fires a POST callback here when a phone
reveal completes. Results are stored in memory and exposed via GET /result/<id>
so the poller on the work machine can fetch them over the ngrok URL.

Endpoints:
  GET  /              → {"status":"ok"}  (health check)
  POST /              → receives Apollo callback, stores result keyed by person id
  GET  /result/<id>   → {"ready":true, "data":{...}} or {"ready":false}
  DELETE /result/<id> → clears a result after it's been consumed

Usage:
    python3 apollo_webhook_server.py [--port 9055]
"""

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

# In-memory store: person_id -> payload dict
results: dict = {}


def log(msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default access log

    def send_json(self, code: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.send_json(200, {"status": "ok"})
            return

        m = re.match(r"^/result/([^/]+)$", self.path)
        if m:
            person_id = m.group(1)
            if person_id in results:
                self.send_json(200, {"ready": True, "data": results[person_id]})
            else:
                self.send_json(200, {"ready": False})
            return

        self.send_json(404, {"error": "not found"})

    def do_DELETE(self):
        m = re.match(r"^/result/([^/]+)$", self.path)
        if m:
            person_id = m.group(1)
            results.pop(person_id, None)
            self.send_json(200, {"deleted": True})
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""

        # Always acknowledge immediately so Apollo doesn't retry
        self.send_json(200, {"received": True})

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            log(f"Bad JSON: {body[:200]}")
            return

        # Apollo phone-reveal webhooks send {"people": [...]} (array at top level).
        # Legacy single-person payloads use {"person": {...}} or flat {"id": ...}.
        people_list = payload.get("people")
        if people_list and isinstance(people_list, list):
            # Phone-reveal batch callback — store each person separately
            for person in people_list:
                person_id = person.get("id")
                if not person_id:
                    log("No id in people[i] — skipping entry")
                    continue
                results[person_id] = person
                phones = [
                    pn.get("sanitized_number") or pn.get("number", "")
                    for pn in (person.get("phone_numbers") or [])
                ]
                log(f"Stored result for {person_id} — phones: {phones or 'none'}")
        else:
            # Legacy single-person payload
            person = payload.get("person") or payload
            person_id = person.get("id") or payload.get("id")

            if not person_id:
                log("No person id in payload — discarding")
                return

            results[person_id] = payload

            phones = [
                pn.get("sanitized_number") or pn.get("number", "")
                for pn in (person.get("phone_numbers") or [])
            ]
            log(f"Stored result for {person_id} — phones: {phones or 'none'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9055)
    args = parser.parse_args()

    log(f"Apollo webhook server on 0.0.0.0:{args.port}")
    log("Endpoints: GET / (health)  POST / (callback)  GET /result/<id>  DELETE /result/<id>")
    log("Waiting for Apollo callbacks...")

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Stopped.")


if __name__ == "__main__":
    main()
