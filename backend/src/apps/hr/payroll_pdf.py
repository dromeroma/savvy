"""Generador de PDF del desprendible de pago."""

from __future__ import annotations

import io
import uuid
from datetime import datetime

from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from xhtml2pdf import pisa

from src.apps.hr.models import HrPayroll, HrPayrollItem, HrPayrollPeriod
from src.modules.organization.models import Organization


PAYROLL_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  @page { size: letter; margin: 1.5cm; }
  body { font-family: Helvetica, sans-serif; color: #1f2937; font-size: 10pt; }
  h1 { font-size: 14pt; margin: 0 0 4px; }
  .org { font-size: 9pt; color: #6b7280; margin-bottom: 12px; }
  .header { display: table; width: 100%; margin-bottom: 16px; }
  .header-left, .header-right { display: table-cell; vertical-align: top; }
  .header-right { text-align: right; }
  .meta { background: #f3f4f6; padding: 8px 12px; border-radius: 4px; margin-bottom: 12px; font-size: 9pt; }
  .meta-row { display: table; width: 100%; }
  .meta-cell { display: table-cell; padding: 2px 8px 2px 0; }
  table.items { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 9pt; }
  table.items th { background: #e5e7eb; color: #374151; text-align: left; padding: 6px; font-size: 8pt; text-transform: uppercase; }
  table.items td { padding: 5px 6px; border-bottom: 1px solid #e5e7eb; }
  .right { text-align: right; }
  .mono { font-family: monospace; }
  .section-title { font-size: 10pt; font-weight: bold; margin-top: 16px; margin-bottom: 6px; color: #374151; border-bottom: 2px solid #d1d5db; padding-bottom: 4px; }
  .totals { background: #f9fafb; padding: 12px; border-radius: 4px; margin-top: 18px; font-size: 10pt; }
  .totals-row { display: table; width: 100%; padding: 3px 0; }
  .totals-label { display: table-cell; }
  .totals-value { display: table-cell; text-align: right; font-family: monospace; }
  .net { font-size: 14pt; font-weight: bold; color: #059669; margin-top: 8px; padding-top: 8px; border-top: 2px solid #d1d5db; }
  .footer { margin-top: 28px; font-size: 8pt; color: #9ca3af; text-align: center; }
</style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      <h1>{{ org.name }}</h1>
      <div class="org">Desprendible de Pago</div>
    </div>
    <div class="header-right">
      <div style="font-size: 9pt; color: #6b7280;">Período</div>
      <div class="mono" style="font-size: 12pt;">{{ period.code }}</div>
      <div style="font-size: 8pt; color: #9ca3af;">{{ period.start_date }} → {{ period.end_date }}</div>
    </div>
  </div>

  <div class="meta">
    <div class="meta-row">
      <div class="meta-cell"><strong>Empleado:</strong> {{ payroll.employee_name }}</div>
      <div class="meta-cell"><strong>Código:</strong> {{ payroll.employee_code }}</div>
    </div>
    <div class="meta-row">
      <div class="meta-cell"><strong>Departamento:</strong> {{ payroll.department_name or '—' }}</div>
      <div class="meta-cell"><strong>Cargo:</strong> {{ payroll.position_name or '—' }}</div>
    </div>
    <div class="meta-row">
      <div class="meta-cell"><strong>Días laborados:</strong> {{ payroll.worked_days }}</div>
      <div class="meta-cell"><strong>Salario base:</strong> $ {{ fmt(payroll.base_salary) }}</div>
    </div>
  </div>

  {% if earnings %}
  <div class="section-title">Devengados</div>
  <table class="items">
    <thead>
      <tr><th>Concepto</th><th class="right">Cantidad</th><th class="right">Base</th><th class="right">%</th><th class="right">Valor</th></tr>
    </thead>
    <tbody>
    {% for it in earnings %}
      <tr>
        <td>{{ it.concept_name }} <span style="color:#9ca3af; font-family: monospace; font-size: 8pt;">[{{ it.concept_code }}]</span></td>
        <td class="right mono">{{ it.quantity or '' }}</td>
        <td class="right mono">{{ fmt(it.base_amount) if it.base_amount else '' }}</td>
        <td class="right mono">{{ it.percentage or '' }}</td>
        <td class="right mono">$ {{ fmt(it.amount) }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% endif %}

  {% if deductions %}
  <div class="section-title">Deducciones</div>
  <table class="items">
    <thead>
      <tr><th>Concepto</th><th class="right">Base</th><th class="right">%</th><th class="right">Valor</th></tr>
    </thead>
    <tbody>
    {% for it in deductions %}
      <tr>
        <td>{{ it.concept_name }} <span style="color:#9ca3af; font-family: monospace; font-size: 8pt;">[{{ it.concept_code }}]</span></td>
        <td class="right mono">{{ fmt(it.base_amount) if it.base_amount else '' }}</td>
        <td class="right mono">{{ it.percentage or '' }}</td>
        <td class="right mono">$ {{ fmt(it.amount) }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% endif %}

  {% if benefits %}
  <div class="section-title">Prestaciones sociales (provisión)</div>
  <table class="items">
    <thead>
      <tr><th>Concepto</th><th class="right">%</th><th class="right">Valor</th></tr>
    </thead>
    <tbody>
    {% for it in benefits %}
      <tr>
        <td>{{ it.concept_name }}</td>
        <td class="right mono">{{ it.percentage or '' }}</td>
        <td class="right mono">$ {{ fmt(it.amount) }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% endif %}

  <div class="totals">
    <div class="totals-row">
      <div class="totals-label">Total devengado</div>
      <div class="totals-value">$ {{ fmt(payroll.total_earnings) }}</div>
    </div>
    <div class="totals-row">
      <div class="totals-label">Total deducciones</div>
      <div class="totals-value">($ {{ fmt(payroll.total_deductions) }})</div>
    </div>
    <div class="net totals-row">
      <div class="totals-label">NETO A PAGAR</div>
      <div class="totals-value">$ {{ fmt(payroll.net_amount) }}</div>
    </div>
  </div>

  <div class="footer">
    Generado el {{ today }} · {{ org.name }} · Sistema SavvyHR
  </div>
</body>
</html>
"""


def _fmt(n) -> str:
    if n is None:
        return "0"
    return f"{int(round(float(n))):,}".replace(",", ".")


async def render_payroll_pdf(
    db: AsyncSession,
    org_id: uuid.UUID,
    payroll: HrPayroll,
    items: list[HrPayrollItem],
    period: HrPayrollPeriod,
) -> tuple[bytes, str]:
    org = await db.scalar(select(Organization).where(Organization.id == org_id))

    earnings = [i for i in items if i.concept_type == "earning"]
    deductions = [i for i in items if i.concept_type == "deduction"]
    benefits = [i for i in items if i.concept_type == "benefit"]

    template = Template(PAYROLL_HTML)
    html = template.render(
        org=org,
        period=period,
        payroll=payroll,
        earnings=earnings,
        deductions=deductions,
        benefits=benefits,
        fmt=_fmt,
        today=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    buf = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8")
    if pisa_status.err:
        raise RuntimeError(f"PDF failed ({pisa_status.err} errors)")
    filename = f"desprendible-{period.code}-{payroll.employee_code}.pdf"
    return buf.getvalue(), filename
