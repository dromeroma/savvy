"""Business logic for SavvyPay wallets — ledger-backed balances."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError, ValidationError
from src.apps.pay.wallets.models import PayWallet
from src.apps.pay.wallets.schemas import WalletBalanceResponse, WalletCreate, WalletFund, WalletTransfer
from src.apps.pay.ledger.service import LedgerEngine
from src.apps.pay.ledger.schemas import AccountCreate, JournalCreate, LedgerEntryLine


class WalletService:

    @staticmethod
    async def create_wallet(db: AsyncSession, org_id: uuid.UUID, data: WalletCreate) -> PayWallet:
        """Create a wallet with 3 backing ledger accounts (available, pending, reserved)."""
        prefix = f"W-{uuid.uuid4().hex[:8]}"

        available = await LedgerEngine.create_account(db, org_id, AccountCreate(
            code=f"{prefix}-avail", name=f"Wallet Available ({data.wallet_type})",
            account_type="user_wallet", currency=data.currency, owner_person_id=data.owner_person_id))
        pending = await LedgerEngine.create_account(db, org_id, AccountCreate(
            code=f"{prefix}-pend", name=f"Wallet Pending ({data.wallet_type})",
            account_type="user_pending", currency=data.currency, owner_person_id=data.owner_person_id))
        reserved = await LedgerEngine.create_account(db, org_id, AccountCreate(
            code=f"{prefix}-rsrv", name=f"Wallet Reserved ({data.wallet_type})",
            account_type="user_reserved", currency=data.currency, owner_person_id=data.owner_person_id))

        wallet = PayWallet(
            organization_id=org_id, owner_person_id=data.owner_person_id,
            wallet_type=data.wallet_type, currency=data.currency,
            available_account_id=available.id, pending_account_id=pending.id,
            reserved_account_id=reserved.id,
        )
        db.add(wallet)
        await db.flush()
        await db.refresh(wallet)

        await LedgerEngine.emit_event(db, org_id, "wallet.created", "wallet", wallet.id,
            {"wallet_type": data.wallet_type, "currency": data.currency})
        return wallet

    @staticmethod
    async def get_wallet(db: AsyncSession, org_id: uuid.UUID, wallet_id: uuid.UUID) -> PayWallet:
        result = await db.execute(select(PayWallet).where(PayWallet.id == wallet_id, PayWallet.organization_id == org_id))
        w = result.scalar_one_or_none()
        if w is None: raise NotFoundError("Wallet not found.")
        return w

    @staticmethod
    async def get_balance(db: AsyncSession, org_id: uuid.UUID, wallet_id: uuid.UUID) -> WalletBalanceResponse:
        w = await WalletService.get_wallet(db, org_id, wallet_id)
        available = float(await LedgerEngine.get_balance(db, w.available_account_id))
        pending = float(await LedgerEngine.get_balance(db, w.pending_account_id))
        reserved = float(await LedgerEngine.get_balance(db, w.reserved_account_id))
        return WalletBalanceResponse(
            wallet_id=w.id, wallet_type=w.wallet_type, currency=w.currency,
            available=available, pending=pending, reserved=reserved,
            total=available + pending + reserved,
        )

    @staticmethod
    async def list_wallets(db: AsyncSession, org_id: uuid.UUID) -> list[PayWallet]:
        return list((await db.execute(select(PayWallet).where(PayWallet.organization_id == org_id).order_by(PayWallet.created_at))).scalars().all())

    @staticmethod
    async def fund_wallet(db: AsyncSession, org_id: uuid.UUID, wallet_id: uuid.UUID, data: WalletFund) -> WalletBalanceResponse:
        """Add funds to a wallet (from external source)."""
        w = await WalletService.get_wallet(db, org_id, wallet_id)

        # Find or create external bank account
        from sqlalchemy import select as sel
        ext_result = await db.execute(sel(PayWallet).limit(0))  # dummy
        # Use a platform clearing account as the source
        accounts = await LedgerEngine.list_accounts(db, org_id)
        clearing = next((a for a in accounts if a.account_type == "platform_clearing"), None)
        if clearing is None:
            clearing = await LedgerEngine.create_account(db, org_id, AccountCreate(
                code="PLATFORM-CLEARING", name="Platform Clearing", account_type="platform_clearing"))

        await LedgerEngine.post_journal(db, org_id, JournalCreate(
            lines=[
                LedgerEntryLine(account_id=w.available_account_id, entry_type="debit", amount=data.amount, description=data.description or "Wallet funded"),
                LedgerEntryLine(account_id=clearing.id, entry_type="credit", amount=data.amount, description=data.description or "Wallet funded"),
            ],
            idempotency_key=data.idempotency_key, source_app="pay",
        ))

        await LedgerEngine.emit_event(db, org_id, "wallet.funded", "wallet", wallet_id,
            {"amount": data.amount})
        return await WalletService.get_balance(db, org_id, wallet_id)

    @staticmethod
    async def transfer(db: AsyncSession, org_id: uuid.UUID, from_wallet_id: uuid.UUID, data: WalletTransfer) -> WalletBalanceResponse:
        """Transfer funds between wallets."""
        from_w = await WalletService.get_wallet(db, org_id, from_wallet_id)
        to_w = await WalletService.get_wallet(db, org_id, data.to_wallet_id)

        # Check available balance
        balance = float(await LedgerEngine.get_balance(db, from_w.available_account_id))
        if balance < data.amount:
            raise ValidationError(f"Insufficient funds: available={balance}, requested={data.amount}")

        await LedgerEngine.post_journal(db, org_id, JournalCreate(
            lines=[
                LedgerEntryLine(account_id=to_w.available_account_id, entry_type="debit", amount=data.amount, description=data.description or "Transfer received"),
                LedgerEntryLine(account_id=from_w.available_account_id, entry_type="credit", amount=data.amount, description=data.description or "Transfer sent"),
            ],
            idempotency_key=data.idempotency_key, source_app="pay",
        ))

        await LedgerEngine.emit_event(db, org_id, "wallet.transfer", "wallet", from_wallet_id,
            {"to_wallet": str(data.to_wallet_id), "amount": data.amount})
        return await WalletService.get_balance(db, org_id, from_wallet_id)
