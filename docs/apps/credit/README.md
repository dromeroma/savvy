# SavvyCredit — Plataforma de Creditos y Prestamos

## Proposito

SavvyCredit es el **motor de creditos config-driven** del ecosistema Savvy. Soporta desde fiado de tienda hasta microfinanzas formales.

## Entidades (11 tablas)

| Tabla | Descripcion |
|-------|-------------|
| `credit_products` | Plantillas de productos crediticios configurables |
| `credit_product_fees` | Fees adicionales por producto |
| `credit_borrowers` | Prestatarios (extends People) con score, riesgo, stats |
| `credit_guarantors` | Garantes por prestamo |
| `credit_applications` | Solicitudes con workflow aprobacion |
| `credit_loans` | Prestamos con saldos, estado, proximos pagos |
| `credit_amortization` | Tabla de amortizacion (cuotas programadas) |
| `credit_disbursements` | Registros de desembolso |
| `credit_payments` | Pagos con asignacion (principal, interes, penalidad) |
| `credit_penalties` | Penalizaciones por mora |
| `credit_restructurings` | Refinanciaciones, condonaciones, castigos |

## CreditEngine

4 metodos de amortizacion con Decimal precision:
- **French** (cuota fija): PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
- **German** (amortizacion constante): P/n + interes decreciente
- **Flat** (interes sobre capital original): interes fijo por periodo
- **Bullet** (solo interes + balloon al final)

## Payment Allocation

Configurable por producto: `interest_first`, `principal_first`, `proportional`

## Loan Lifecycle

pending -> active -> current/delinquent -> paid_off/written_off/restructured

## Frontend (8 vistas)

Dashboard KPIs (cartera, mora, colocacion), productos, prestatarios, solicitudes con aprobacion, prestamos con desembolso, detalle con tabla amortizacion, pagos.
