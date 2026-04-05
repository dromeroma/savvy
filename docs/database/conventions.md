# Convenciones de Base de Datos

---

## Resumen

Este documento establece las convenciones que toda tabla, columna, indice y migracion en SavvyCore debe seguir. Son obligatorias para mantener consistencia en todo el proyecto.

---

## Naming (Nomenclatura)

### Tablas

| Regla | Ejemplo correcto | Ejemplo incorrecto |
|-------|-----------------|-------------------|
| Plural, snake_case | `organizations` | `Organization`, `org` |
| Sustantivos, no verbos | `invitations` | `invite_users` |
| Sin prefijos de modulo | `products` | `pos_products` |
| Tablas de relacion: ambas entidades | `user_roles` | `assignments` |

### Columnas

| Regla | Ejemplo correcto | Ejemplo incorrecto |
|-------|-----------------|-------------------|
| Singular, snake_case | `organization_id` | `OrganizationId`, `orgId` |
| Foreign keys: `tabla_singular_id` | `user_id` | `userId`, `fk_user` |
| Booleanos: prefijo `is_` o `has_` | `is_active`, `has_discount` | `active`, `discount` |
| Fechas: sufijo `_at` | `created_at`, `expires_at` | `creation_date`, `expiry` |
| Contadores: sufijo `_count` | `login_count` | `logins`, `num_logins` |

### Indices

| Regla | Formato | Ejemplo |
|-------|---------|---------|
| Indice regular | `idx_{tabla}_{columnas}` | `idx_products_tenant_id` |
| Indice unico | `idx_{tabla}_{columnas}` (con UNIQUE) | `idx_users_email` |
| Indice parcial | `idx_{tabla}_{columnas}` (con WHERE) | `idx_invitations_email_status` |
| Indice compuesto | `idx_{tabla}_{col1}_{col2}` | `idx_memberships_org_user` |

### Constraints

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Primary key | Implicito por `PRIMARY KEY` | `organizations_pkey` |
| Foreign key | `fk_{tabla}_{columna}` | `fk_memberships_organization_id` |
| Check | `chk_{tabla}_{columna}` | `chk_memberships_role` |
| Unique | Via indice unico | `idx_users_email` |

---

## Primary Keys

### Regla: UUID para todas las PKs

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

| Criterio | UUID | Auto-increment (SERIAL) |
|----------|------|------------------------|
| Seguridad | No predecible | Predecible (enumerable) |
| Distribucion | Funciona con sharding | Conflictos en multi-BD |
| Generacion | Client-side o server-side | Solo server-side |
| Tamano | 16 bytes | 4-8 bytes |
| Rendimiento indice | Ligeramente menor (random) | Optimo (secuencial) |
| URLs amigables | No (pero usamos slugs) | No |

**Decision**: UUID por seguridad y preparacion para distribucion futura. El impacto en rendimiento de indices es negligible para nuestro volumen.

**Funcion**: Usamos `gen_random_uuid()` de PostgreSQL (extension `pgcrypto`) que genera UUID v4 aleatorios.

---

## tenant_id

### Regla: Toda tabla de datos de negocio debe incluir tenant_id

```sql
tenant_id UUID NOT NULL REFERENCES organizations(id)
```

**Excepciones** (tablas sin tenant_id):
- `organizations` -- Es la tabla de tenants.
- `users` -- Un usuario puede pertenecer a multiples orgs.
- `refresh_tokens` -- Pertenecen al usuario, no al tenant.

**Tablas que SI requieren tenant_id** (ejemplos futuros):
- `products`, `orders`, `customers` -- Datos de negocio de la app.
- `settings`, `audit_logs` -- Datos operativos por org.

### Posicion de la columna

`tenant_id` siempre va como la **segunda columna** despues de `id`:

```sql
CREATE TABLE products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES organizations(id),  -- Siempre segunda
    name        VARCHAR(255) NOT NULL,
    ...
);
```

---

## Timestamps

### Regla: Toda tabla incluye created_at y updated_at

```sql
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

| Campo | Tipo | Obligatorio | Default | Actualizado por |
|-------|------|-------------|---------|-----------------|
| `created_at` | TIMESTAMPTZ | Si | `NOW()` | Nunca (inmutable) |
| `updated_at` | TIMESTAMPTZ | Si | `NOW()` | Trigger automatico |
| `deleted_at` | TIMESTAMPTZ | No | `NULL` | Aplicacion (soft delete) |

### Tipo de dato: TIMESTAMPTZ

Siempre usar `TIMESTAMPTZ` (con timezone), nunca `TIMESTAMP` (sin timezone):

```sql
-- CORRECTO: almacena el instante absoluto en UTC
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

-- INCORRECTO: ambiguo, depende del timezone del servidor
created_at TIMESTAMP NOT NULL DEFAULT NOW()
```

### Trigger para updated_at

Toda tabla con `updated_at` debe tener este trigger:

```sql
CREATE TRIGGER trg_{tabla}_updated_at
    BEFORE UPDATE ON {tabla}
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

La funcion `update_updated_at_column()` se define una sola vez en la migracion base.

---

## Soft Deletes

### Regla: Usar soft delete para datos de negocio importantes

```sql
deleted_at TIMESTAMPTZ DEFAULT NULL
```

**Tablas con soft delete**: `organizations`, `users`
**Tablas sin soft delete**: `memberships`, `refresh_tokens`, `invitations`

### Reglas de soft delete

1. Los queries normales deben filtrar `WHERE deleted_at IS NULL`.
2. Los indices unicos deben ser parciales: `WHERE deleted_at IS NULL`.
3. Nunca hacer `DELETE FROM` en tablas con soft delete. Siempre `UPDATE SET deleted_at = NOW()`.
4. Tener un job periodico para purgar registros con `deleted_at` mayor a 30 dias (configurable).

---

## Indices

### Reglas generales

1. **Toda FK** debe tener un indice (PostgreSQL no los crea automaticamente).
2. **tenant_id** debe ser el primer campo en indices compuestos de tablas con datos de negocio.
3. **Preferir indices parciales** cuando sea posible (`WHERE deleted_at IS NULL`).
4. **No crear indices preventivos** -- Solo crear indices que se necesiten para queries reales.

### Patrones comunes

```sql
-- FK simple
CREATE INDEX idx_{tabla}_{fk_column} ON {tabla}({fk_column});

-- Busqueda por tenant + campo frecuente
CREATE INDEX idx_{tabla}_tenant_{campo} ON {tabla}(tenant_id, {campo});

-- Busqueda con filtro de activos
CREATE INDEX idx_{tabla}_tenant_{campo}_active
    ON {tabla}(tenant_id, {campo})
    WHERE deleted_at IS NULL;

-- Ordenamiento por tenant + fecha
CREATE INDEX idx_{tabla}_tenant_created
    ON {tabla}(tenant_id, created_at DESC);
```

---

## Migraciones

### Reglas

1. **Nunca modificar** una migracion ya aplicada en produccion.
2. **Una migracion por cambio logico** (no agrupar cambios no relacionados).
3. **Toda migracion debe ser reversible** (incluir el DOWN).
4. **Nombrar migraciones descriptivamente**: `0001_create_organizations.sql`, `0002_create_users.sql`.
5. **Probar en un entorno limpio** antes de aplicar en produccion.

### Formato de nombre

```
{numero_secuencial}_{accion}_{tabla_o_descripcion}.sql

Ejemplos:
  0001_create_organizations.sql
  0002_create_users.sql
  0003_create_memberships.sql
  0004_add_email_verified_to_users.sql
  0005_create_products.sql
```

### Estructura de migracion

```sql
-- UP
-- Descripcion: Crear tabla products
-- Fecha: 2026-03-28

CREATE TABLE products (
    ...
);

-- DOWN
DROP TABLE IF EXISTS products;
```

---

## Tipos de datos recomendados

| Dato | Tipo PostgreSQL | Notas |
|------|----------------|-------|
| Identificadores | `UUID` | `gen_random_uuid()` |
| Nombres, textos cortos | `VARCHAR(N)` | Especificar longitud maxima |
| Textos largos | `TEXT` | Sin limite |
| Email | `VARCHAR(255)` | Con indice unico parcial |
| Dinero | `DECIMAL(12,2)` | Nunca usar FLOAT |
| Cantidades enteras | `INTEGER` | O `BIGINT` si puede superar 2 billones |
| Booleanos | `BOOLEAN` | `DEFAULT false` |
| Fechas/horas | `TIMESTAMPTZ` | Siempre con timezone |
| Solo fecha | `DATE` | Sin componente de hora |
| JSON | `JSONB` | Indexable, no usar `JSON` |
| Enums cortos | `VARCHAR(20)` con `CHECK` | Preferir CHECK sobre CREATE TYPE |
| IPs | `VARCHAR(45)` | Soporta IPv4 e IPv6 |
| URLs | `VARCHAR(2048)` | Longitud maxima de URL |

### Por que VARCHAR + CHECK en lugar de CREATE TYPE (ENUM)

```sql
-- PREFERIDO: flexible, facil de modificar
role VARCHAR(20) CHECK (role IN ('owner', 'admin', 'member'))

-- EVITAR: dificil agregar valores, requiere ALTER TYPE
CREATE TYPE role_enum AS ENUM ('owner', 'admin', 'member');
role role_enum NOT NULL
```

Los `CHECK` constraints son mas faciles de modificar en migraciones que los `ENUM` types de PostgreSQL.

---

## Checklist para nueva tabla

Al crear una nueva tabla, verificar:

- [ ] `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- [ ] `tenant_id UUID NOT NULL REFERENCES organizations(id)` (si aplica)
- [ ] `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- [ ] `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- [ ] `deleted_at TIMESTAMPTZ DEFAULT NULL` (si aplica soft delete)
- [ ] Trigger `trg_{tabla}_updated_at` para `updated_at`
- [ ] Indice en `tenant_id`
- [ ] Indices en todas las foreign keys
- [ ] Indices parciales con `WHERE deleted_at IS NULL` si aplica
- [ ] RLS habilitado con politica de aislamiento por tenant (si tiene tenant_id)
- [ ] Migracion con nombre descriptivo y secuencial
- [ ] DOWN de la migracion incluido

---

## Referencias

- [Esquema de BD](./schema.md)
- [Multi-tenancy](../architecture/multi-tenancy.md)
