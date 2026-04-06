# SavvyFinance — Motor de Transacciones Financieras

## Tabla de Contenidos

1. [Proposito](#proposito)
2. [Entidades del Modulo](#entidades-del-modulo)
3. [Categorias Financieras](#categorias-financieras)
4. [Transacciones](#transacciones)
5. [Cuentas de Pago](#cuentas-de-pago)
6. [Integracion con Accounting](#integracion-con-accounting)
7. [Seeders por Tipo de Negocio](#seeders-por-tipo-de-negocio)
8. [Endpoints API](#endpoints-api)
9. [Como SavvyChurch usa SavvyFinance](#como-savvychurch-usa-savvyfinance)
10. [Como SavvyPOS usara SavvyFinance](#como-savvypos-usara-savvyfinance)

---

## Proposito

SavvyFinance es el **motor generico de ingresos y egresos** compartido por todas las apps del ecosistema. No contiene logica de negocio especifica (no sabe que es un diezmo ni una venta), sino que provee:

- **Categorias configurables** por tipo de app.
- **Registro de transacciones** con trazabilidad completa.
- **Integracion automatica con contabilidad** (journal entries).
- **Cuentas de pago configurables** que mapean metodos de pago a cuentas contables.

```
+--------------------------------------------------------------+
|                     SavvyFinance                             |
|                                                              |
|  +--------------+    +------------------+    +-----------+   |
|  | Categorias   |    | Transacciones    |    | Cuentas   |   |
|  | (por app)    |--->| (income/expense) |--->| de Pago   |   |
|  +--------------+    +--------+---------+    +-----------+   |
|                               |                              |
|                               v                              |
|                     +-----------------+                      |
|                     | SavvyAccounting |                      |
|                     | (journal_entry) |                      |
|                     +-----------------+                      |
+--------------------------------------------------------------+
|                                                              |
|  Apps consumidoras:                                          |
|  [Church] [POS] [HR] [CRM] [Futuras...]                     |
+--------------------------------------------------------------+
```

---

## Entidades del Modulo

| Entidad              | Tabla                       | Descripcion                                         |
|----------------------|-----------------------------|-----------------------------------------------------|
| Categoria Financiera | `finance_categories`        | Clasificacion de ingresos/egresos por app           |
| Transaccion          | `finance_transactions`      | Registro individual de ingreso o egreso             |
| Cuenta de Pago       | `finance_payment_accounts`  | Mapeo: metodo de pago -> cuenta contable            |

---

## Categorias Financieras

### Tabla `finance_categories`

```sql
CREATE TABLE finance_categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    app_code        VARCHAR(30) NOT NULL,        -- 'church', 'pos', 'hr', 'general'
    code            VARCHAR(50) NOT NULL,         -- 'TITHE', 'OFFERING', 'SALE', 'PURCHASE'
    name            VARCHAR(100) NOT NULL,        -- 'Diezmo', 'Ofrenda', 'Venta', 'Compra'
    type            VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    description     TEXT,
    account_id      UUID REFERENCES chart_of_accounts(id),  -- Cuenta contable asociada
    is_system       BOOLEAN DEFAULT FALSE,        -- No editable por usuario
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (organization_id, app_code, code)
);

CREATE INDEX idx_finance_cat_org ON finance_categories(organization_id);
CREATE INDEX idx_finance_cat_app ON finance_categories(organization_id, app_code);
```

### Categorias por App

Las categorias son **especificas por app_code**, lo que permite que cada aplicacion tenga su propio catalogo de tipos de ingreso/egreso:

```
+-------------------------------------------------------------------+
|  app_code = 'church'                                              |
|  +----------+-----------+----------+-----------------------------+|
|  | Code     | Nombre    | Tipo     | Cuenta Contable             ||
|  +----------+-----------+----------+-----------------------------+|
|  | TITHE    | Diezmo    | income   | 4101 - Ingresos por Diezmos ||
|  | OFFERING | Ofrenda   | income   | 4102 - Ingresos por Ofrendas||
|  | SEED     | Siembra   | income   | 4103 - Ingresos por Siembras||
|  | SPECIAL  | Ofrenda E.| income   | 4104 - Ofrendas Especiales  ||
|  | EXPENSE  | Gasto Gral| expense  | 5101 - Gastos Generales     ||
|  | SALARY   | Salarios  | expense  | 5201 - Gastos de Nomina     ||
|  | RENT     | Arriendo  | expense  | 5301 - Gastos de Arriendo   ||
|  | UTILITY  | Servicios | expense  | 5302 - Servicios Publicos   ||
|  +----------+-----------+----------+-----------------------------+|
+-------------------------------------------------------------------+

+-------------------------------------------------------------------+
|  app_code = 'pos'                                                 |
|  +----------+-----------+----------+-----------------------------+|
|  | Code     | Nombre    | Tipo     | Cuenta Contable             ||
|  +----------+-----------+----------+-----------------------------+|
|  | SALE     | Venta     | income   | 4201 - Ingresos por Ventas  ||
|  | RETURN   | Devolucion| expense  | 4202 - Devoluciones         ||
|  | PURCHASE | Compra    | expense  | 5401 - Compras de Mercancia ||
|  | SHIPPING | Envio     | expense  | 5402 - Gastos de Envio      ||
|  +----------+-----------+----------+-----------------------------+|
+-------------------------------------------------------------------+
```

---

## Transacciones

### Tabla `finance_transactions`

```sql
CREATE TABLE finance_transactions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id   UUID NOT NULL REFERENCES organizations(id),
    scope_id          UUID NOT NULL REFERENCES organizational_scopes(id),

    -- Clasificacion
    category_id       UUID NOT NULL REFERENCES finance_categories(id),
    type              VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    app_code          VARCHAR(30) NOT NULL,        -- Redundante pero util para filtrado rapido

    -- Monto
    amount            DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    currency          VARCHAR(3) DEFAULT 'USD',

    -- Metodo de pago
    payment_method    VARCHAR(30) NOT NULL CHECK (payment_method IN (
        'cash', 'bank_transfer', 'credit_card', 'debit_card',
        'check', 'mobile_payment', 'crypto', 'other'
    )),

    -- Persona asociada (opcional)
    person_id         UUID REFERENCES people(id),

    -- Referencia a entidad origen (polimorfismo)
    reference_type    VARCHAR(50),     -- 'church_activity', 'pos_order', 'hr_payroll'
    reference_id      UUID,            -- ID de la entidad en la app origen

    -- Datos adicionales
    description       TEXT,
    transaction_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    receipt_number    VARCHAR(50),
    notes             TEXT,
    metadata          JSONB DEFAULT '{}',

    -- Contabilidad
    journal_entry_id  UUID REFERENCES journal_entries(id),  -- Vinculo al asiento contable

    -- Auditoria
    created_by        UUID REFERENCES auth.users(id),
    status            VARCHAR(20) DEFAULT 'confirmed'
                      CHECK (status IN ('pending', 'confirmed', 'voided', 'reconciled')),
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fin_tx_org ON finance_transactions(organization_id);
CREATE INDEX idx_fin_tx_scope ON finance_transactions(scope_id);
CREATE INDEX idx_fin_tx_category ON finance_transactions(category_id);
CREATE INDEX idx_fin_tx_type ON finance_transactions(organization_id, type);
CREATE INDEX idx_fin_tx_app ON finance_transactions(organization_id, app_code);
CREATE INDEX idx_fin_tx_person ON finance_transactions(person_id);
CREATE INDEX idx_fin_tx_date ON finance_transactions(organization_id, transaction_date);
CREATE INDEX idx_fin_tx_reference ON finance_transactions(reference_type, reference_id);
CREATE INDEX idx_fin_tx_journal ON finance_transactions(journal_entry_id);
```

### Campos Clave

| Campo            | Descripcion                                                                     |
|------------------|---------------------------------------------------------------------------------|
| `category_id`    | Vinculo a la categoria (TITHE, SALE, etc.) que determina la cuenta contable     |
| `type`           | `income` o `expense` — redundante con categoria pero facilita consultas         |
| `app_code`       | Identifica que app origino la transaccion. Permite filtrado rapido              |
| `person_id`      | Persona asociada (quien pago el diezmo, a quien se le vendio)                   |
| `reference_type` | Tipo de entidad origen en la app (tabla fuente). Permite trazabilidad           |
| `reference_id`   | ID de la entidad origen. Junto con reference_type, forman un enlace polimorfico |
| `payment_method`  | Como se pago/cobro                                                             |
| `journal_entry_id`| Vinculo al asiento contable generado automaticamente                           |

### Referencia Polimorfica

Los campos `reference_type` y `reference_id` permiten rastrear el **origen** de cada transaccion sin acoplar SavvyFinance a ninguna app especifica:

```
+-------------------------------+--------------------+---------------------------+
| App          | reference_type | reference_id               | Significado        |
+-------------------------------+--------------------+---------------------------+
| SavvyChurch  | church_activity| UUID de la actividad       | Ofrenda de un culto|
| SavvyPOS     | pos_order      | UUID de la orden de venta  | Pago de una venta  |
| SavvyHR      | hr_payroll     | UUID de la nomina          | Pago de salario    |
+-------------------------------+--------------------+---------------------------+
```

---

## Cuentas de Pago

### Tabla `finance_payment_accounts`

Esta tabla define **que cuenta contable se usa para cada metodo de pago**. Permite que el sistema genere asientos contables correctos automaticamente:

```sql
CREATE TABLE finance_payment_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    payment_method  VARCHAR(30) NOT NULL,
    account_id      UUID NOT NULL REFERENCES chart_of_accounts(id),
    name            VARCHAR(100) NOT NULL,     -- 'Caja General', 'Banco Nacional'
    description     TEXT,
    is_default      BOOLEAN DEFAULT FALSE,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (organization_id, payment_method, account_id)
);
```

### Configuracion Tipica

```
+-------------------------------------------------------------------+
| Metodo de Pago     | Cuenta Contable          | Nombre           |
+--------------------+--------------------------+------------------+
| cash               | 1101 - Caja General      | Caja General     |
| bank_transfer      | 1102 - Bancos            | Banco Nacional   |
| credit_card        | 1103 - Cuentas por Cobrar| Datáfono VISA    |
| debit_card         | 1102 - Bancos            | Datáfono débito  |
| check              | 1104 - Cheques por Cobrar| Cheques recibidos|
| mobile_payment     | 1105 - Pagos Digitales   | Nequi/Daviplata  |
+-------------------------------------------------------------------+
```

### Uso en la Generacion de Asientos

Cuando se registra una transaccion:

```
Transaccion: Diezmo de $500,000 en efectivo

1. Categoria: TITHE -> Cuenta 4101 (Ingresos por Diezmos)
2. Metodo de pago: cash -> Cuenta 1101 (Caja General)

Asiento contable generado:
+---------------------------+----------+----------+
| Cuenta                    | Debito   | Credito  |
+---------------------------+----------+----------+
| 1101 - Caja General      | 500,000  |          |
| 4101 - Ingresos Diezmos  |          | 500,000  |
+---------------------------+----------+----------+
```

---

## Integracion con Accounting

### Flujo: Transaction -> Journal Entry

```
+-------------------+        +--------------------+        +------------------+
| finance_transaction|  --->  | Motor de Asientos  |  --->  | journal_entries   |
| (SavvyFinance)    |        | (SavvyAccounting)  |        | journal_entry_    |
|                   |        |                    |        | lines             |
+-------------------+        +--------------------+        +------------------+

Flujo detallado:
================================================================

1. App crea transaccion financiera
   POST /finance/transactions
   {
     category_id: "uuid-tithe",
     amount: 500000,
     payment_method: "cash",
     person_id: "uuid-juan",
     ...
   }

2. SavvyFinance guarda la transaccion

3. SavvyFinance busca las cuentas contables:
   a. Cuenta de ingreso/gasto: finance_categories.account_id
      -> 4101 (Ingresos por Diezmos)
   b. Cuenta de pago: finance_payment_accounts WHERE payment_method = 'cash'
      -> 1101 (Caja General)

4. SavvyFinance llama a SavvyAccounting para crear el asiento:
   accounting_service.create_journal_entry({
     transaction_date: "2026-04-04",
     description: "Diezmo - Juan Perez",
     reference_type: "finance_transaction",
     reference_id: "uuid-transaccion",
     lines: [
       { account_id: "uuid-1101", debit: 500000, credit: 0 },
       { account_id: "uuid-4101", debit: 0, credit: 500000 }
     ]
   })

5. SavvyAccounting valida partida doble (debitos == creditos)

6. SavvyAccounting guarda el journal_entry y retorna el ID

7. SavvyFinance actualiza finance_transactions.journal_entry_id

================================================================
```

### Casos Especiales

**Transaccion con impuestos (futuro POS)**:

```
Venta de $100,000 + IVA 19% = $119,000 en tarjeta de credito

Asiento:
+--------------------------------+----------+----------+
| Cuenta                         | Debito   | Credito  |
+--------------------------------+----------+----------+
| 1103 - CxC Tarjetas           | 119,000  |          |
| 4201 - Ingresos por Ventas    |          | 100,000  |
| 2401 - IVA por Pagar          |          |  19,000  |
+--------------------------------+----------+----------+
```

**Gasto con retencion (futuro)**:

```
Pago de arriendo $1,000,000 - Retencion 3.5% = $965,000 transferencia

Asiento:
+--------------------------------+-----------+----------+
| Cuenta                         | Debito    | Credito  |
+--------------------------------+-----------+----------+
| 5301 - Gastos de Arriendo     | 1,000,000 |          |
| 1102 - Bancos                 |           | 965,000  |
| 2365 - Retencion en la Fuente |           |  35,000  |
+--------------------------------+-----------+----------+
```

---

## Seeders por Tipo de Negocio

Al crear una organizacion, se ejecutan seeders que crean las categorias financieras y cuentas de pago segun el tipo de negocio:

### Seeder: Iglesia (`church`)

```python
CHURCH_FINANCE_SEED = {
    "categories": [
        # Ingresos
        {"code": "TITHE",      "name": "Diezmo",             "type": "income"},
        {"code": "OFFERING",   "name": "Ofrenda",            "type": "income"},
        {"code": "SEED",       "name": "Siembra",            "type": "income"},
        {"code": "SPECIAL",    "name": "Ofrenda Especial",   "type": "income"},
        {"code": "DONATION",   "name": "Donacion",           "type": "income"},
        {"code": "EVENT",      "name": "Evento",             "type": "income"},
        # Egresos
        {"code": "SALARY",     "name": "Salarios",           "type": "expense"},
        {"code": "RENT",       "name": "Arriendo",           "type": "expense"},
        {"code": "UTILITY",    "name": "Servicios Publicos", "type": "expense"},
        {"code": "SUPPLY",     "name": "Insumos",            "type": "expense"},
        {"code": "MAINTENANCE","name": "Mantenimiento",      "type": "expense"},
        {"code": "MISSION",    "name": "Misiones",           "type": "expense"},
        {"code": "BENEVOLENCE","name": "Benevolencia",       "type": "expense"},
        {"code": "OTHER_EXP",  "name": "Otros Gastos",       "type": "expense"},
    ],
    "payment_accounts": [
        {"payment_method": "cash",          "name": "Caja General"},
        {"payment_method": "bank_transfer", "name": "Banco Principal"},
        {"payment_method": "mobile_payment","name": "Pagos Digitales"},
    ]
}
```

### Seeder: Punto de Venta (`pos` / `retail`)

```python
RETAIL_FINANCE_SEED = {
    "categories": [
        # Ingresos
        {"code": "SALE",           "name": "Venta",               "type": "income"},
        {"code": "SERVICE",        "name": "Servicio",            "type": "income"},
        {"code": "INTEREST",       "name": "Intereses Cobrados",  "type": "income"},
        # Egresos
        {"code": "PURCHASE",       "name": "Compra de Mercancia", "type": "expense"},
        {"code": "RETURN",         "name": "Devolucion",          "type": "expense"},
        {"code": "SHIPPING",       "name": "Envio",               "type": "expense"},
        {"code": "SALARY",         "name": "Nomina",              "type": "expense"},
        {"code": "RENT",           "name": "Arriendo",            "type": "expense"},
        {"code": "UTILITY",        "name": "Servicios Publicos",  "type": "expense"},
        {"code": "TAX",            "name": "Impuestos",           "type": "expense"},
        {"code": "MARKETING",      "name": "Marketing",           "type": "expense"},
        {"code": "OTHER_EXP",      "name": "Otros Gastos",        "type": "expense"},
    ],
    "payment_accounts": [
        {"payment_method": "cash",          "name": "Caja Registradora"},
        {"payment_method": "bank_transfer", "name": "Banco Comercial"},
        {"payment_method": "credit_card",   "name": "Datafono Credito"},
        {"payment_method": "debit_card",    "name": "Datafono Debito"},
        {"payment_method": "mobile_payment","name": "Pagos Digitales"},
    ]
}
```

---

## Endpoints API

### Categorias

| Metodo | Ruta                                 | Descripcion                              |
|--------|--------------------------------------|------------------------------------------|
| GET    | `/finance/categories`                | Listar categorias (filtro por app_code)  |
| POST   | `/finance/categories`                | Crear categoria personalizada            |
| PATCH  | `/finance/categories/{id}`           | Actualizar categoria                     |
| DELETE | `/finance/categories/{id}`           | Desactivar categoria                     |

### Transacciones

| Metodo | Ruta                                 | Descripcion                              |
|--------|--------------------------------------|------------------------------------------|
| GET    | `/finance/transactions`              | Listar transacciones (paginado, filtros) |
| POST   | `/finance/transactions`              | Registrar transaccion                    |
| GET    | `/finance/transactions/{id}`         | Obtener transaccion con asiento contable |
| PATCH  | `/finance/transactions/{id}`         | Actualizar transaccion (solo pending)    |
| POST   | `/finance/transactions/{id}/void`    | Anular transaccion                       |

### Cuentas de Pago

| Metodo | Ruta                                 | Descripcion                              |
|--------|--------------------------------------|------------------------------------------|
| GET    | `/finance/payment-accounts`          | Listar cuentas de pago                   |
| POST   | `/finance/payment-accounts`          | Crear cuenta de pago                     |
| PATCH  | `/finance/payment-accounts/{id}`     | Actualizar cuenta de pago                |
| DELETE | `/finance/payment-accounts/{id}`     | Desactivar cuenta de pago                |

### Reportes

| Metodo | Ruta                                       | Descripcion                                   |
|--------|-------------------------------------------|-----------------------------------------------|
| GET    | `/finance/reports/summary`                 | Resumen: total ingresos vs egresos por periodo|
| GET    | `/finance/reports/by-category`             | Desglose por categoria                        |
| GET    | `/finance/reports/by-person`               | Transacciones por persona                     |
| GET    | `/finance/reports/by-payment-method`       | Desglose por metodo de pago                   |

### Parametros de Consulta

```
GET /finance/transactions?app_code=church&type=income&scope_id=uuid&date_from=2026-01-01&date_to=2026-03-31&page=1&limit=50
GET /finance/reports/summary?scope_id=uuid&period=monthly&year=2026
```

---

## Como SavvyChurch usa SavvyFinance

### Registro de Diezmo

```python
# El pastor registra un diezmo durante el culto

async def register_tithe(
    scope_id: UUID,          # Iglesia
    person_id: UUID,         # Congregante que diezma
    amount: Decimal,
    payment_method: str,
    activity_id: UUID        # Actividad/culto donde se recibio
):
    tithe_category = await finance_service.get_category(
        app_code="church", code="TITHE"
    )

    transaction = await finance_service.create_transaction(
        scope_id=scope_id,
        category_id=tithe_category.id,
        type="income",
        app_code="church",
        amount=amount,
        payment_method=payment_method,
        person_id=person_id,
        reference_type="church_activity",
        reference_id=activity_id,
        description=f"Diezmo - Culto dominical"
    )

    # SavvyFinance automaticamente crea el asiento contable
    # transaction.journal_entry_id ya esta vinculado

    return transaction
```

### Reporte de Diezmos por Congregante

```python
# El pastor quiere ver cuanto ha diezmado cada persona este año

GET /finance/reports/by-person?app_code=church&category_code=TITHE&year=2026&scope_id=uuid

Response:
{
  "period": "2026",
  "category": "TITHE",
  "data": [
    {"person": {"id": "...", "name": "Juan Perez"},   "total": 6000000, "count": 12},
    {"person": {"id": "...", "name": "Maria Lopez"},   "total": 3600000, "count": 12},
    {"person": {"id": "...", "name": "Carlos Gomez"},  "total": 2400000, "count": 8}
  ],
  "grand_total": 12000000
}
```

### Diezmo del Diezmo

Las iglesias que pertenecen a una denominacion deben aportar un porcentaje de sus ingresos al nivel superior. SavvyFinance facilita este calculo:

```python
async def calculate_tithe_of_tithe(
    scope_id: UUID,
    period_start: date,
    period_end: date,
    percentage: Decimal = Decimal("0.10")  # 10%
) -> dict:
    """
    Calcula el diezmo del diezmo: porcentaje sobre diezmos + ofrendas.
    """
    # Obtener total de categorias TITHE + OFFERING del periodo
    categories = await finance_service.get_categories(
        app_code="church",
        codes=["TITHE", "OFFERING"]
    )

    total = await finance_service.sum_transactions(
        scope_id=scope_id,
        category_ids=[c.id for c in categories],
        date_from=period_start,
        date_to=period_end
    )

    return {
        "period": f"{period_start} - {period_end}",
        "total_tithes_and_offerings": total,
        "percentage": percentage,
        "amount_due": total * percentage
    }
```

---

## Como SavvyPOS usara SavvyFinance

### Registro de Venta

```python
# El sistema POS registra una venta completada

async def register_sale(
    scope_id: UUID,          # Sucursal
    person_id: UUID,         # Cliente (opcional)
    order_id: UUID,          # Orden de venta
    amount: Decimal,
    payment_method: str
):
    sale_category = await finance_service.get_category(
        app_code="pos", code="SALE"
    )

    transaction = await finance_service.create_transaction(
        scope_id=scope_id,
        category_id=sale_category.id,
        type="income",
        app_code="pos",
        amount=amount,
        payment_method=payment_method,
        person_id=person_id,
        reference_type="pos_order",
        reference_id=order_id,
        description=f"Venta #{order_id[:8]}"
    )

    return transaction
```

### Registro de Compra de Inventario

```python
async def register_purchase(
    scope_id: UUID,
    supplier_id: UUID,       # Proveedor (es una persona en people)
    purchase_order_id: UUID,
    amount: Decimal,
    payment_method: str
):
    purchase_category = await finance_service.get_category(
        app_code="pos", code="PURCHASE"
    )

    transaction = await finance_service.create_transaction(
        scope_id=scope_id,
        category_id=purchase_category.id,
        type="expense",
        app_code="pos",
        amount=amount,
        payment_method=payment_method,
        person_id=supplier_id,
        reference_type="pos_purchase_order",
        reference_id=purchase_order_id,
        description=f"Compra de mercancia"
    )

    return transaction
```

---

> **Principio clave**: SavvyFinance no sabe que es un diezmo ni una venta. Solo sabe registrar transacciones clasificadas por categorias configurables y generar asientos contables. Las apps le dan contexto semantico a traves de `app_code`, `category_id` y `reference_type/reference_id`.
