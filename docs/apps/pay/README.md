# SavvyPay — Infraestructura Financiera del Ecosistema

## Proposito

SavvyPay es el **backbone financiero** del ecosistema Savvy. Es una infraestructura de pagos de nivel bancario basada en un **ledger de doble partida inmutable**. Todo el dinero que fluye en el ecosistema pasa por SavvyPay.

**NO es un simple gateway de pagos. Es un sistema financiero completo.**

---

## Principios Fundamentales

1. **Correccion financiera obligatoria**: Nunca se pierde ni duplica dinero
2. **Ledger inmutable**: Las entradas del ledger nunca se modifican ni eliminan
3. **Saldos derivados**: Los balances NUNCA se almacenan — se calculan desde el ledger
4. **Doble partida**: Cada movimiento genera debito + credito que DEBEN cuadrar
5. **Idempotencia**: Toda operacion tiene clave de idempotencia para prevenir duplicados
6. **Eventos inmutables**: Cada accion financiera emite un evento auditable
7. **Trazabilidad**: Cada entrada rastrea quien, cuando, por que y desde que sistema

---

## Entidades (11 tablas)

| Tabla | Tipo | Descripcion |
|-------|------|-------------|
| `pay_accounts` | Core | Cuentas internas del ledger (wallet, fees, clearing, reserves) |
| `pay_ledger_entries` | Core (IMMUTABLE) | Entradas de doble partida — la fuente de verdad |
| `pay_events` | Core (IMMUTABLE) | Log de eventos financieros |
| `pay_idempotency_keys` | Core | Prevencion de operaciones duplicadas |
| `pay_transactions` | Business | Transacciones con maquina de estados |
| `pay_refunds` | Business | Reembolsos parciales/totales |
| `pay_wallets` | Business | Wallets con 3 cuentas ledger (available, pending, reserved) |
| `pay_fee_rules` | Config | Reglas de comisiones configurables |
| `pay_payouts` | Business | Retiros/transferencias a comercios |
| `pay_subscription_plans` | Config | Planes de suscripcion |
| `pay_subscriptions_active` | Business | Suscripciones activas |

---

## LedgerEngine (El Corazon)

### Invariante critico

```
Para cualquier journal_id:
  SUM(debitos) == SUM(creditos)
```

Si no cuadra, se rechaza con `ValidationError`. No hay excepciones.

### Tipos de cuenta

| Tipo | Proposito |
|------|-----------|
| `user_wallet` | Fondos disponibles del usuario/comercio |
| `user_pending` | Fondos autorizados pero no liquidados |
| `user_reserved` | Fondos reservados (durante autorizacion) |
| `platform_fees` | Comisiones de la plataforma |
| `platform_clearing` | Cuenta de compensacion para liquidacion |
| `platform_reserve` | Reserva/escrow |
| `external_bank` | Representa movimientos bancarios externos |

### Calculo de saldo

```python
balance = SUM(debits for account) - SUM(credits for account)
```

Los saldos son SIEMPRE computados en tiempo real desde el ledger. Nunca almacenados.

---

## Transaction State Machine

```
pending → authorized → captured → settled
pending → failed
pending → cancelled
authorized → captured
authorized → failed
authorized → cancelled
captured → settled
captured → refunded
settled → refunded
```

### Eventos emitidos por transicion

| Transicion | Evento | Efecto en ledger |
|------------|--------|-----------------|
| → captured | payment.captured | Debit payee, Credit payer |
| → refunded | payment.refunded | Reverse: Debit payer, Credit payee |
| → settled | payment.settled | (Evento de registro) |
| → failed | payment.failed | (Sin efecto en ledger) |

---

## Wallet Engine

Cada wallet tiene **3 cuentas ledger** vinculadas:

```
PayWallet
├── available_account_id → pay_accounts (user_wallet)
├── pending_account_id → pay_accounts (user_pending)
└── reserved_account_id → pay_accounts (user_reserved)
```

### Operaciones

| Operacion | Efecto ledger |
|-----------|---------------|
| **Fund** | Debit wallet.available, Credit platform.clearing |
| **Transfer** | Debit to_wallet.available, Credit from_wallet.available |
| **Reserve** | Debit wallet.reserved, Credit wallet.available |
| **Release** | Debit wallet.available, Credit wallet.reserved |

### Respuesta de balance

```json
{
  "wallet_id": "uuid",
  "available": 500000.00,
  "pending": 100000.00,
  "reserved": 50000.00,
  "total": 650000.00
}
```

---

## Fee System

### Tipos de regla

| Tipo | Calculo |
|------|---------|
| `percentage` | amount * percentage_value / 100 |
| `fixed` | fixed_value |
| `tiered` | Escalonado por rango de monto (JSONB rules) |

### Restricciones

- `min_fee`: cobro minimo garantizado
- `max_fee`: tope maximo
- `applies_to`: filtra por tipo de transaccion (payment, payout, subscription, transfer, all)
- `source_app`: filtra por app de origen (pos, credit, parking, etc.)

---

## Idempotencia

Toda operacion critica acepta `idempotency_key`:

1. Si la key NO existe: ejecuta la operacion, guarda la key + resultado
2. Si la key YA existe: retorna `ConflictError` (409)

Esto previene:
- Cobros duplicados
- Doble gasto
- Race conditions en operaciones concurrentes

---

## Event System

Cada accion financiera emite un evento inmutable:

| Evento | Cuando |
|--------|--------|
| `payment.created` | Transaccion creada |
| `payment.captured` | Pago capturado (ledger afectado) |
| `payment.settled` | Pago liquidado |
| `payment.refunded` | Reembolso procesado |
| `payout.created` | Retiro solicitado |
| `wallet.created` | Wallet creado |
| `wallet.funded` | Fondos agregados |
| `wallet.transfer` | Transferencia entre wallets |
| `subscription.created` | Suscripcion iniciada |
| `ledger.entry.created` | Entrada de ledger posteada |

---

## Integracion con el Ecosistema

SavvyPay es consumido por TODAS las apps via `source_app`:

| App | Uso |
|-----|-----|
| SavvyPOS | Pagos de ventas |
| SavvyCredit | Desembolsos y cobros de prestamos |
| SavvyParking | Cobro de sesiones |
| SavvyCondo | Cobro de cuotas de administracion |
| SavvyHealth | Cobro de consultas y servicios |
| SavvyEdu | Cobro de matriculas |
| SavvyChurch | Diezmos y ofrendas |

---

## Consistencia y Confiabilidad

### Consistencia fuerte (CRITICO)

- Ledger entries
- Account balances (derivados)
- Transaction state transitions
- Wallet operations

### Consistencia eventual (aceptable)

- Notificaciones
- Analytics/dashboards
- Eventos de audit

---

## Endpoints API

Base: `/api/v1/pay/`

### Ledger
GET `/ledger/accounts`, POST `/ledger/accounts`
GET `/ledger/balances` — Saldos computados en tiempo real
POST `/ledger/journal` — Postear journal balanceado
GET `/ledger/entries` — Historial de movimientos
GET `/ledger/events` — Log de eventos

### Transactions
GET/POST `/transactions`
GET `/transactions/{id}`
POST `/transactions/{id}/transition` — State machine
POST `/transactions/refunds`

### Wallets
GET/POST `/wallets`
GET `/wallets/{id}/balance`
POST `/wallets/{id}/fund`
POST `/wallets/{id}/transfer`

### Fees
GET/POST `/fees/rules`
GET `/fees/calculate?amount=X&tx_type=Y`

### Payouts
GET/POST `/payouts`

### Subscriptions
GET/POST `/subscriptions/plans`
GET/POST `/subscriptions`

### Dashboard
GET `/dashboard/kpis`

---

## Frontend (8 vistas)

- Dashboard con 6 KPIs financieros (volumen, fees, wallets, payouts)
- Ledger: saldos por cuenta (derivados) + ultimos movimientos con journal/debit/credit
- Transacciones: lista con estado, tipo, metodo, app de origen
- Wallets: tarjetas con 4 saldos (available, pending, reserved, total)
- Fees: reglas configurables con tipo, porcentaje, minimo, aplica-a
- Payouts: lista con monto, fee, neto, metodo, estado
- Suscripciones: planes con precio/ciclo + suscripciones activas

---

> **Principio absoluto**: SavvyPay es la unica fuente de verdad financiera del ecosistema. Todo dinero que entra, sale, se mueve o se retiene pasa por el ledger. No hay excepciones.
