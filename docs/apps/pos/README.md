# SavvyPOS — Cloud-First Point of Sale

## Proposito

SavvyPOS es el **punto de venta cloud** nativamente integrado al ecosistema Savvy. Conecta ventas, inventario, pagos (SavvyPay), contabilidad (SavvyAccounting) y clientes (SavvyCRM) en tiempo real.

> **Nota**: Existe un segundo POS en el ecosistema llamado **SavvyPOS LocalFirst** (`pos_local`) que es un producto independiente, orientado a zonas con internet inestable. Funciona offline y sincroniza cuando hay conexion. Este documento cubre solo el POS cloud del ecosistema.

## Entidades (11 tablas)

| Tabla | Descripcion |
|-------|-------------|
| `pos_locations` | Sucursales/tiendas |
| `pos_categories` | Categorias de productos con jerarquia |
| `pos_taxes` | Configuracion de impuestos (IVA, etc.) |
| `pos_products` | Productos con SKU, barcode, tipo, precio, costo |
| `pos_product_variants` | Variantes (talla, color, sabor, etc.) |
| `pos_inventory` | Stock materializado por producto/variant/sucursal |
| `pos_stock_movements` | Audit trail INMUTABLE de movimientos de stock |
| `pos_cash_registers` | Cajas con sesiones apertura/cierre + conciliacion |
| `pos_sales` | Transacciones de venta con lifecycle |
| `pos_sale_lines` | Lineas de venta con producto, cantidad, precio |
| `pos_discounts` | Descuentos/promociones configurables |

## Tipos de producto

- **simple**: producto basico con un solo precio
- **variant**: producto con variantes (Talla M/L/XL, Color rojo/azul)
- **bundle**: combo de varios productos
- **service**: servicio (no genera movimiento de inventario)
- **recipe**: receta (para restaurantes — futuro KDS)

## Flujo de Venta

```
1. Cashier abre caja (pos_cash_registers.status = 'open')
2. Agrega productos al carrito (POS terminal)
3. Checkout:
   a. Crea pos_sales + pos_sale_lines
   b. Por cada linea: pos_stock_movements (type='sale', qty negative)
   c. pos_inventory actualizado (materialized view)
   d. (futuro) Crea pay_transaction en SavvyPay
   e. (futuro) Crea journal_entry en SavvyAccounting
4. Venta completada: status='completed'
5. Anulacion: status='voided' + movimientos de return reversan stock
```

## Inventario con audit trail

El stock tiene dos capas:
- **`pos_inventory`**: vista materializada (performance) con cantidad actual
- **`pos_stock_movements`**: fuente de verdad inmutable (audit trail)

Cada cambio de stock crea un movimiento + actualiza el materialized. Tipos:
- `purchase`: compra a proveedor (+)
- `sale`: venta (-)
- `adjustment`: ajuste manual (+/-)
- `transfer_in` / `transfer_out`: transferencias entre sucursales
- `return`: devolucion (+)

## Cajas (cash registers)

Ciclo: **apertura** (con saldo inicial) → **operacion** (ventas) → **cierre** (conteo fisico)

Al cerrar se calcula:
- `expected_balance = opening_balance + SUM(ventas en efectivo)`
- `difference = closing_balance - expected_balance`

La diferencia indica sobrante/faltante para auditoria.

## Integracion con el ecosistema

| App | Integracion |
|-----|-------------|
| SavvyPay | Crea `pay_transactions` con source_app='pos' |
| SavvyAccounting | Via AccountingEngine para asientos contables |
| SavvyCRM | Los clientes son contactos CRM via `customer_person_id` |
| SavvyPeople | Los clientes son Persons |

## Frontend (8 vistas)

- **Dashboard** con 6 KPIs (ventas hoy, total, productos activos, stock bajo)
- **Terminal POS** — interfaz de caja con grid de productos y carrito lateral
- **Productos** — CRUD de catalogo con SKU, barcode, precio, costo
- **Inventario** — vista de stock por producto/sucursal con alertas de min_stock
- **Ventas** — historial con anulacion
- **Cajas** — apertura/cierre con calculo de diferencia
- **Sucursales** — CRUD de locations

## Endpoints API

Base: `/api/v1/pos/`

### Catalog
GET/POST `/locations`
GET/POST `/categories`
GET/POST `/products` · GET/PATCH `/products/{id}` · GET `/products/barcode/{barcode}`

### Inventory
GET `/inventory`
POST `/inventory/adjust`
GET `/inventory/movements`

### Sales
GET/POST `/sales` · GET `/sales/{id}` · POST `/sales/{id}/void`

### Registers
GET `/registers` · POST `/registers/open` · POST `/registers/{id}/close`

### Config
GET/POST `/config/taxes` · GET/POST `/config/discounts`

### Dashboard
GET `/dashboard/kpis`

---

## Diferencias con SavvyPOS LocalFirst

| | SavvyPOS (cloud) | SavvyPOS LocalFirst |
|---|---|---|
| **Mercado** | Negocios urbanos con conectividad | Zonas rurales, internet inestable |
| **Arquitectura** | Cloud-first, realtime | Local-first, sync offline |
| **Integracion** | Nativa con Pay, Accounting, CRM | Standalone autonomo |
| **Valor** | "Todo conectado" | "Nunca pierdes una venta" |
| **Code** | `pos` | `pos_local` |
| **is_external** | false (interno) | true (app externa) |

Son dos productos complementarios para dos segmentos de mercado distintos.
