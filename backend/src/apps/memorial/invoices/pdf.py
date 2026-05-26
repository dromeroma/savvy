"""PDF de factura de SavvyMemorial (reutiliza xhtml2pdf como water)."""

from __future__ import annotations

import io
import uuid
from decimal import Decimal

from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from xhtml2pdf import pisa

from src.apps.memorial.models import (
    MemorialExequialContract,
    MemorialInvoice,
    MemorialPayment,
    MemorialPaymentInvoice,
    MemorialService,
)
from src.core.exceptions import NotFoundError
from src.modules.organization.models import Organization


STATUS_LABELS = {
    "pending": "PENDIENTE",
    "partial": "PAGO PARCIAL",
    "paid": "PAGADA",
    "overdue": "VENCIDA",
    "annulled": "ANULADA",
}

REGIME_LABELS = {
    "simplificado": "Régimen simplificado",
    "comun": "Régimen común",
    "no_responsable": "No responsable de IVA",
}


INVOICE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8" />
<style>
  @page { size: letter; margin: 1.5cm; }
  body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #222; }
  h1 { font-size: 16pt; margin: 0; color: #6B7280; }
  h2 { font-size: 11pt; margin: 0 0 6pt 0; color: #555; }
  .muted { color: #777; font-size: 9pt; }
  table { width: 100%; border-collapse: collapse; }
  .org-name { font-size: 14pt; font-weight: bold; color: #1f2937; }
  .badge { display: inline-block; padding: 3pt 8pt; border-radius: 4pt; font-size: 9pt; font-weight: bold; color: white; }
  .badge-pending { background: #f59e0b; }
  .badge-partial { background: #3b82f6; }
  .badge-paid { background: #10b981; }
  .badge-overdue { background: #ef4444; }
  .badge-annulled { background: #6b7280; }
  .info-box { background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 4pt; padding: 8pt; margin-top: 8pt; }
  .breakdown { margin-top: 12pt; }
  .breakdown th, .breakdown td { border-bottom: 1px solid #e5e7eb; padding: 6pt 4pt; text-align: left; }
  .breakdown th { background: #f9fafb; font-size: 9pt; color: #555; }
  .right { text-align: right; }
  .totals td { padding: 4pt; }
  .total-row td { font-size: 12pt; font-weight: bold; border-top: 2px solid #222; padding-top: 8pt; }
  .balance-row td { font-size: 11pt; font-weight: bold; color: #b91c1c; padding-top: 6pt; }
  .footer { margin-top: 18pt; padding-top: 10pt; border-top: 1px dashed #ccc; font-size: 8.5pt; color: #666; }
</style></head>
<body>

  <table>
    <tr>
      {% if logo_data_url %}
      <td style="width: 80pt; vertical-align: top;">
        <img src="{{ logo_data_url }}" style="max-width: 70pt; max-height: 70pt;" />
      </td>
      {% endif %}
      <td style="vertical-align: top;">
        <div class="org-name">{{ fiscal.legal_name or org.name }}</div>
        <div class="muted">Servicios funerarios y planes exequiales</div>
        {% if fiscal.nit %}<div class="muted">NIT: {{ fiscal.nit }}{% if fiscal.dv %}-{{ fiscal.dv }}{% endif %}</div>{% endif %}
        {% if fiscal.address %}<div class="muted">{{ fiscal.address }}{% if fiscal.city %}, {{ fiscal.city }}{% endif %}{% if fiscal.department %}, {{ fiscal.department }}{% endif %}</div>{% endif %}
        {% if fiscal.phone or fiscal.email %}
        <div class="muted">
          {% if fiscal.phone %}Tel: {{ fiscal.phone }}{% endif %}
          {% if fiscal.phone and fiscal.email %} · {% endif %}
          {% if fiscal.email %}{{ fiscal.email }}{% endif %}
        </div>
        {% endif %}
        {% if regime_label %}<div class="muted">Régimen: {{ regime_label }}</div>{% endif %}
      </td>
      <td style="width: 35%; text-align: right; vertical-align: top;">
        <h1>FACTURA {{ inv.code }}</h1>
        <div class="muted">{{ source_label }}</div>
        <div style="margin-top: 6pt;"><span class="badge badge-{{ inv.status }}">{{ status_label }}</span></div>
      </td>
    </tr>
  </table>

  {% if fiscal.dian_resolution %}
  <div class="muted" style="margin-top: 4pt; font-size: 8pt; font-style: italic;">{{ fiscal.dian_resolution }}</div>
  {% endif %}

  <!-- Responsable + meta -->
  <table style="margin-top: 14pt;">
    <tr>
      <td style="width: 60%; vertical-align: top; padding-right: 8pt;">
        <h2>Responsable de pago</h2>
        <div class="info-box">
          <strong>{{ inv.responsible_name }}</strong><br/>
          {% if inv.responsible_document %}<span class="muted">Doc:</span> {{ inv.responsible_document }}<br/>{% endif %}
          {% if inv.responsible_email %}<span class="muted">Email:</span> {{ inv.responsible_email }}<br/>{% endif %}
          {% if inv.responsible_phone %}<span class="muted">Tel:</span> {{ inv.responsible_phone }}<br/>{% endif %}
          {% if inv.responsible_address %}{{ inv.responsible_address }}{% endif %}
        </div>
      </td>
      <td style="width: 40%; vertical-align: top;">
        <h2>Datos de la factura</h2>
        <div class="info-box">
          <span class="muted">Emisión:</span> {{ inv.issue_date }}<br/>
          <span class="muted">Vencimiento:</span> <strong>{{ inv.due_date }}</strong>
          {% if inv.period_start %}
          <br/><span class="muted">Periodo:</span> {{ inv.period_start }} a {{ inv.period_end }}
          {% endif %}
          {% if contract_code %}
          <br/><span class="muted">Contrato:</span> {{ contract_code }}
          {% endif %}
          {% if service_code %}
          <br/><span class="muted">Servicio:</span> {{ service_code }}
          {% endif %}
        </div>
      </td>
    </tr>
  </table>

  <!-- Concepto -->
  <h2 style="margin-top: 16pt;">Detalle</h2>
  <table class="breakdown">
    <thead>
      <tr><th>Concepto</th><th class="right">Valor</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>{{ inv.description or 'Servicio facturado' }}</td>
        <td class="right">$ {{ fmt(inv.subtotal) }}</td>
      </tr>
      {% if inv.surcharges > 0 %}
      <tr><td>Recargos</td><td class="right">$ {{ fmt(inv.surcharges) }}</td></tr>
      {% endif %}
      {% if inv.late_interest > 0 %}
      <tr><td>Interés de mora</td><td class="right" style="color:#b91c1c;">$ {{ fmt(inv.late_interest) }}</td></tr>
      {% endif %}
      {% if inv.discounts > 0 %}
      <tr><td>Descuentos</td><td class="right" style="color:#15803d;">- $ {{ fmt(inv.discounts) }}</td></tr>
      {% endif %}
    </tbody>
  </table>

  <table class="totals" style="margin-left: auto; width: 50%;">
    <tr class="total-row"><td class="right">TOTAL FACTURA</td><td class="right">$ {{ fmt(inv.total) }}</td></tr>
    {% if inv.paid_amount > 0 %}
    <tr><td class="right muted">Pagado</td><td class="right" style="color:#15803d;">$ {{ fmt(inv.paid_amount) }}</td></tr>
    {% endif %}
    <tr class="balance-row"><td class="right">SALDO A PAGAR</td><td class="right">$ {{ fmt(inv.balance) }}</td></tr>
  </table>

  {% if applied_payments %}
  <h2 style="margin-top: 14pt;">Pagos aplicados</h2>
  <table class="breakdown">
    <thead><tr><th>Fecha</th><th>Método</th><th>Recibo</th><th class="right">Monto</th></tr></thead>
    <tbody>
      {% for p in applied_payments %}
      <tr>
        <td>{{ p.date }}</td>
        <td>{{ p.method }}</td>
        <td>{{ p.receipt or '—' }}</td>
        <td class="right">$ {{ fmt(p.amount) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}

  {% if inv.notes %}
  <div style="margin-top: 12pt; font-size: 9pt;"><strong>Observaciones:</strong> {{ inv.notes }}</div>
  {% endif %}

  <div class="footer">
    Para pagar, comunícate con la administración o usa los canales que ofrece la funeraria.
    Después del vencimiento se generarán intereses de mora.
    <br/><br/>Esta factura fue generada electrónicamente.
  </div>
</body></html>
"""


def _fmt(n: Decimal | float | int | None) -> str:
    if n is None:
        return "0"
    return f"{int(round(float(n))):,}".replace(",", ".")


async def render_invoice_pdf(
    db: AsyncSession,
    org_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> tuple[bytes, str]:
    inv = await db.scalar(
        select(MemorialInvoice).where(
            MemorialInvoice.id == invoice_id,
            MemorialInvoice.organization_id == org_id,
        )
    )
    if inv is None:
        raise NotFoundError("Factura no encontrada.")

    org = await db.scalar(select(Organization).where(Organization.id == org_id))
    org_settings = org.settings or {} if org else {}
    fiscal = org_settings.get("fiscal_info") or {}
    logo_data_url = org_settings.get("logo_data_url")
    regime_label = REGIME_LABELS.get(fiscal.get("tax_regime", ""), "")

    contract_code = None
    if inv.contract_id is not None:
        c = await db.scalar(
            select(MemorialExequialContract).where(MemorialExequialContract.id == inv.contract_id),
        )
        contract_code = c.code if c else None
    service_code = None
    if inv.service_id is not None:
        svc = await db.scalar(
            select(MemorialService).where(MemorialService.id == inv.service_id),
        )
        service_code = svc.code if svc else None

    pay_rows = await db.execute(
        select(
            MemorialPayment.payment_date,
            MemorialPayment.method,
            MemorialPayment.receipt_number,
            MemorialPaymentInvoice.amount,
        )
        .join(MemorialPaymentInvoice, MemorialPaymentInvoice.payment_id == MemorialPayment.id)
        .where(MemorialPaymentInvoice.invoice_id == inv.id)
        .order_by(MemorialPayment.payment_date)
    )
    applied_payments = [
        {"date": r[0], "method": r[1], "receipt": r[2], "amount": r[3]}
        for r in pay_rows.all()
    ]

    source_label = (
        "Cuota plan exequial" if inv.source_type == "exequial_dues" else "Servicio funerario"
    )

    template = Template(INVOICE_HTML)
    html = template.render(
        inv=inv,
        org=org,
        fiscal=fiscal,
        logo_data_url=logo_data_url,
        regime_label=regime_label,
        contract_code=contract_code,
        service_code=service_code,
        source_label=source_label,
        status_label=STATUS_LABELS.get(inv.status, inv.status.upper()),
        applied_payments=applied_payments,
        fmt=_fmt,
    )

    buf = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8")
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed ({pisa_status.err} errors).")
    filename = f"factura-{inv.code}.pdf"
    return buf.getvalue(), filename
