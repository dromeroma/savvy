"""SavvyHealth service catalog."""

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class HealthService(BaseMixin, OrgMixin, Base):
    __tablename__ = "health_services"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="consultation")
    # consultation, procedure, lab, imaging, therapy, other
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    duration_minutes: Mapped[int] = mapped_column(default=30, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
