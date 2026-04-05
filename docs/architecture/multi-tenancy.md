# Estrategia de Multi-tenancy

---

## Resumen

SavvyCore utiliza una estrategia de **base de datos compartida con esquema compartido** y aislamiento mediante `organization_id` + **Row Level Security (RLS)** de PostgreSQL. Esta decision balancea costo, complejidad operativa y seguridad para una plataforma SaaS en etapa temprana.

---

## Comparacion de estrategias de multi-tenancy

| Criterio | BD por tenant | Schema por tenant | BD compartida + organization_id |
|----------|--------------|-------------------|-------------------------------|
| **Aislamiento de datos** | Maximo | Alto | Medio (RLS lo eleva a alto) |
| **Costo operativo** | Muy alto (N bases) | Alto (N schemas) | Bajo (1 base, 1 schema) |
| **Complejidad de deploy** | Alta | Media | Baja |
| **Migraciones** | Aplicar N veces | Aplicar N veces | Aplicar 1 vez |
| **Escalabilidad** | Limitada por recursos | Media | Alta |
| **Onboarding de tenant** | Lento (crear BD) | Medio (crear schema) | Instantaneo (INSERT) |
| **Backup/Restore individual** | Facil | Medio | Dificil |
| **Performance con muchos tenants** | Se degrada | Se degrada | Estable con indices |
| **Complejidad de queries** | Baja (sin filtro) | Baja (sin filtro) | Media (siempre filtrar) |
| **Costo mensual estimado (100 tenants)** | ~$500-2000 | ~$200-500 | ~$50-100 |

### Por que elegimos BD compartida con organization_id

1. **Costo**: Un solo servidor PostgreSQL para todos los tenants. Critico en etapa temprana.
2. **Simplicidad**: Una sola conexion, un solo schema, migraciones simples.
3. **Velocidad de onboarding**: Crear un tenant es un INSERT, no provisionar infraestructura.
4. **RLS de PostgreSQL**: Nos da aislamiento a nivel de base de datos, no solo de aplicacion.
5. **Escalabilidad suficiente**: PostgreSQL maneja millones de filas con indices apropiados.

### Riesgos mitigados

| Riesgo | Mitigacion |
|--------|-----------|
| Leak de datos entre tenants | RLS a nivel de BD + filtro en middleware + tests automatizados |
| "Noisy neighbor" (tenant consumiendo recursos) | Rate limiting por organizacion + monitoreo + limites de plan |
| Backup individual | Export selectivo por organization_id + soft deletes |
| Cumplimiento regulatorio (datos en pais X) | Plan futuro: instancias regionales cuando se requiera |

---

## Implementacion tecnica

### 1. Columna organization_id

**Toda tabla de datos de negocio** incluye una columna `organization_id`:

```sql
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(255) NOT NULL,
    price           DECIMAL(12,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_organization_id ON products(organization_id);
```

**Excepciones** (tablas sin organization_id):
- `organizations` -- ES la tabla de tenants, no necesita referenciarse a si misma.
- `users` -- Un usuario puede pertenecer a multiples organizaciones via `memberships`. Los usuarios son globales.
- `refresh_tokens` -- Pertenecen al usuario, no a la organizacion.

### 2. OrgMixin en SQLAlchemy

En el codigo Python, las tablas de negocio heredan de `OrgMixin` para incluir automaticamente el campo `organization_id`:

```python
class OrgMixin:
    """Mixin que agrega organization_id a modelos de datos de negocio."""
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
```

### 3. Row Level Security (RLS)

PostgreSQL RLS garantiza que las queries solo devuelvan filas de la organizacion activa, incluso si el codigo de la aplicacion tiene un bug:

```sql
-- Habilitar RLS en la tabla
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Politica: solo ver filas de la organizacion actual
CREATE POLICY org_isolation ON products
    USING (organization_id = current_setting('app.current_org')::UUID);

-- Politica para INSERT: solo insertar con la organizacion actual
CREATE POLICY org_insert ON products
    FOR INSERT
    WITH CHECK (organization_id = current_setting('app.current_org')::UUID);
```

### 4. Dependency de organizacion en FastAPI

La dependency `get_org_id` se ejecuta en cada peticion autenticada y establece el contexto:

```
Peticion HTTP
      |
      v
+---------------------+
| get_org_id          |
| (FastAPI Dependency) |
|                     |
| 1. Extraer org_id   |
|    del JWT           |
|                     |
| 2. Validar que la   |
|    organizacion      |
|    existe            |
|                     |
| 3. SET app.current  |
|    _org en PG        |
|                     |
| 4. Retornar org_id  |
|    al handler        |
+---------------------+
      |
      v
  Handler del endpoint
```

**Fuentes de identificacion de la organizacion** (en orden de prioridad):

1. **JWT claim** `org_id` -- Presente en tokens autenticados.
2. **Header** `X-Organization-ID` -- Para peticiones de servicio a servicio (futuro).
3. **Subdominio** -- `miempresa.savvypos.com` (futuro).

### 5. Flujo completo de una peticion multi-tenant

```
+--------+         +----------+         +-----------+         +--------+
| Cliente|         | FastAPI  |         | Servicio  |         |  PostgreSQL
+---+----+         +----+-----+         +-----+-----+         +---+----+
    |                    |                     |                    |
    | POST /api/v1/pos/products                |                    |
    | Authorization: Bearer <jwt>              |                    |
    |------------------->|                     |                    |
    |                    |                     |                    |
    |                    | 1. Decodificar JWT  |                    |
    |                    |    org_id = "abc123"|                    |
    |                    |                     |                    |
    |                    | 2. Validar org      |                    |
    |                    |----- lookup ------->|                    |
    |                    |                     |                    |
    |                    | 3. SET app.current_org = 'abc123'       |
    |                    |---------------------------------------------->|
    |                    |                     |                    |
    |                    | 4. Forward request  |                    |
    |                    |-------------------->|                    |
    |                    |                     |                    |
    |                    |                     | 5. INSERT product  |
    |                    |                     |    (organization_id|
    |                    |                     |     se valida      |
    |                    |                     |     via RLS)       |
    |                    |                     |------------------->|
    |                    |                     |                    |
    |                    |                     |    OK              |
    |                    |                     |<-------------------|
    |                    |                     |                    |
    |                    |  201 Created        |                    |
    |<-------------------|                     |                    |
    |                    |                     |                    |
```

---

## Reglas para desarrolladores

### Obligatorias

1. **Toda tabla de datos de negocio** debe incluir `organization_id UUID NOT NULL REFERENCES organizations(id)`.
2. **Toda tabla con organization_id** debe tener RLS habilitado con politica de aislamiento.
3. **Todo indice compuesto** en tablas de negocio debe incluir `organization_id` como primer campo.
4. **Toda query** debe ser validada por RLS -- nunca desactivar RLS en produccion.
5. **Todo test** debe verificar que una organizacion no puede acceder a datos de otra organizacion.

### Prohibidas

1. **Nunca** usar `SET ROLE` o `RESET ROLE` para evadir RLS.
2. **Nunca** hacer queries sin contexto de organizacion (excepto en tareas administrativas internas).
3. **Nunca** exponer `organization_id` como parametro editable por el usuario en la API.

---

## Indices recomendados

Para tablas con alto volumen de queries:

```sql
-- Indice compuesto: organization + campo de busqueda frecuente
CREATE INDEX idx_products_org_name ON products(organization_id, name);

-- Indice compuesto: organization + ordenamiento comun
CREATE INDEX idx_orders_org_created ON orders(organization_id, created_at DESC);

-- Indice parcial: solo filas activas de la organizacion
CREATE INDEX idx_products_org_active
    ON products(organization_id)
    WHERE deleted_at IS NULL;
```

---

## Plan de evolucion

| Fase | Estrategia | Trigger |
|------|-----------|---------|
| Fase 1 (actual) | BD compartida + RLS | 0 - 1,000 tenants |
| Fase 2 | BD compartida + particionamiento por organization_id | 1,000 - 10,000 tenants |
| Fase 3 | Sharding horizontal (Citus o multi-BD) | 10,000+ tenants |
| Fase 4 | Instancias dedicadas para enterprise | Clientes que lo requieran |

---

## Referencias

- [PostgreSQL Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Convenciones de BD](../database/conventions.md)
- [Esquema de BD](../database/schema.md)
