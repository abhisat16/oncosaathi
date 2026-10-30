"""WhatsApp channel (Twilio WhatsApp Sandbox): the plumbing. The conversation itself is handled in server.py with the
same brain as the web chat, so answers still come only from hospital.json.

    phone -> Twilio -> POST /whatsapp/twilio (form) -> we return empty TwiML at once, then in the background:
      voice note (audio/ogg) -> saaras:v4 STT -> brain.respond() -> text reply  + bulbul TTS as Ogg/Opus voice note
      -> Twilio REST API (Messages.json); the voice note is served from /wa/audio/<id>.ogg for ~30 min, in memory only.

.env (never printed): TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM (sandbox: whatsapp:+14155238886),
optional PUBLIC_URL (else the SHARE=1 gradio.live link is used). Every webhook must carry a valid X-Twilio-Signature.

Moving to Meta WhatsApp Cloud API later (same brain, only this file changes):
  - webhook: GET verify (hub.mode / hub.verify_token / hub.challenge) + POST JSON (entry[].changes[].value.messages[]);
    verify X-Hub-Signature-256 (HMAC-SHA256 of the raw body with the app secret) instead of X-Twilio-Signature.
  - incoming media: GET graph.facebook.com/<media_id> -> url, then download with the Bearer token.
  - replies: POST graph.facebook.com/v21.0/<WHATSAPP_PHONE_NUMBER_ID>/messages; upload the Ogg/Opus to /media first and
    send {"type": "audio", "audio": {"id": ...}} (no public audio URL needed). reminders.py already uses this API.
  - outside the 24-hour customer-care window only approved templates may be sent (reminders.py's utility template).
"""
import base64
import hashlib
import hmac
import os
import secrets
import time
from urllib.parse import urlparse

import httpx

PUBLIC_URL = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")     # set by server.py from the share link if empty
AUDIO_TTL_S = 1800
_audio = {}                                                           # id -> (ogg bytes, expires); never written to disk


def _env(k, default=""):
    return os.environ.get(k, default).strip()


def ready():
    return bool(_env("TWILIO_ACCOUNT_SID") and _env("TWILIO_AUTH_TOKEN"))


def public_base():
    return PUBLIC_URL


def valid_signature(url, params, signature):
    """Twilio's scheme: base64(HMAC-SHA1(auth_token, url + each POST key+value sorted by key))."""
    token = _env("TWILIO_AUTH_TOKEN")
    if not token or not signature:
        return False
    s = url + "".join(k + params[k] for k in sorted(params))
    mac = base64.b64encode(hmac.new(token.encode(), s.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(mac, signature)


async def fetch_media(url):
    """Download an incoming attachment. Only Twilio's own media host is accepted (no fetching arbitrary URLs)."""
    if urlparse(url).hostname != "api.twilio.com":
        raise ValueError("unexpected media host")
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        r = await c.get(url, auth=(_env("TWILIO_ACCOUNT_SID"), _env("TWILIO_AUTH_TOKEN")))
    r.raise_for_status()
    return r.content


async def send(to, body=None, media_url=None):
    """Send one WhatsApp message via Twilio. Returns the message SID, or an error string (never raises)."""
    sid = _env("TWILIO_ACCOUNT_SID")
    data = {"From": _env("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"), "To": to}
    if body:
        data["Body"] = body[:1550]
    if media_url:
        data["MediaUrl"] = media_url
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data=data,
                             auth=(sid, _env("TWILIO_AUTH_TOKEN")))
        return r.json().get("sid", "") if r.status_code < 300 else f"error {r.status_code}: {r.text[:160]}"
    except Exception as e:
        return f"error {e!r}"


def put_audio(ogg):
    now = time.time()
    for k in [k for k, (_, exp) in _audio.items() if exp < now]:
        _audio.pop(k, None)
    aid = secrets.token_urlsafe(18)
    _audio[aid] = (ogg, now + AUDIO_TTL_S)
    return aid


def get_audio(aid):
    item = _audio.get(aid)
    return item[0] if item and item[1] > time.time() else None


def mask(phone):
    return "…" + phone[-2:] if phone and len(phone) > 6 else "?"
