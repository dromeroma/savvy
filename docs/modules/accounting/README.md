# SavvyAccounting — Motor Contable de Doble Partida

## Tabla de Contenidos

1. [Proposito](#proposito)
2. [Entidades del Modulo](#entidades-del-modulo)
3. [Plan de Cuentas](#plan-de-cuentas)
4. [Periodos Fiscales](#periodos-fiscales)
5. [Asientos Contables](#asientos-contables)
6. [AccountingEngine](#accountingengine)
7. [Reportes Financieros](#reportes-financieros)
8. [Integracion con SavvyFinance](#integracion-con-savvyfinance)
9. [Modos de Periodo Fiscal](#modos-de-periodo-fiscal)
10. [Endpoints API](#endpoints-api)

---

## Proposito

SavvyAccounting es el **motor contable de doble partida** compartido por todas las apps del ecosistema Savvy. Proporciona:

- **Plan de cuentas jerarquico** (activos, pasivos, patrimonio, ingresos, gastos).
- **Periodos fiscales** mensuales con apertura/cierre.
- **Asientos contables** con validacion de partida doble (debitos == creditos).
- **Reportes financieros** automaticos: Estado de Resultados y Balance General.

```
+--------------------------------------------------------------+
|                    SavvyAccounting                            |
|                                                              |
|  +-----------------+  +-----------------+  +--------------+  |
|  | Plan de Cuentas |  | Periodos        |  | Asientos     |  |
|  | (jerarquico)    |  | Fiscales        |  | Contables    |  |
|  +-----------------+  +-----------------+  +------+-------+  |
|                                                   |          |
|                                            +------v-------+  |
|                                            | Reportes:    |  |
|                                            | - Estado Res.|  |
|                                            | - Balance Grl|  |
|                                            +--------------+  |
+--------------------------------------------------------------+
|  Consumido por: SavvyFinance -> Church, Edu, POS, etc.       |
+--------------------------------------------------------------+
```

---

## Entidades del Modulo

| Entidad           | Tabla                  | Descripcion                                        |
|-------------------|------------------------|----------------------------------------------------|
| Cuenta Contable   | `chart_of_accounts`    | Catalogo jerarquico de cuentas (activo, pasivo, etc)|
| Periodo Fiscal    | `fiscal_periods`       | Periodo mensual con estado open/closed              |
| Asiento Contable  | `journal_entries`      | Cabecera del asiento (fecha, descripcion, fuente)   |
| Linea de Asiento  | `journal_entry_lines`  | Linea individual de debito o credito                |

---

## Plan de Cuentas

### Tabla `chart_of_accounts`

```sql
CREATE TABLE chart_of_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    code            VARCHAR(20) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    type            VARCHAR(20) NOT NULL,     -- asset, liability, equity, revenue, expense
    parent_id       UUID REFERENCES chart_of_accounts(id),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_system       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, code)
);
```

### Tipos de Cuenta

| Tipo       | Codigo  | Naturaleza | Ejemplo                     |
|------------|---------|------------|-----------------------------|
| `asset`    | 1xxx    | Debito     | Caja, Bancos, Cuentas x Cobrar |
| `liability`| 2xxx    | Credito    | Cuentas x Pagar, Prestamos  |
| `equity`   | 3xxx    | Credito    | Capital Social, Utilidades   |
| `revenue`  | 4xxx    | Credito    | Ingresos por Diezmos, Ventas |
| `expense`  | 5xxx    | Debito     | Gastos Generales, Nomina     |

### Jerarquia

El campo `parent_id` permite estructura de arbol:

```
1000 - Activos
  1100 - Activos Corrientes
    1101 - Caja General
    1102 - Bancos
    1103 - Cuentas por Cobrar
  1200 - Activos No Corrientes
    1201 - Muebles y Enseres
```

---

## Periodos Fiscales

### Tabla `fiscal_periods`

```sql
CREATE TABLE fiscal_periods (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    app_code        VARCHAR(30),              -- NULL = unified, 'church' = per-app
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'open',  -- open, closed
    closed_by       UUID REFERENCES users(id),
    closed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, year, month, app_code)
);
```

### Estados

```
open ---(cierre manual)---> closed
```

Un periodo cerrado no acepta nuevos asientos contables.

---

## Asientos Contables

### Tabla `journal_entries`

```sql
CREATE TABLE journal_entries (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id   UUID NOT NULL REFERENCES organizations(id),
    fiscal_period_id  UUID NOT NULL REFERENCES fiscal_periods(id),
    entry_number      INTEGER NOT NULL,
    date              DATE NOT NULL,
    description       TEXT NOT NULL,
    source_app        VARCHAR(30),             -- 'church', 'edu', 'pos'
    reference_type    VARCHAR(50),
    reference_id      UUID,
    status            VARCHAR(20) NOT NULL DEFAULT 'posted',
    created_by        UUID,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Tabla `journal_entry_lines`

```sql
CREATE TABLE journal_entry_lines (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id  UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id        UUID NOT NULL REFERENCES chart_of_accounts(id),
    debit             NUMERIC(15,2) NOT NULL DEFAULT 0,
    credit            NUMERIC(15,2) NOT NULL DEFAULT 0,
    description       TEXT
);
```

### Regla de Partida Doble

El `AccountingEngine` valida que **todo asiento cumpla**:

```
SUM(debitos) == SUM(creditos)
```

Si no cuadra, se rechaza con `ValidationError`.

---

## AccountingEngine

Servicio estatico centralizado en `src/modules/accounting/service.py`:

```python
class AccountingEngine:
    # Plan de Cuentas
    @staticmethod async def list_accounts(db, org_id)
    @staticmethod async def create_account(db, org_id, data)
    @staticmethod async def update_account(db, org_id, account_id, data)

    # Periodos Fiscales
    @staticmethod async def get_or_create_period(db, org_id, target_date, app_code=None)
    @staticmethod async def close_period(db, org_id, period_id, closed_by)

    # Asientos Contables
    @staticmethod async def create_entry(db, org_id, entry_date, description, created_by, lines)
    @staticmethod async def list_entries(db, org_id, period_id=None, source_app=None)
    @staticmethod async def get_entry(db, org_id, entry_id)

    # Reportes
    @staticmethod async def income_statement(db, org_id, start_date, end_date)
    @staticmethod async def balance_sheet(db, org_id, as_of_date)
```

### Flujo de Creacion de Asiento

```
1. App solicita crear asiento (via FinanceService o directamente)
2. AccountingEngine obtiene o crea el periodo fiscal para la fecha
3. Valida: SUM(debitos) == SUM(creditos)
4. Genera entry_number secuencial dentro del periodo
5. Guarda journal_entry + journal_entry_lines
6. Retorna el asiento creado
```

---

## Reportes Financieros

### Estado de Resultados (Income Statement)

```
GET /accounting/reports/income-statement?start_date=2026-01-01&end_date=2026-03-31
```

Calcula:
- **Ingresos**: SUM(credito - debito) de cuentas tipo `revenue`
- **Gastos**: SUM(debito - credito) de cuentas tipo `expense`
- **Utilidad Neta**: Ingresos - Gastos

### Balance General (Balance Sheet)

```
GET /accounting/reports/balance-sheet?as_of_date=2026-03-31
```

Calcula:
- **Activos**: SUM(debito - credito) de cuentas tipo `asset`
- **Pasivos**: SUM(credito - debito) de cuentas tipo `liability`
- **Patrimonio**: SUM(credito - debito) de cuentas tipo `equity` + Resultado del Ejercicio
- **Validacion**: Activos == Pasivos + Patrimonio

El Balance General incluye automaticamente la utilidad neta del periodo como parte del patrimonio ("Resultado del Ejercicio").

---

## Integracion con SavvyFinance

SavvyFinance es el consumidor principal de SavvyAccounting. Cada transaccion financiera genera un asiento contable:

```
SavvyFinance.create_transaction()
    |
    v
AccountingEngine.create_entry(
    lines = [
        {account: cuenta_pago,    debit: monto,  credit: 0},      # Ej: Caja
        {account: cuenta_ingreso, debit: 0,       credit: monto},  # Ej: Ingresos
    ]
)
```

Para egresos el flujo se invierte:

```
    lines = [
        {account: cuenta_gasto,  debit: monto,  credit: 0},      # Ej: Gastos
        {account: cuenta_pago,   debit: 0,       credit: monto},  # Ej: Bancos
    ]
```

---

## Modos de Periodo Fiscal

La organizacion puede configurar `settings.fiscal_period_mode`:

| Modo       | Comportamiento                                     |
|------------|-----------------------------------------------------|
| `unified`  | Un solo set de periodos para toda la org             |
| `per_app`  | Cada app (church, edu, pos) tiene sus propios periodos |

Con `per_app`, una iglesia puede cerrar el periodo de enero para contabilidad sin afectar el periodo de enero de educacion.

---

## Endpoints API

### Plan de Cuentas

| Metodo | Ruta                              | Descripcion                    |
|--------|-----------------------------------|--------------------------------|
| GET    | `/accounting/chart`               | Listar cuentas                 |
| POST   | `/accounting/chart`               | Crear cuenta                   |
| PATCH  | `/accounting/chart/{id}`          | Actualizar cuenta              |

### Periodos Fiscales

| Metodo | Ruta                              | Descripcion                    |
|--------|-----------------------------------|--------------------------------|
| GET    | `/accounting/periods`             | Listar periodos                |
| POST   | `/accounting/periods/{id}/close`  | Cerrar periodo                 |

### Asientos Contables

| Metodo | Ruta                              | Descripcion                    |
|--------|-----------------------------------|--------------------------------|
| GET    | `/accounting/journal`             | Listar asientos                |
| POST   | `/accounting/journal`             | Crear asiento                  |
| GET    | `/accounting/journal/{id}`        | Obtener asiento con lineas     |

### Reportes

| Metodo | Ruta                                            | Descripcion                    |
|--------|-------------------------------------------------|--------------------------------|
| GET    | `/accounting/reports/income-statement`           | Estado de resultados           |
| GET    | `/accounting/reports/balance-sheet`              | Balance general                |

---

> **Principio clave**: SavvyAccounting no sabe de diezmos, ventas ni matriculas. Solo sabe de cuentas, debitos, creditos y periodos. Las apps le dan contexto a traves de `source_app` y `reference_type/reference_id` en los asientos.
