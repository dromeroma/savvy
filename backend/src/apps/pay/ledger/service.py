"""LedgerEngine — The financial core of SavvyPay.

All financial state is derived from this ledger.
No balance is ever stored directly — it is always computed from entries.

CRITICAL INVARIANTS:
1. For any journal_id: SUM(debits) == SUM(credits)
2. Entries are NEVER modified or deleted
3. All operations use idempotency keys to prevent duplicates
"""

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, ValidationError
from src.apps.pay.ledger.models import PayAccount, PayEvent, PayIdempotencyKey, PayLedgerEntry
from src.apps.pay.ledger.schemas import AccountCreate, JournalCreate, AccountBalanceResponse


def _d(val) -> Decimal:
    return Decimal(str(val)) if val else Decimal("0")


class LedgerEngine:
    """The single source of truth for all financial operations."""

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    @staticmethod
    async def create_account(db: AsyncSession, org_id: uuid.UUID, data: AccountCreate) -> PayAccount:
        account = PayAccount(organization_id=org_id, **data.model_dump())
        db.add(account)
        await db.flush()
        await db.refresh(account)
        return account

    @staticmethod
    async def list_accounts(db: AsyncSession, org_id: uuid.UUID) -> list[PayAccount]:
        result = await db.execute(
            select(PayAccount).where(PayAccount.organization_id == org_id)
            .order_by(PayAccount.account_type, PayAccount.code)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_account(db: AsyncSession, org_id: uuid.UUID, account_id: uuid.UUID) -> PayAccount:
        from src.core.exceptions import NotFoundError
        result = await db.execute(
            select(PayAccount).where(PayAccount.id == account_id, PayAccount.organization_id == org_id)
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise NotFoundError("Account not found.")
        return account

    # ------------------------------------------------------------------
    # Balance (derived from ledger — NEVER stored)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_balance(db: AsyncSession, account_id: uuid.UUID) -> Decimal:
        """Compute balance from ledger entries. debits - credits for asset accounts."""
        debit_result = await db.execute(
            select(func.coalesce(func.sum(PayLedgerEntry.amount), 0))
            .where(PayLedgerEntry.account_id == account_id, PayLedgerEntry.entry_type == "debit")
        )
        credit_result = await db.execute(
            select(func.coalesce(func.sum(PayLedgerEntry.amount), 0))
            .where(PayLedgerEntry.account_id == account_id, PayLedgerEntry.entry_type == "credit")
        )
        debits = _d(debit_result.scalar())
        credits = _d(credit_result.scalar())
        return debits - credits

    @staticmethod
    async def get_all_balances(db: AsyncSession, org_id: uuid.UUID) -> list[AccountBalanceResponse]:
        accounts = await LedgerEngine.list_accounts(db, org_id)
        balances = []
        for account in accounts:
            balance = await LedgerEngine.get_balance(db, account.id)
            balances.append(AccountBalanceResponse(
                account_id=account.id, code=account.code, name=account.name,
                account_type=account.account_type, currency=account.currency,
                balance=float(balance),
            ))
        return balances

    # ------------------------------------------------------------------
    # Journal Entries (the core write operation)
    # ------------------------------------------------------------------

    @staticmethod
    async def post_journal(
        db: AsyncSession, org_id: uuid.UUID, data: JournalCreate,
        actor_id: uuid.UUID | None = None,
    ) -> list[PayLedgerEntry]:
        """Post a balanced journal entry to the ledger.

        CRITICAL: Validates that SUM(debits) == SUM(credits) before posting.
        """
        # 1. Check idempotency
        if data.idempotency_key:
            existing = await db.execute(
                select(PayIdempotencyKey).where(PayIdempotencyKey.key == data.idempotency_key)
            )
            if existing.scalar_one_or_none():
                raise ConflictError("Duplicate operation: idempotency key already used.")

        # 2. Validate balance: SUM(debits) == SUM(credits)
        total_debit = sum(_d(line.amount) for line in data.lines if line.entry_type == "debit")
        total_credit = sum(_d(line.amount) for line in data.lines if line.entry_type == "credit")

        if abs(total_debit - total_credit) > Decimal("0.01"):
            raise ValidationError(
                f"Journal is not balanced: debits={total_debit}, credits={total_credit}"
            )

        # 3. Generate journal_id (groups all entries in this journal)
        journal_id = uuid.uuid4()

        # 4. Create ledger entries (IMMUTABLE)
        entries = []
        for line in data.lines:
            entry = PayLedgerEntry(
                organization_id=org_id,
                journal_id=journal_id,
                account_id=line.account_id,
                entry_type=line.entry_type,
                amount=line.amount,
                description=line.description or data.description,
                transaction_id=data.transaction_id,
                source_app=data.source_app,
                source_ref_type=data.source_ref_type,
                source_ref_id=data.source_ref_id,
                actor_id=actor_id,
                idempotency_key=data.idempotency_key,
            )
            db.add(entry)
            entries.append(entry)

        # 5. Record idempotency key
        if data.idempotency_key:
            idem = PayIdempotencyKey(
                key=data.idempotency_key,
                organization_id=org_id,
                entity_type="journal",
                entity_id=journal_id,
            )
            db.add(idem)

        await db.flush()
        for entry in entries:
            await db.refresh(entry)
        return entries

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    @staticmethod
    async def emit_event(
        db: AsyncSession, org_id: uuid.UUID,
        event_type: str, entity_type: str, entity_id: uuid.UUID,
        data: dict, actor_id: uuid.UUID | None = None,
        source_app: str | None = None,
    ) -> PayEvent:
        event = PayEvent(
            organization_id=org_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            actor_id=actor_id,
            source_app=source_app,
        )
        db.add(event)
        await db.flush()
        await db.refresh(event)
        return event

    @staticmethod
    async def list_events(
        db: AsyncSession, org_id: uuid.UUID, entity_type: str | None = None,
        entity_id: uuid.UUID | None = None, limit: int = 50,
    ) -> list[PayEvent]:
        q = select(PayEvent).where(PayEvent.organization_id == org_id)
        if entity_type:
            q = q.where(PayEvent.entity_type == entity_type)
        if entity_id:
            q = q.where(PayEvent.entity_id == entity_id)
        q = q.order_by(PayEvent.created_at.desc()).limit(limit)
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def list_ledger_entries(
        db: AsyncSession, org_id: uuid.UUID, account_id: uuid.UUID | None = None,
        journal_id: uuid.UUID | None = None, limit: int = 100,
    ) -> list[PayLedgerEntry]:
        q = select(PayLedgerEntry).where(PayLedgerEntry.organization_id == org_id)
        if account_id:
            q = q.where(PayLedgerEntry.account_id == account_id)
        if journal_id:
            q = q.where(PayLedgerEntry.journal_id == journal_id)
        q = q.order_by(PayLedgerEntry.posted_at.desc()).limit(limit)
        return list((await db.execute(q)).scalars().all())
