"""SavvyPay wallet model — ledger-backed financial accounts for users/merchants.

IMPORTANT: Wallet balances are NEVER stored. They are computed from ledger entries.
This table provides wallet metadata and links to ledger accounts.
"""

import uuid
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PayWallet(BaseMixin, OrgMixin, Base):
    """A user/merchant wallet — links to ledger accounts for balance computation."""

    __tablename__ = "pay_wallets"

    owner_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    wallet_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    # user, merchant, platform
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    # Links to ledger accounts
    available_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pay_accounts.id", ondelete="RESTRICT"), nullable=False)
    pending_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pay_accounts.id", ondelete="RESTRICT"), nullable=False)
    reserved_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pay_accounts.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
