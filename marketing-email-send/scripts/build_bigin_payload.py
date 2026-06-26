#!/usr/bin/env python3
"""Build a ready-to-send Bigin sendEmails payload.

Input: JSON on stdin with resolved recipient/company/template/attachment details.
Output: JSON payload suitable for Bigin_sendEmails body.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass


@dataclass
class Input:
    recipient_email: str
    recipient_name: str
    subject: str
    body: str
    attachment_id: str
    from_email: str = "litti@packets.build"
    from_name: str = "Litti@packets"
    reply_to_email: str | None = None
    reply_to_name: str | None = None
    org_email: bool = True
    mail_format: str = "text"


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("Provide JSON on stdin.", file=sys.stderr)
        return 2
    data = Input(**json.loads(raw))
    payload = {
        "data": [
            {
                "subject": data.subject,
                "from": {
                    "email": data.from_email,
                    "user_name": data.from_name,
                },
                "to": [
                    {
                        "email": data.recipient_email,
                        "user_name": data.recipient_name,
                    }
                ],
                "content": data.body,
                "mail_format": data.mail_format,
                "org_email": data.org_email,
                "reply_to": {
                    "email": data.reply_to_email or data.from_email,
                    "user_name": data.reply_to_name or data.from_name,
                },
                "attachments": [
                    {"id": data.attachment_id}
                ],
            }
        ]
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
