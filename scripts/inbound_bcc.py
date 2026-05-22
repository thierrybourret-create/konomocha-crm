#!/usr/bin/env python3
"""inbound_bcc.py — Postfix pipe: parse raw email, POST to CRM inbound endpoint.
Runs as mail is delivered to bcc@crm.konomocha.com.
Exit 75 (EX_TEMPFAIL) on transient errors so Postfix retries.
"""
import sys, json, email as _email, email.utils, email.header
import urllib.request, urllib.error
from datetime import datetime, timezone

SECRET = 'e7038dae70931811874e2f8c5335b3717c99ce205f7796e29e4ed3113aea3bc8'
API    = 'http://localhost:8002/crm-staging/api/emails/inbound'

def decode_header(value):
    if not value:
        return ''
    parts = email.header.decode_header(value)
    decoded = []
    for b, charset in parts:
        if isinstance(b, bytes):
            decoded.append(b.decode(charset or 'utf-8', errors='replace'))
        else:
            decoded.append(b)
    return ' '.join(decoded)

def extract_body(msg, max_chars=500):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or 'utf-8', errors='replace')[:max_chars]
                except Exception:
                    pass
        return ''
    try:
        return msg.get_payload(decode=True).decode(
            msg.get_content_charset() or 'utf-8', errors='replace')[:max_chars]
    except Exception:
        return ''

raw = sys.stdin.buffer.read()
msg = _email.message_from_bytes(raw)

from_addr = email.utils.parseaddr(msg.get('From', ''))[1]
to_addr   = email.utils.parseaddr(msg.get('To',   ''))[1]
subject   = decode_header(msg.get('Subject', ''))
date_raw  = msg.get('Date', '')

try:
    sent_at = email.utils.parsedate_to_datetime(date_raw).isoformat()
except Exception:
    sent_at = datetime.now(timezone.utc).isoformat()

body = extract_body(msg)

payload = json.dumps({
    'direction':    'outbound',
    'from_address': from_addr or None,
    'to_address':   to_addr   or None,
    'subject':      subject   or None,
    'body_snippet': body      or None,
    'sent_at':      sent_at,
}).encode()

req = urllib.request.Request(
    API,
    data=payload,
    headers={'Content-Type': 'application/json', 'X-Inbound-Token': SECRET},
)
try:
    urllib.request.urlopen(req, timeout=15)
except urllib.error.URLError as exc:
    sys.stderr.write(f'CRM inbound failed: {exc}\n')
    sys.exit(75)   # EX_TEMPFAIL — Postfix will retry
