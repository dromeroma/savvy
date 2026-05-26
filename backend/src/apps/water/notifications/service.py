"""Notifications service — emit + read.

Side channels (email, future SMS/WhatsApp) are best-effort: the in-app
WaterNotification row is always saved. If email is configured via SAVVY_SMTP_*
env vars and the destination user has an email on their User record, an
HTML email mirrors the in-app notification. Failures are logged, never raised.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import WaterNotification
from src.apps.water.notifications.schemas import NotificationItem
from src.core.email import is_configured as _email_configured
from src.core.email import render_branded, send_email
from src.modules.auth.models import User
from src.modules.organization.models import Organization

log = logging.getLogger("savvycore.notifications")


class NotificationsService:

    # ------------------------------------------------------------------
    # Producer API — called from invoices/payments/pqrs/suspend hooks.
    # ------------------------------------------------------------------
    @staticmethod
    async def emit(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        type_: str,
        title: str,
        body: str | None = None,
        link: str | None = None,
        *,
        send_email_too: bool = True,
    ) -> WaterNotification:
        n = WaterNotification(
            organization_id=org_id, user_id=user_id,
            type=type_, title=title, body=body, link=link,
        )
        db.add(n)
        await db.flush()
        if send_email_too and _email_configured():
            await NotificationsService._fire_email(db, org_id, user_id, title, body)
        return n

    @staticmethod
    async def _fire_email(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        body: str | None,
    ) -> None:
        """Best-effort email mirror of an in-app notification."""
        try:
            user = await db.get(User, user_id)
            if user is None or not user.email:
                return
            org = await db.get(Organization, org_id)
            org_name = org.name if org else "Savvy"
            body_html = (
                f'<p>{(body or "").replace(chr(10), "<br>")}</p>'
                if body else ""
            )
            html = render_branded(org_name, title, body_html)
            plain = f"{title}\n\n{body or ''}".strip()
            await send_email(user.email, title, html, plain)
        except Exception as exc:
            log.error("Email mirror failed for user %s: %s", user_id, exc)

    @staticmethod
    async def emit_to_users(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_ids: list[uuid.UUID],
        type_: str,
        title: str,
        body: str | None = None,
        link: str | None = None,
        *,
        send_email_too: bool = True,
    ) -> int:
        """Fan-out helper — emit the same notification to multiple users."""
        if not user_ids:
            return 0
        for uid in user_ids:
            db.add(WaterNotification(
                organization_id=org_id, user_id=uid,
                type=type_, title=title, body=body, link=link,
            ))
        await db.flush()
        if send_email_too and _email_configured():
            for uid in user_ids:
                await NotificationsService._fire_email(db, org_id, uid, title, body)
        return len(user_ids)

    # ------------------------------------------------------------------
    # Consumer API — used by the inbox UI.
    # ------------------------------------------------------------------
    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[NotificationItem]:
        stmt = (
            select(WaterNotification)
            .where(
                WaterNotification.organization_id == org_id,
                WaterNotification.user_id == user_id,
            )
            .order_by(WaterNotification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(WaterNotification.read_at.is_(None))
        rows = await db.execute(stmt)
        return [NotificationItem.model_validate(n) for n in rows.scalars().all()]

    @staticmethod
    async def count_unread(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> int:
        n = await db.scalar(
            select(func.count(WaterNotification.id)).where(
                WaterNotification.organization_id == org_id,
                WaterNotification.user_id == user_id,
                WaterNotification.read_at.is_(None),
            )
        )
        return int(n or 0)

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        ids: list[uuid.UUID] | None = None,
    ) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(WaterNotification)
            .where(
                WaterNotification.organization_id == org_id,
                WaterNotification.user_id == user_id,
                WaterNotification.read_at.is_(None),
            )
            .values(read_at=now)
        )
        if ids:
            stmt = stmt.where(WaterNotification.id.in_(ids))
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount or 0
