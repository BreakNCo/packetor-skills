#!/usr/bin/env python3
"""
Apollo phone reveal webhook receiver.

Runs on the ngrok machine. Apollo fires a POST callback here when a phone
reveal completes. Results are stored in a SQLite database (apollo_results.db
in the same directory) so they survive server restarts.

Endpoints:
  GET  /              → {"status":"ok"}  (health check)
  POST /              → receives Apollo callback, stores result keyed by person id
  GET  /result/<id>   → {"ready":true, "data":{...}} or {"ready":false}
  DELETE /result/<id> → clears a result after it's been consumed

Usage:
    python3 apollo_webhook_server.py [--port 9055] [--db ./apollo_results.db]
"""

import argparse
import json
import re
import sqlite3
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

DB_PATH: str = ""


def log(msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def init_db(path: str):
    con = sqlite3.connect(path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS results (
            person_id TEXT PRIMARY KEY,
            data      TEXT NOT NULL,
            stored_at TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()


def db_store(person_id: str, data: dict):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR REPLACE INTO results (person_id, data, stored_at) VALUES (?, ?, ?)",
        (person_id, json.dumps(data), datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
    )
    con.commit()
    con.close()


def db_get(person_id: str):
    con = sqlite3.connect(DB_PATH)
    row = con.execute("SELECT data FROM results WHERE person_id = ?", (person_id,)).fetchone()
    con.close()
    return json.loads(row[0]) if row else None


def db_delete(person_id: str):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM results WHERE person_id = ?", (person_id,))
    con.commit()
    con.close()


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
            data = db_get(person_id)
            if data is not None:
                self.send_json(200, {"ready": True, "data": data})
            else:
                self.send_json(200, {"ready": False})
            return

        self.send_json(404, {"error": "not found"})

    def do_DELETE(self):
        # Results are never deleted — they persist in SQLite across restarts.
        # Return 200 so pollers that still issue DELETEs don't break.
        self.send_json(200, {"deleted": False, "note": "results are persistent, DELETE is a no-op"})

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
                db_store(person_id, person)
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

            db_store(person_id, payload)

            phones = [
                pn.get("sanitized_number") or pn.get("number", "")
                for pn in (person.get("phone_numbers") or [])
            ]
            log(f"Stored result for {person_id} — phones: {phones or 'none'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9055)
    parser.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "apollo_results.db"))
    args = parser.parse_args()

    global DB_PATH
    DB_PATH = args.db

    init_db(DB_PATH)
    log(f"Apollo webhook server on 0.0.0.0:{args.port} (db: {DB_PATH})")
    log("Endpoints: GET / (health)  POST / (callback)  GET /result/<id>  DELETE /result/<id>")
    log("Waiting for Apollo callbacks...")

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Stopped.")


if __name__ == "__main__":
    main()
