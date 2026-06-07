"""Renderer de PDF para liquidaciones — 3 plantillas (formal, moderna, compacta)."""

from __future__ import annotations

import io
import uuid
from datetime import datetime

from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from xhtml2pdf import pisa

from src.apps.hr.models import (
    HrEmployee,
    HrDepartment,
    HrPosition,
    HrLiquidation,
    HrLiquidationItem,
    HrSettings,
)
from src.modules.organization.models import Organization


# ----------------------------------------------------- Plantilla FORMAL

FORMAL_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  @page { size: letter; margin: 1.5cm; }
  body { font-family: Helvetica, sans-serif; color: #1f2937; font-size: 10pt; }
  h1 { font-size: 15pt; margin: 0; }
  .header { display: table; width: 100%; border-bottom: 3px double {{ brand }}; padding-bottom: 12px; margin-bottom: 16px; }
  .header-left, .header-right { display: table-cell; vertical-align: top; }
  .header-right { text-align: right; }
  .logo { max-height: 60px; }
  .org-name { font-size: 13pt; font-weight: bold; color: {{ brand }}; }
  .org-meta { font-size: 8pt; color: #6b7280; margin-top: 4px; }
  .title { font-size: 14pt; font-weight: bold; text-align: center; text-transform: uppercase; margin: 16px 0 8px; color: {{ brand }}; letter-spacing: 1px; }
  .subtitle { text-align: center; font-size: 9pt; color: #6b7280; margin-bottom: 18px; }
  table.info { width: 100%; border-collapse: collapse; margin-bottom: 14px; }
  table.info td { padding: 5px 8px; border: 1px solid #e5e7eb; font-size: 9pt; }
  table.info td.label { background: #f9fafb; font-weight: bold; width: 22%; }
  table.items { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 9pt; }
  table.items th { background: {{ brand }}; color: white; padding: 6px; text-align: left; font-size: 8pt; text-transform: uppercase; }
  table.items td { padding: 6px; border-bottom: 1px solid #e5e7eb; }
  table.items .right { text-align: right; font-family: monospace; }
  .section-title { font-size: 11pt; font-weight: bold; margin-top: 18px; color: {{ brand }}; border-bottom: 1px solid {{ brand }}; padding-bottom: 3px; }
  .totals { margin-top: 18px; }
  .totals-row { display: table; width: 100%; padding: 4px 12px; }
  .totals-row.alt { background: #f9fafb; }
  .totals-label { display: table-cell; font-weight: bold; }
  .totals-value { display: table-cell; text-align: right; font-family: monospace; }
  .net { background: {{ brand }}; color: white; font-size: 13pt; font-weight: bold; padding: 12px; text-align: right; margin-top: 8px; }
  .notes { margin-top: 18px; padding: 10px; background: #fffbeb; border-left: 3px solid #f59e0b; font-size: 9pt; }
  .signature { margin-top: 50px; display: table; width: 100%; }
  .signature-cell { display: table-cell; text-align: center; padding: 0 20px; }
  .signature-line { border-top: 1px solid #6b7280; margin: 0 30px 4px; padding-top: 4px; font-size: 9pt; }
  .signature-img { max-height: 50px; margin-bottom: 4px; }
  .footer { margin-top: 30px; text-align: center; font-size: 7pt; color: #9ca3af; }
</style></head>
<body>
  <div class="header">
    <div class="header-left">
      {% if logo_url %}<img src="{{ logo_url }}" class="logo"/>{% endif %}
      <div class="org-name">{{ org_name }}</div>
      <div class="org-meta">{% if org_meta.address %}{{ org_meta.address }}{% endif %}{% if org_meta.city %} · {{ org_meta.city }}{% endif %}{% if org_meta.tax_id %} · NIT {{ org_meta.tax_id }}{% endif %}</div>
    </div>
    <div class="header-right">
      <div style="font-size: 8pt; color: #6b7280;">N° Liquidación</div>
      <div style="font-family: monospace; font-size: 13pt; font-weight: bold;">{{ liq.liquidation_number }}</div>
      <div style="font-size: 8pt; color: #9ca3af; margin-top: 4px;">Emitida {{ today }}</div>
    </div>
  </div>

  <div class="title">Liquidación Definitiva de Contrato Laboral</div>
  <div class="subtitle">{{ reason_label }}</div>

  <table class="info">
    <tr><td class="label">Trabajador</td><td>{{ emp.full_name }}</td><td class="label">Código</td><td>{{ emp.employee_code }}</td></tr>
    <tr><td class="label">Documento</td><td>{{ emp.document_type or '' }} {{ emp.document_number or '—' }}</td><td class="label">Cargo</td><td>{{ emp.position_name or '—' }}</td></tr>
    <tr><td class="label">Departamento</td><td>{{ emp.department_name or '—' }}</td><td class="label">Salario base</td><td class="right" style="font-family: monospace;">$ {{ fmt(liq.base_salary) }}</td></tr>
    <tr><td class="label">Fecha ingreso</td><td>{{ liq.contract_start_date }}</td><td class="label">Último día laborado</td><td>{{ liq.last_worked_date }}</td></tr>
    <tr><td class="label">Fecha terminación</td><td>{{ liq.termination_date }}</td><td class="label">Días totales</td><td>{{ liq.days_worked_total }}</td></tr>
  </table>

  <div class="section-title">Devengados</div>
  <table class="items">
    <thead><tr><th>Concepto</th><th class="right">Cantidad</th><th class="right">Base</th><th class="right">Tasa</th><th class="right">Valor</th></tr></thead>
    <tbody>
      {% for it in earnings %}
      <tr><td><strong>{{ it.concept_name }}</strong>{% if it.notes %}<br/><span style="color:#6b7280; font-size: 8pt;">{{ it.notes }}</span>{% endif %}</td>
          <td class="right">{{ it.quantity }}</td>
          <td class="right">{{ fmt(it.base_amount) }}</td>
          <td class="right">{% if it.rate %}{{ it.rate }}{% else %}—{% endif %}</td>
          <td class="right"><strong>$ {{ fmt(it.amount) }}</strong></td></tr>
      {% endfor %}
    </tbody>
  </table>

  {% if deductions %}
  <div class="section-title">Deducciones</div>
  <table class="items">
    <thead><tr><th>Concepto</th><th class="right">Valor</th></tr></thead>
    <tbody>
      {% for it in deductions %}
      <tr><td>{{ it.concept_name }}</td><td class="right">$ {{ fmt(it.amount) }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}

  <div class="totals">
    <div class="totals-row alt"><div class="totals-label">Total devengado</div><div class="totals-value">$ {{ fmt(liq.total_earnings) }}</div></div>
    <div class="totals-row"><div class="totals-label">Total deducciones</div><div class="totals-value">- $ {{ fmt(liq.total_deductions) }}</div></div>
  </div>
  <div class="net">NETO A PAGAR: $ {{ fmt(liq.net_amount) }} {{ liq.currency }}</div>

  {% if liq.notes %}
  <div class="notes"><strong>Observaciones:</strong><br/>{{ liq.notes|replace('\n', '<br/>') }}</div>
  {% endif %}

  <div class="signature">
    <div class="signature-cell">
      {% if signature_url %}<img src="{{ signature_url }}" class="signature-img"/>{% endif %}
      <div class="signature-line">{{ admin_name or '' }}<br/>
        <span style="font-size: 8pt; color: #6b7280;">{{ admin_title or 'Representante Legal' }} · {{ org_name }}</span>
      </div>
    </div>
    <div class="signature-cell">
      <div class="signature-line">{{ emp.full_name }}<br/>
        <span style="font-size: 8pt; color: #6b7280;">C.C. {{ emp.document_number or '—' }} · Trabajador</span>
      </div>
    </div>
  </div>

  <div class="footer">Documento generado por SavvyHR · {{ today }}</div>
</body></html>
"""


# ----------------------------------------------------- Plantilla MODERNA

MODERNA_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  @page { size: letter; margin: 1.2cm; }
  body { font-family: Helvetica, sans-serif; color: #1f2937; font-size: 9pt; }
  .banner { background: {{ brand }}; color: white; padding: 14px 18px; margin-bottom: 18px; }
  .banner-table { display: table; width: 100%; }
  .banner-left, .banner-right { display: table-cell; vertical-align: middle; }
  .banner-right { text-align: right; }
  .banner h1 { margin: 0; font-size: 18pt; letter-spacing: 2px; }
  .banner .sub { font-size: 9pt; opacity: 0.85; margin-top: 2px; }
  .org-block { font-size: 8pt; opacity: 0.85; text-align: right; }
  .columns { display: table; width: 100%; margin-bottom: 16px; }
  .col { display: table-cell; vertical-align: top; padding: 0 8px; width: 50%; }
  .card { background: #f9fafb; border-left: 3px solid {{ brand }}; padding: 10px 14px; margin-bottom: 8px; }
  .card-label { font-size: 7pt; text-transform: uppercase; color: #6b7280; letter-spacing: 0.5px; }
  .card-value { font-size: 11pt; font-weight: bold; }
  .items-wrap { background: white; border: 1px solid #e5e7eb; padding: 10px; border-radius: 4px; margin-bottom: 12px; }
  .items-title { font-size: 10pt; font-weight: bold; color: {{ brand }}; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 2px solid {{ brand }}; }
  table.items { width: 100%; border-collapse: collapse; font-size: 9pt; }
  table.items td { padding: 4px 6px; border-bottom: 1px solid #f3f4f6; }
  table.items td.right { text-align: right; font-family: monospace; }
  .total-grid { display: table; width: 100%; margin-top: 14px; }
  .total-grid-cell { display: table-cell; padding: 10px; vertical-align: top; width: 33%; }
  .total-card { background: #f9fafb; padding: 10px; border-radius: 4px; text-align: center; }
  .total-card .lbl { font-size: 7pt; text-transform: uppercase; color: #6b7280; }
  .total-card .val { font-size: 12pt; font-weight: bold; margin-top: 2px; font-family: monospace; }
  .total-card.net { background: {{ brand }}; color: white; }
  .total-card.net .lbl { color: white; opacity: 0.85; }
  .notes { margin-top: 12px; padding: 8px 12px; background: #fef3c7; border-radius: 4px; font-size: 8pt; }
  .footer-sign { margin-top: 36px; display: table; width: 100%; }
  .footer-sign div { display: table-cell; text-align: center; padding: 0 20px; }
  .footer-sign .line { border-top: 1px solid #6b7280; padding-top: 4px; font-size: 8pt; margin: 0 30px; }
  .signature-img { max-height: 44px; }
</style></head>
<body>
  <div class="banner">
    <div class="banner-table">
      <div class="banner-left">
        <h1>LIQUIDACIÓN</h1>
        <div class="sub">{{ liq.liquidation_number }} · {{ reason_label }}</div>
      </div>
      <div class="banner-right org-block">
        {% if logo_url %}<img src="{{ logo_url }}" style="max-height:38px; margin-bottom:4px;"/><br/>{% endif %}
        <strong>{{ org_name }}</strong><br/>
        {% if org_meta.address %}{{ org_meta.address }}<br/>{% endif %}
        {% if org_meta.tax_id %}NIT {{ org_meta.tax_id }}{% endif %}
      </div>
    </div>
  </div>

  <div class="columns">
    <div class="col">
      <div class="card"><div class="card-label">Trabajador</div><div class="card-value">{{ emp.full_name }}</div>
        <div style="font-size: 8pt; color: #6b7280;">{{ emp.employee_code }} · {{ emp.document_type or '' }} {{ emp.document_number or '—' }}</div></div>
      <div class="card"><div class="card-label">Cargo / Departamento</div><div class="card-value">{{ emp.position_name or '—' }}</div>
        <div style="font-size: 8pt; color: #6b7280;">{{ emp.department_name or '—' }}</div></div>
    </div>
    <div class="col">
      <div class="card"><div class="card-label">Período laborado</div><div class="card-value">{{ liq.days_worked_total }} días</div>
        <div style="font-size: 8pt; color: #6b7280;">{{ liq.contract_start_date }} → {{ liq.last_worked_date }}</div></div>
      <div class="card"><div class="card-label">Salario base · IBC</div><div class="card-value">$ {{ fmt(liq.base_salary) }}</div>
        <div style="font-size: 8pt; color: #6b7280;">IBC: $ {{ fmt(liq.average_salary) }}</div></div>
    </div>
  </div>

  <div class="items-wrap">
    <div class="items-title">Devengados</div>
    <table class="items">
      {% for it in earnings %}
      <tr><td><strong>{{ it.concept_name }}</strong>{% if it.notes %}<br/><span style="color:#9ca3af; font-size: 7pt;">{{ it.notes }}</span>{% endif %}</td>
          <td class="right">$ {{ fmt(it.amount) }}</td></tr>
      {% endfor %}
    </table>
  </div>

  {% if deductions %}
  <div class="items-wrap">
    <div class="items-title">Deducciones</div>
    <table class="items">
      {% for it in deductions %}
      <tr><td>{{ it.concept_name }}</td><td class="right">$ {{ fmt(it.amount) }}</td></tr>
      {% endfor %}
    </table>
  </div>
  {% endif %}

  <div class="total-grid">
    <div class="total-grid-cell"><div class="total-card"><div class="lbl">Devengado</div><div class="val">$ {{ fmt(liq.total_earnings) }}</div></div></div>
    <div class="total-grid-cell"><div class="total-card"><div class="lbl">Deducido</div><div class="val">$ {{ fmt(liq.total_deductions) }}</div></div></div>
    <div class="total-grid-cell"><div class="total-card net"><div class="lbl">Neto a Pagar</div><div class="val">$ {{ fmt(liq.net_amount) }}</div></div></div>
  </div>

  {% if liq.notes %}
  <div class="notes"><strong>Observaciones:</strong> {{ liq.notes|replace('\n', '<br/>') }}</div>
  {% endif %}

  <div class="footer-sign">
    <div>
      {% if signature_url %}<img src="{{ signature_url }}" class="signature-img"/><br/>{% endif %}
      <div class="line">{{ admin_name or '' }}<br/><span style="color:#6b7280;">{{ admin_title or 'Representante Legal' }}</span></div>
    </div>
    <div>
      <div class="line">{{ emp.full_name }}<br/><span style="color:#6b7280;">C.C. {{ emp.document_number or '—' }}</span></div>
    </div>
  </div>
</body></html>
"""


# ----------------------------------------------------- Plantilla COMPACTA

COMPACTA_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  @page { size: letter; margin: 1cm; }
  body { font-family: Helvetica, sans-serif; color: #111827; font-size: 8.5pt; }
  .top { display: table; width: 100%; border-bottom: 2px solid {{ brand }}; padding-bottom: 6px; margin-bottom: 8px; }
  .top-left, .top-right { display: table-cell; vertical-align: top; }
  .top-right { text-align: right; }
  .top h1 { margin: 0; font-size: 12pt; color: {{ brand }}; }
  .top .org { font-size: 9pt; font-weight: bold; }
  .top .num { font-size: 11pt; font-family: monospace; }
  .top .meta { font-size: 7pt; color: #6b7280; }
  .grid { display: table; width: 100%; margin-bottom: 6px; }
  .grid > div { display: table-cell; padding: 3px 6px; font-size: 8pt; vertical-align: top; }
  .grid .label { font-weight: bold; color: #6b7280; font-size: 7pt; text-transform: uppercase; }
  table.items { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 8pt; }
  table.items th { background: #f3f4f6; padding: 4px; text-align: left; font-size: 7pt; text-transform: uppercase; }
  table.items td { padding: 3px 5px; border-bottom: 1px solid #f3f4f6; }
  table.items td.right { text-align: right; font-family: monospace; }
  .totals { display: table; width: 100%; margin-top: 10px; }
  .totals > div { display: table-cell; padding: 4px 8px; }
  .totals .lbl { background: #f9fafb; font-weight: bold; }
  .totals .val { background: #f9fafb; text-align: right; font-family: monospace; }
  .totals .net-lbl { background: {{ brand }}; color: white; font-weight: bold; }
  .totals .net-val { background: {{ brand }}; color: white; text-align: right; font-family: monospace; font-weight: bold; }
  .signs { margin-top: 22px; display: table; width: 100%; font-size: 7pt; }
  .signs > div { display: table-cell; text-align: center; }
  .signs .line { border-top: 1px solid #9ca3af; margin: 0 24px; padding-top: 2px; }
  .signs img { max-height: 30px; }
  .notes { margin-top: 8px; padding: 4px 8px; background: #fffbeb; font-size: 7pt; }
</style></head>
<body>
  <div class="top">
    <div class="top-left">
      <h1>LIQUIDACIÓN LABORAL</h1>
      <div class="org">{{ org_name }}</div>
      <div class="meta">{% if org_meta.address %}{{ org_meta.address }}{% endif %}{% if org_meta.tax_id %} · NIT {{ org_meta.tax_id }}{% endif %}</div>
    </div>
    <div class="top-right">
      <div class="num">{{ liq.liquidation_number }}</div>
      <div class="meta">{{ today }}</div>
      <div class="meta">{{ reason_label }}</div>
    </div>
  </div>

  <div class="grid">
    <div><div class="label">Trabajador</div>{{ emp.full_name }}<br/>{{ emp.employee_code }}</div>
    <div><div class="label">Documento</div>{{ emp.document_type or '' }} {{ emp.document_number or '—' }}</div>
    <div><div class="label">Cargo</div>{{ emp.position_name or '—' }}</div>
    <div><div class="label">Período</div>{{ liq.contract_start_date }} → {{ liq.last_worked_date }}<br/><strong>{{ liq.days_worked_total }} días</strong></div>
  </div>
  <div class="grid">
    <div><div class="label">Salario base</div>$ {{ fmt(liq.base_salary) }}</div>
    <div><div class="label">IBC</div>$ {{ fmt(liq.average_salary) }}</div>
    <div><div class="label">Terminación</div>{{ liq.termination_date }}</div>
    <div><div class="label">Estado</div>{{ liq.status|upper }}</div>
  </div>

  <table class="items">
    <thead><tr><th>Concepto</th><th class="right">Cantidad</th><th class="right">Valor</th></tr></thead>
    <tbody>
      {% for it in earnings %}
      <tr><td>{{ it.concept_name }}</td><td class="right">{{ it.quantity }}</td><td class="right">$ {{ fmt(it.amount) }}</td></tr>
      {% endfor %}
      {% for it in deductions %}
      <tr><td style="color:#dc2626;">{{ it.concept_name }}</td><td class="right">{{ it.quantity }}</td><td class="right" style="color:#dc2626;">- $ {{ fmt(it.amount) }}</td></tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="totals">
    <div class="lbl">Devengado</div>
    <div class="val">$ {{ fmt(liq.total_earnings) }}</div>
    <div class="lbl">Deducido</div>
    <div class="val">- $ {{ fmt(liq.total_deductions) }}</div>
    <div class="net-lbl">NETO</div>
    <div class="net-val">$ {{ fmt(liq.net_amount) }}</div>
  </div>

  {% if liq.notes %}<div class="notes"><strong>Obs:</strong> {{ liq.notes|replace('\n', ' · ') }}</div>{% endif %}

  <div class="signs">
    <div>
      {% if signature_url %}<img src="{{ signature_url }}"/><br/>{% endif %}
      <div class="line">{{ admin_name or '' }} — {{ admin_title or 'Representante Legal' }}</div>
    </div>
    <div><div class="line">{{ emp.full_name }} — C.C. {{ emp.document_number or '—' }}</div></div>
  </div>
</body></html>
"""


TEMPLATES = {
    "formal": FORMAL_HTML,
    "moderna": MODERNA_HTML,
    "compacta": COMPACTA_HTML,
}


REASON_LABELS = {
    "voluntary": "Renuncia voluntaria del trabajador",
    "mutual": "Mutuo acuerdo",
    "with_cause": "Despido con justa causa",
    "without_cause": "Despido sin justa causa",
    "end_of_contract": "Vencimiento del término del contrato",
    "retirement": "Pensión / jubilación",
    "death": "Fallecimiento del trabajador",
    "other": "Otra causa",
}


def _fmt(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return str(value)


async def render_liquidation_pdf(
    db: AsyncSession,
    org_id: uuid.UUID,
    liq: HrLiquidation,
    items: list[HrLiquidationItem],
    *,
    template_key: str | None = None,
) -> tuple[bytes, str]:
    """Renderiza el PDF de la liquidación en la plantilla indicada (o la default
    de la organización). Devuelve (bytes_pdf, nombre_de_archivo)."""

    org = (await db.execute(
        select(Organization).where(Organization.id == org_id)
    )).scalar_one()
    settings = (await db.execute(
        select(HrSettings).where(HrSettings.organization_id == org_id)
    )).scalar_one_or_none()
    emp = (await db.execute(
        select(HrEmployee).where(HrEmployee.id == liq.employee_id)
    )).scalar_one()

    dept_name = None
    pos_name = None
    if emp.department_id:
        d = (await db.execute(select(HrDepartment).where(HrDepartment.id == emp.department_id))).scalar_one_or_none()
        dept_name = d.name if d else None
    if emp.position_id:
        p = (await db.execute(select(HrPosition).where(HrPosition.id == emp.position_id))).scalar_one_or_none()
        pos_name = p.name if p else None

    # Resolver plantilla
    key = (template_key or liq.pdf_template or
           (settings.default_liquidation_template if settings else None) or "formal")
    if key not in TEMPLATES:
        key = "formal"

    # Datos org
    org_settings = (org.settings or {}) if hasattr(org, "settings") else {}
    org_meta = {
        "address": org_settings.get("address") or org_settings.get("street"),
        "city": org_settings.get("city"),
        "tax_id": org_settings.get("tax_id") or org_settings.get("nit"),
    }

    logo_url = (settings.logo_url if settings and settings.logo_url else
                org_settings.get("logo_url"))
    signature_url = settings.signature_url if settings else None
    admin_name = (settings.admin_name if settings and settings.admin_name else
                  org_settings.get("admin_name") or org_settings.get("legal_representative"))
    admin_title = settings.admin_title if settings else None
    brand = (settings.brand_color if settings and settings.brand_color else
             org_settings.get("brand_color") or "#EC4899")

    full_name = " ".join(x for x in [emp.first_name, emp.last_name] if x).strip()
    earnings = [it for it in items if it.kind == "earning"]
    deductions = [it for it in items if it.kind == "deduction"]

    template = Template(TEMPLATES[key])
    html = template.render(
        liq=liq,
        emp={
            "full_name": full_name,
            "employee_code": emp.employee_code,
            "document_type": emp.document_type,
            "document_number": emp.document_number,
            "department_name": dept_name,
            "position_name": pos_name,
        },
        earnings=earnings,
        deductions=deductions,
        org_name=org.name,
        org_meta=org_meta,
        logo_url=logo_url,
        signature_url=signature_url,
        admin_name=admin_name,
        admin_title=admin_title,
        brand=brand,
        reason_label=REASON_LABELS.get(liq.termination_reason, liq.termination_reason),
        today=datetime.now().strftime("%Y-%m-%d"),
        fmt=_fmt,
    )

    buf = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"Error generando PDF: {result.err}")
    filename = f"liquidacion-{liq.liquidation_number}-{full_name.replace(' ', '_')}.pdf"
    return buf.getvalue(), filename
