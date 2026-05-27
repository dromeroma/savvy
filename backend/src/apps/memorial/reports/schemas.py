"""Schemas para reportes."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class IncomePoint(BaseModel):
    period: str  # YYYY-MM
    exequial_dues: Decimal
    service_income: Decimal
    total: Decimal


class IncomeReport(BaseModel):
    date_from: date
    date_to: date
    points: list[IncomePoint]
    total_dues: Decimal
    total_services: Decimal
    grand_total: Decimal


class ServiceTypeCount(BaseModel):
    service_type: str
    count: int
    total_revenue: Decimal


class ServicesByTypeReport(BaseModel):
    date_from: date
    date_to: date
    items: list[ServiceTypeCount]
    total_count: int
    total_revenue: Decimal


class PlanRankingItem(BaseModel):
    plan_id: uuid.UUID
    plan_code: str
    plan_name: str
    contracts_count: int
    active_count: int
    total_revenue: Decimal


class PlanRankingReport(BaseModel):
    items: list[PlanRankingItem]


class EmployeeRankingItem(BaseModel):
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    position_name: str | None = None
    days_present: int
    hours_worked: Decimal


class EmployeeRankingReport(BaseModel):
    date_from: date
    date_to: date
    items: list[EmployeeRankingItem]


class OperationalKpis(BaseModel):
    services_open: int
    services_in_progress: int
    services_closed_period: int
    avg_close_hours: float | None
    contracts_active: int
    contracts_overdue: int
    leads_open: int
    leads_won_period: int
    inventory_low_stock_items: int
