"""Invoice PDF rendering using xhtml2pdf.

Pipeline:
  invoice + subscriber + org → Jinja2 template → HTML → xhtml2pdf → PDF bytes

xhtml2pdf is pure Python (no system deps) so it works the same on Windows
dev and Linux production. Layout uses inline CSS that xhtml2pdf supports.
"""

from __future__ import annotations

import io
import uuid
from datetime import date
from decimal import Decimal

from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from xhtml2pdf import pisa

from src.apps.water.models import (
    WaterInvoice,
    WaterMeter,
    WaterPayment,
    WaterPaymentInvoice,
    WaterSubscriber,
)
from src.core.exceptions import NotFoundError
from src.modules.organization.models import Organization


# Status labels in Spanish for the printed badge.
STATUS_LABELS = {
    "pending": "PENDIENTE",
    "partial": "PAGO PARCIAL",
    "paid": "PAGADA",
    "overdue": "VENCIDA",
    "annulled": "ANULADA",
}

# Régimen tributario labels
REGIME_LABELS = {
    "simplificado": "Régimen simplificado",
    "comun": "Régimen común",
    "no_responsable": "No responsable de IVA",
}


INVOICE_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Factura #{{ inv.consecutive }}</title>
  <style>
    @page { size: letter; margin: 1.5cm; }
    body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #222; }
    h1 { font-size: 16pt; margin: 0; color: #0EA5E9; }
    h2 { font-size: 11pt; margin: 0 0 6pt 0; color: #555; }
    .muted { color: #777; font-size: 9pt; }
    .row { display: block; width: 100%; }
    table { width: 100%; border-collapse: collapse; }
    .header-table td { vertical-align: top; padding: 0; }
    .org-name { font-size: 14pt; font-weight: bold; color: #0c4a6e; }
    .badge {
      display: inline-block; padding: 3pt 8pt; border-radius: 4pt;
      font-size: 9pt; font-weight: bold; color: white;
    }
    .badge-pending { background: #f59e0b; }
    .badge-partial { background: #3b82f6; }
    .badge-paid { background: #10b981; }
    .badge-overdue { background: #ef4444; }
    .badge-annulled { background: #6b7280; }
    .info-box {
      background: #f3f4f6; border: 1px solid #e5e7eb;
      border-radius: 4pt; padding: 8pt; margin-top: 8pt;
    }
    .breakdown { margin-top: 12pt; }
    .breakdown th, .breakdown td {
      border-bottom: 1px solid #e5e7eb; padding: 6pt 4pt; text-align: left;
    }
    .breakdown th { background: #f9fafb; font-size: 9pt; color: #555; }
    .breakdown td.right, .breakdown th.right { text-align: right; }
    .totals { margin-top: 6pt; }
    .totals td { padding: 4pt 4pt; }
    .totals td.label { text-align: right; color: #555; }
    .totals td.value { text-align: right; }
    .total-row td { font-size: 12pt; font-weight: bold; border-top: 2px solid #222; padding-top: 8pt; }
    .balance-row td { font-size: 11pt; font-weight: bold; color: #b91c1c; padding-top: 6pt; }
    .footer {
      margin-top: 18pt; padding-top: 10pt; border-top: 1px dashed #ccc;
      font-size: 8.5pt; color: #666;
    }
    .stub-divider {
      border-top: 1px dashed #999; margin: 20pt 0 10pt 0;
      text-align: center; font-size: 8pt; color: #999;
    }
    .stub-table th, .stub-table td { padding: 3pt 4pt; font-size: 9pt; }
    .stub-table th { background: #f9fafb; color: #555; text-align: left; }
  </style>
</head>
<body>

  <!-- Header -->
  <table class="header-table">
    <tr>
      {% if logo_data_url %}
      <td style="width: 80pt; vertical-align: top;">
        <img src="{{ logo_data_url }}" style="max-width: 70pt; max-height: 70pt;" />
      </td>
      {% endif %}
      <td style="vertical-align: top;">
        <div class="org-name">{{ fiscal.legal_name or org.name }}</div>
        <div class="muted">Servicio de acueducto</div>
        {% if fiscal.nit %}
        <div class="muted">NIT: {{ fiscal.nit }}{% if fiscal.dv %}-{{ fiscal.dv }}{% endif %}</div>
        {% endif %}
        {% if fiscal.address %}
        <div class="muted">
          {{ fiscal.address }}{% if fiscal.city %}, {{ fiscal.city }}{% endif %}{% if fiscal.department %}, {{ fiscal.department }}{% endif %}
        </div>
        {% endif %}
        {% if fiscal.phone or fiscal.email %}
        <div class="muted">
          {% if fiscal.phone %}Tel: {{ fiscal.phone }}{% endif %}
          {% if fiscal.phone and fiscal.email %} · {% endif %}
          {% if fiscal.email %}{{ fiscal.email }}{% endif %}
        </div>
        {% endif %}
        {% if fiscal.tax_regime %}
        <div class="muted">Régimen: {{ regime_label }}</div>
        {% endif %}
      </td>
      <td style="width: 35%; text-align: right; vertical-align: top;">
        <h1>FACTURA #{{ inv.consecutive }}</h1>
        <div class="muted">Periodo {{ inv.period_year }}-{{ '%02d' % inv.period_month }}</div>
        <div style="margin-top: 6pt;">
          <span class="badge badge-{{ inv.status }}">{{ status_label }}</span>
        </div>
      </td>
    </tr>
  </table>

  {% if fiscal.dian_resolution %}
  <div class="muted" style="margin-top: 4pt; font-size: 8pt; font-style: italic;">
    {{ fiscal.dian_resolution }}
  </div>
  {% endif %}

  <!-- Subscriber + Invoice metadata -->
  <table style="margin-top: 14pt;">
    <tr>
      <td style="width: 60%; vertical-align: top; padding-right: 8pt;">
        <h2>Suscriptor</h2>
        <div class="info-box">
          <strong>{{ subscriber_name }}</strong><br/>
          <span class="muted">Código:</span> {{ sub.code }}<br/>
          {% if sub.document_number %}
          <span class="muted">{{ sub.document_type or 'Doc' }}:</span> {{ sub.document_number }}<br/>
          {% endif %}
          {% if sub.address %}
          {{ sub.address }}{% if sub.neighborhood %}, {{ sub.neighborhood }}{% endif %}<br/>
          {% endif %}
          {% if sub.stratum %}
          <span class="muted">Estrato:</span> {{ sub.stratum }}
          &nbsp;·&nbsp;
          <span class="muted">Tipo:</span> {{ sub.subscriber_type }}
          {% endif %}
        </div>
      </td>
      <td style="width: 40%; vertical-align: top;">
        <h2>Datos de la factura</h2>
        <div class="info-box">
          <span class="muted">Emisión:</span> {{ inv.issue_date }}<br/>
          <span class="muted">Vencimiento:</span> <strong>{{ inv.due_date }}</strong><br/>
          {% if meter_serial %}
          <span class="muted">Medidor:</span> {{ meter_serial }}<br/>
          {% endif %}
          {% if cons %}
          <span class="muted">Lectura anterior:</span> {{ cons.previous_reading }} m³<br/>
          <span class="muted">Lectura actual:</span> {{ cons.current_reading }} m³
          {% endif %}
        </div>
      </td>
    </tr>
  </table>

  <!-- Breakdown -->
  <h2 style="margin-top: 16pt;">Detalle</h2>
  <table class="breakdown">
    <thead>
      <tr>
        <th>Concepto</th>
        <th class="right">Cantidad</th>
        <th class="right">Valor</th>
      </tr>
    </thead>
    <tbody>
      {% if fixed_charge > 0 %}
      <tr>
        <td>Cargo fijo mensual</td>
        <td class="right">1</td>
        <td class="right">$ {{ fmt(fixed_charge) }}</td>
      </tr>
      {% endif %}
      {% if consumption_cubic > 0 %}
      <tr>
        <td>Consumo de agua</td>
        <td class="right">{{ consumption_cubic }} m³</td>
        <td class="right">$ {{ fmt(consumption_charge) }}</td>
      </tr>
      {% endif %}
      {% if surcharges > 0 %}
      <tr>
        <td>Recargos</td><td class="right">—</td>
        <td class="right">$ {{ fmt(surcharges) }}</td>
      </tr>
      {% endif %}
      {% if reconnection_fee > 0 %}
      <tr>
        <td>Cargo por reconexión</td><td class="right">—</td>
        <td class="right">$ {{ fmt(reconnection_fee) }}</td>
      </tr>
      {% endif %}
      {% if suspension_fee > 0 %}
      <tr>
        <td>Cargo por suspensión</td><td class="right">—</td>
        <td class="right">$ {{ fmt(suspension_fee) }}</td>
      </tr>
      {% endif %}
      {% if late_interest > 0 %}
      <tr>
        <td>Interés de mora</td><td class="right">—</td>
        <td class="right" style="color: #b91c1c;">$ {{ fmt(late_interest) }}</td>
      </tr>
      {% endif %}
      {% if discounts > 0 %}
      <tr>
        <td>Descuentos</td><td class="right">—</td>
        <td class="right" style="color: #15803d;">- $ {{ fmt(discounts) }}</td>
      </tr>
      {% endif %}
    </tbody>
  </table>

  <!-- Totals -->
  <table class="totals" style="margin-left: auto; width: 50%;">
    <tr class="total-row">
      <td class="label">TOTAL FACTURA</td>
      <td class="value">$ {{ fmt(total) }}</td>
    </tr>
    {% if paid_amount > 0 %}
    <tr>
      <td class="label">Pagado</td>
      <td class="value" style="color: #15803d;">$ {{ fmt(paid_amount) }}</td>
    </tr>
    {% endif %}
    <tr class="balance-row">
      <td class="label">SALDO A PAGAR</td>
      <td class="value">$ {{ fmt(balance) }}</td>
    </tr>
  </table>

  <!-- Pagos aplicados (si tiene) -->
  {% if applied_payments %}
  <h2 style="margin-top: 14pt;">Pagos aplicados a esta factura</h2>
  <table class="breakdown">
    <thead>
      <tr><th>Fecha</th><th>Método</th><th>Recibo</th><th class="right">Monto</th></tr>
    </thead>
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
  <div style="margin-top: 12pt; font-size: 9pt;">
    <strong>Observaciones:</strong> {{ inv.notes }}
  </div>
  {% endif %}

  <!-- Footer -->
  <div class="footer">
    <strong>Cómo pagar:</strong> Acércate a la oficina del acueducto, paga al cobrador
    asignado a tu zona o consulta tus opciones de pago en línea con la administración.
    Después de la fecha de vencimiento se generarán intereses de mora.<br/><br/>
    Esta factura fue generada electrónicamente. Consérvala como soporte de pago.
  </div>

  <!-- Stub for the cashier -->
  <div class="stub-divider">- - - - - - - - - - - corte aquí - - - - - - - - - - -</div>
  <table class="stub-table">
    <tr>
      <th style="width: 25%;">Factura</th>
      <td style="width: 25%;">#{{ inv.consecutive }}</td>
      <th style="width: 25%;">Periodo</th>
      <td style="width: 25%;">{{ inv.period_year }}-{{ '%02d' % inv.period_month }}</td>
    </tr>
    <tr>
      <th>Suscriptor</th><td colspan="3">{{ subscriber_name }} ({{ sub.code }})</td>
    </tr>
    <tr>
      <th>Vence</th><td>{{ inv.due_date }}</td>
      <th>Saldo</th><td><strong>$ {{ fmt(balance) }}</strong></td>
    </tr>
  </table>

</body>
</html>
"""


def _fmt(n: Decimal | float | int | None) -> str:
    if n is None:
        return "0"
    return f"{int(round(float(n))):,}".replace(",", ".")


def _subscriber_display(sub: WaterSubscriber) -> str:
    if sub.business_name:
        return sub.business_name
    return f"{sub.first_name} {sub.last_name or ''}".strip()


async def render_invoice_pdf(
    db: AsyncSession,
    org_id: uuid.UUID,
    invoice_id: uuid.UUID,
    *,
    subscriber_id: uuid.UUID | None = None,
) -> tuple[bytes, str]:
    """Render an invoice as a PDF. Returns (pdf_bytes, suggested_filename).

    If `subscriber_id` is provided, the invoice MUST belong to that subscriber
    (used by the customer portal endpoint to prevent cross-account reads).
    """
    # Load invoice
    stmt = select(WaterInvoice).where(
        WaterInvoice.id == invoice_id,
        WaterInvoice.organization_id == org_id,
    )
    if subscriber_id is not None:
        stmt = stmt.where(WaterInvoice.subscriber_id == subscriber_id)
    inv = await db.scalar(stmt)
    if inv is None:
        raise NotFoundError("Invoice not found.")

    sub = await db.scalar(
        select(WaterSubscriber).where(WaterSubscriber.id == inv.subscriber_id),
    )
    if sub is None:
        raise NotFoundError("Subscriber not found.")

    org = await db.scalar(select(Organization).where(Organization.id == org_id))
    org_settings = org.settings or {} if org else {}

    # Consumption row (for meter serial + readings)
    cons = None
    meter_serial = None
    if inv.consumption_id is not None:
        from src.apps.water.models import WaterConsumption
        cons = await db.scalar(
            select(WaterConsumption).where(WaterConsumption.id == inv.consumption_id),
        )
        if cons:
            meter = await db.scalar(
                select(WaterMeter).where(WaterMeter.id == cons.meter_id),
            )
            meter_serial = meter.serial_number if meter else None

    # Payments applied to this invoice
    pay_rows = await db.execute(
        select(WaterPayment.payment_date, WaterPayment.method,
               WaterPayment.receipt_number, WaterPaymentInvoice.amount)
        .join(WaterPaymentInvoice, WaterPaymentInvoice.payment_id == WaterPayment.id)
        .where(WaterPaymentInvoice.invoice_id == inv.id)
        .order_by(WaterPayment.payment_date)
    )
    applied_payments = [
        {"date": r[0], "method": r[1], "receipt": r[2], "amount": r[3]}
        for r in pay_rows.all()
    ]

    fiscal = org_settings.get("fiscal_info") or {}
    logo_data_url = org_settings.get("logo_data_url")
    regime_label = REGIME_LABELS.get(fiscal.get("tax_regime", ""), "")

    template = Template(INVOICE_HTML)
    html = template.render(
        inv=inv,
        sub=sub,
        org=org,
        org_settings=org_settings,
        fiscal=fiscal,
        logo_data_url=logo_data_url,
        regime_label=regime_label,
        cons=cons,
        meter_serial=meter_serial,
        subscriber_name=_subscriber_display(sub),
        status_label=STATUS_LABELS.get(inv.status, inv.status.upper()),
        fixed_charge=Decimal(inv.fixed_charge),
        consumption_cubic=Decimal(inv.consumption_cubic),
        consumption_charge=Decimal(inv.consumption_charge),
        surcharges=Decimal(inv.surcharges),
        discounts=Decimal(inv.discounts),
        reconnection_fee=Decimal(inv.reconnection_fee),
        suspension_fee=Decimal(inv.suspension_fee),
        late_interest=Decimal(inv.late_interest),
        total=Decimal(inv.total),
        paid_amount=Decimal(inv.paid_amount),
        balance=Decimal(inv.balance),
        applied_payments=applied_payments,
        fmt=_fmt,
    )

    buf = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8")
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed ({pisa_status.err} errors).")
    filename = f"factura-{inv.consecutive}-{sub.code}.pdf"
    return buf.getvalue(), filename
