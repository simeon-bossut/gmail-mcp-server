"""
Provides tools for common operations with Gmail (e.g., send_mail)
"""

import os
from base64 import urlsafe_b64encode
from typing import Any, Optional, Dict
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "gmail-mcp-server",
    instructions="Provides tools for common operations with Gmail (e.g., send_mail)",
)

def _b64url_decode(data_b64: str) -> bytes:
    # base64url decode with padding
    padded = data_b64 + "=" * ((4 - len(data_b64) % 4) % 4)
    return urlsafe_b64encode(b"").__class__(b"") if False else __import__('base64').urlsafe_b64decode(padded)

class GoogleClient:
    """Encapsulates a Gmail API client."""
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self._creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )
        self.gmail = build("gmail", "v1", credentials=self._creds, cache_discovery=False)

def get_google_client(env_override: Optional[Dict[str, str]] = None) -> GoogleClient:
    """
    Constructs a GoogleClient using parameters from env_override (if provided), else from environment variables.
    """
    source = env_override if env_override is not None else os.environ
    client_id = source.get("CLIENT_ID")
    client_secret = source.get("CLIENT_SECRET")
    refresh_token = source.get("REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        raise RuntimeError("Required Google OAuth credentials not found in environment or env_override parameter")
    return GoogleClient(client_id, client_secret, refresh_token)

@mcp.tool(name="send_mail", description="Send a new email to recipient(s) with a subject and body")
async def send_mail(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    env_override: Optional[Dict[str, str]] = None,
) -> dict[str, Any]:
    """
    Sends an email using Gmail API.

    :param to: Recipient email address.
    :param subject: Email subject.
    :param body: Email body (can include HTML).
    :param cc: CC recipients, comma-separated.
    :param bcc: BCC recipients, comma-separated.
    :param env_override: (optional) Per-request env dict for Google OAuth credentials.
    :returns: Dict with 'content' list or error flag.
    """
    try:
        # Build MIME message using EmailMessage to ensure proper UTF-8 encoding
        msg = EmailMessage()
        msg['To'] = to
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc
        msg['Subject'] = subject
        # Plain text body with utf-8 charset. If HTML is needed, use add_alternative.
        msg.set_content(body, subtype='plain', charset='utf-8')

        # as_bytes() will include proper headers and charset; encode to base64url without padding
        raw = urlsafe_b64encode(msg.as_bytes()).decode('ascii').rstrip('=')

        # get google client (from env_override or os.environ)
        google_client = get_google_client(env_override)

        # send via Gmail API
        sent = (
            google_client.gmail
            .users()
            .messages()
            .send(
                userId="me",
                body={"raw": raw},
            )
            .execute()
        )

        return {
            "content": [
                {"type": "text", "text": f"Email sent successfully. Message ID: {sent['id']}"}
            ]
        }
    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error sending email: {e}"}
            ],
            "isError": True,
        }



@mcp.tool(name="get_latest_message", description="Get the latest message from INBOX (subject, from, date, snippet, body)")
async def get_latest_message(env_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    client = get_google_client(env_override)
    gmail = client.gmail
    # list latest
    lst = gmail.users().messages().list(userId="me", maxResults=1, labelIds=["INBOX"]).execute()
    messages = lst.get("messages") or []
    if not messages:
        return {"found": False}
    msg_id = messages[0]["id"]
    msg = gmail.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})
    headers = {h.get("name"): h.get("value") for h in payload.get("headers", [])}
    subject = headers.get("Subject")
    from_hdr = headers.get("From")
    date_hdr = headers.get("Date")
    snippet = msg.get("snippet")

    # extract text/plain
    body = None
    parts = payload.get("parts")
    if parts:
        for p in parts:
            if p.get("mimeType") == "text/plain":
                data = p.get("body", {}).get("data")
                if data:
                    try:
                        raw = __import__('base64').urlsafe_b64decode(data + "=" * ((4 - len(data) % 4) % 4))
                        body = raw.decode("utf-8", errors="replace")
                        break
                    except Exception:
                        body = ""
    else:
        data = payload.get("body", {}).get("data")
        if data:
            try:
                raw = __import__('base64').urlsafe_b64decode(data + "=" * ((4 - len(data) % 4) % 4))
                body = raw.decode("utf-8", errors="replace")
            except Exception:
                body = ""

    return {
        "found": True,
        "id": msg_id,
        "subject": subject,
        "from": from_hdr,
        "date": date_hdr,
        "snippet": snippet,
        "body": body,
    }


@mcp.tool(name="list_labels", description="List Gmail labels for the account")
async def list_labels(env_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    client = get_google_client(env_override)
    gmail = client.gmail
    resp = gmail.users().labels().list(userId="me").execute()
    return resp


@mcp.tool(name="create_label", description="Create a Gmail label. Provide {'name': 'LabelName'}")
async def create_label(label: Dict[str, Any], env_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    client = get_google_client(env_override)
    gmail = client.gmail
    resp = gmail.users().labels().create(userId="me", body=label).execute()
    return resp


@mcp.tool(name="modify_message_labels", description="Modify labels on a message: {'addLabelIds': [...], 'removeLabelIds': [...]}")
async def modify_message_labels(message_id: str, mods: Dict[str, Any], env_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    client = get_google_client(env_override)
    gmail = client.gmail
    resp = gmail.users().messages().modify(userId="me", id=message_id, body=mods).execute()
    return resp


@mcp.tool(name="mark_read", description="Mark a message as read (remove UNREAD)")
async def mark_read(message_id: str, env_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    return await modify_message_labels(message_id, {"removeLabelIds": ["UNREAD"]}, env_override=env_override)


@mcp.tool(name="refresh_gmail_token", description="Ask backend to refresh the stored Gmail refresh_token for the current user")
async def refresh_gmail_token(env_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Calls the Paperslate API endpoint POST /api/connectors/gmail/refresh.

    env_override may contain:
      - BASE_API_URL: full base URL of the backend (e.g. https://api.example.com)
      - API_TOKEN: the user's API token to authenticate the request (sent as x-api-token header)
    If not provided, environment variables of the same names are used. Returns parsed JSON from backend.
    """
    source = env_override if env_override is not None else os.environ
    base = source.get("BASE_API_URL") or source.get("API_BASE_URL") or os.environ.get("BASE_API_URL") or "http://localhost:8000"
    api_token = source.get("API_TOKEN") or os.environ.get("API_TOKEN")
    if not api_token:
        return {"isError": True, "error": "Missing API_TOKEN in env_override or environment"}

    url = f"{base.rstrip('/')}/api/connectors/gmail/refresh"
    try:
        import requests as _requests
        resp = _requests.post(url, headers={"x-api-token": api_token}, timeout=20)
        try:
            data = resp.json()
        except Exception:
            return {"isError": True, "error": "Non-JSON response from backend", "body": resp.text}

        if resp.status_code >= 400:
            return {"isError": True, "status_code": resp.status_code, "details": data}

        return {"isError": False, "result": data}
    except Exception as e:
        return {"isError": True, "error": str(e)}

if __name__ == "__main__":
    mcp.run(transport=os.getenv("TRANSPORT", "stdio"))