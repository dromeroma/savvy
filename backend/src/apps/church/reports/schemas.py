"""Pydantic schemas for church-specific reports."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category_name: str
    category_code: str
    total: Decimal


class MonthlySummaryResponse(BaseModel):
    """Consolidated monthly summary for a church."""

    year: int
    month: int
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    income_by_category: list[CategoryTotal]
    expenses_by_category: list[CategoryTotal]
    tithe_of_tithe: TitheOfTitheResponse | None = None


class TitheOfTitheResponse(BaseModel):
    """Tithe of tithe calculation: 10% of (tithes + offerings)."""

    total_tithes: Decimal
    total_offerings: Decimal
    base_amount: Decimal
    tithe_of_tithe: Decimal
