"""SMTP email sender — env-based config, gracefully no-ops if not set up.

Configure via environment variables (all prefixed SAVVY_):
    SAVVY_SMTP_HOST       e.g. smtp.gmail.com
    SAVVY_SMTP_PORT       587 (TLS) or 465 (SSL)
    SAVVY_SMTP_USER       login user
    SAVVY_SMTP_PASSWORD   login password (or app password for Gmail)
    SAVVY_SMTP_FROM       "Acueducto Demo <no-reply@acueducto.com>"
    SAVVY_SMTP_TLS        "1" for STARTTLS (default), "0" to disable
    SAVVY_SMTP_SSL        "1" for SSL on connect (port 465 typically)

If SAVVY_SMTP_HOST is unset, every send call is a no-op (returns False)
and logs a single warning. This keeps demo deployments working without
needing email creds.
"""

from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger("savvycore.email")

_warned_unconfigured = False


def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def is_configured() -> bool:
    return bool(os.environ.get("SAVVY_SMTP_HOST"))


def _send_sync(to: str, subject: str, html: str, plain: str | None = None) -> None:
    """Blocking SMTP send. Caller schedules in a thread via run_in_executor."""
    host = os.environ["SAVVY_SMTP_HOST"]
    port = int(os.environ.get("SAVVY_SMTP_PORT", "587"))
    user = os.environ.get("SAVVY_SMTP_USER")
    password = os.environ.get("SAVVY_SMTP_PASSWORD")
    from_addr = os.environ.get("SAVVY_SMTP_FROM") or user or "no-reply@savvy.local"
    use_tls = _bool("SAVVY_SMTP_TLS", True)
    use_ssl = _bool("SAVVY_SMTP_SSL", False)

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = subject
    # Plain fallback so non-HTML clients still see something readable.
    msg.set_content(plain or "Tu cliente de correo no soporta HTML.")
    msg.add_alternative(html, subtype="html")

    cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with cls(host, port, timeout=15) as server:
        if use_tls and not use_ssl:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)


async def send_email(
    to: str | None,
    subject: str,
    html: str,
    plain: str | None = None,
) -> bool:
    """Schedule an SMTP send. Returns True on success, False on
    no-op (unconfigured) or failure (logged). Never raises — email must
    not break business flows like invoice generation.
    """
    global _warned_unconfigured

    if not to or not to.strip() or "@" not in to:
        return False
    if not is_configured():
        if not _warned_unconfigured:
            log.warning(
                "Email sending disabled — SAVVY_SMTP_HOST not set. "
                "Set it in env vars to enable outbound mail.",
            )
            _warned_unconfigured = True
        return False
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _send_sync, to, subject, html, plain)
        log.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as exc:
        # Don't propagate — the in-app notification was already saved.
        log.error("Failed to send email to %s: %s", to, exc)
        return False


# ----------------------------------------------------------------------
# Minimal branded template
# ----------------------------------------------------------------------

_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:24px 0;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;">
      <tr><td style="background:#0EA5E9;padding:18px 24px;color:#fff;font-size:15pt;font-weight:bold;">
        {org_name}
      </td></tr>
      <tr><td style="padding:24px;color:#222;font-size:11pt;line-height:1.55;">
        <h2 style="margin:0 0 12px 0;font-size:14pt;color:#0c4a6e;">{title}</h2>
        {body_html}
      </td></tr>
      <tr><td style="background:#f9fafb;padding:14px 24px;border-top:1px solid #e5e7eb;color:#777;font-size:9pt;">
        Este correo fue enviado por {org_name} a través de SavvyCore.
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""


def render_branded(org_name: str, title: str, body_html: str) -> str:
    """Wrap content in the basic branded template."""
    return _TEMPLATE.format(
        org_name=org_name or "Savvy",
        title=title,
        body_html=body_html,
    )
