"""Analytics schemas for the executive dashboard."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class MonthlyPoint(BaseModel):
    month: str   # YYYY-MM
    amount: Decimal
    count: int = 0


class StratumStat(BaseModel):
    stratum: int | None
    subscribers: int
    avg_consumption_cubic: Decimal
    total_billed: Decimal


class NeighborhoodStat(BaseModel):
    neighborhood: str | None
    subscribers: int
    open_balance: Decimal


class TopDebtor(BaseModel):
    subscriber_id: str
    code: str
    name: str
    days_overdue: int
    balance: Decimal


class AnalyticsResponse(BaseModel):
    billed_trend: list[MonthlyPoint]       # last 12 months
    collected_trend: list[MonthlyPoint]    # last 12 months
    consumption_trend: list[MonthlyPoint]  # last 12 months — cubic
    by_stratum: list[StratumStat]
    by_neighborhood: list[NeighborhoodStat]
    top_debtors: list[TopDebtor]
    new_subscribers_last_30d: int
    avg_collection_per_day: Decimal
    collection_rate: Decimal   # paid_this_month / billed_this_month (0..1)
