# Guia: Crear una nueva aplicacion SaaS sobre SavvyCore

---

## Resumen

Esta guia describe el proceso completo para crear una nueva aplicacion SaaS (como SavvyPOS, SavvyLogistics, etc.) que se ejecuta sobre la base de SavvyCore.

---

## Prerequisitos

Antes de empezar:

- [ ] SavvyCore esta funcionando localmente (auth, organizations, gateway).
- [ ] Tienes claro el dominio de negocio de la app.
- [ ] Has definido el MVP (funcionalidades minimas viables).
- [ ] Has revisado la [arquitectura general](../architecture/overview.md).
- [ ] Has revisado las [convenciones de BD](../database/conventions.md) y [API](../api/README.md).

---

## Paso 1: Planificacion

### 1.1 Definir el alcance

Responder estas preguntas:

1. **Que problema resuelve?** {Una frase clara}
2. **Quienes son los usuarios?** {Tipos de usuario}
3. **Que funcionalidades tiene el MVP?** {Lista priorizada}
4. **Que datos maneja?** {Entidades principales}
5. **Que integraciones necesita?** {APIs externas, otros modulos}

### 1.2 Elegir el prefijo de la app

El prefijo se usa en rutas API y nombres de migracion:

| App | Prefijo | Ruta base |
|-----|---------|-----------|
| SavvyPOS | `pos` | `/api/v1/pos/` |
| SavvyLogistics | `logistics` | `/api/v1/logistics/` |
| SavvyInventory | `inventory` | `/api/v1/inventory/` |
| {Tu app} | `{prefijo}` | `/api/v1/{prefijo}/` |

**Reglas del prefijo**:
- Minusculas, sin guiones ni guiones bajos.
- Corto (max 15 caracteres).
- Descriptivo del dominio.
- Unico entre todas las apps.

---

## Paso 2: Crear la estructura de carpetas

```
src/apps/{prefijo}/
  handlers/              <-- Handlers HTTP
  services/              <-- Logica de negocio
  repositories/          <-- Acceso a BD
  schemas/               <-- Schemas Zod
  models/                <-- Modelos Drizzle
  middleware/             <-- Middlewares especificos de la app (si aplica)
  routes.ts              <-- Definicion de rutas
  index.ts               <-- Export publico

migrations/
  {prefijo}_0001_create_{primera_tabla}.sql
```

### Crear los archivos base

**index.ts** -- Export de la app:

```typescript
// src/apps/{prefijo}/index.ts
export { appRoutes as {prefijo}Routes } from './routes'
```

**routes.ts** -- Rutas de la app:

```typescript
// src/apps/{prefijo}/routes.ts
import { Hono } from 'hono'
import { authMiddleware } from '../../core/shared/middleware/auth.middleware'
import { tenantMiddleware } from '../../core/shared/middleware/tenant.middleware'

export const appRoutes = new Hono()

// Aplicar middlewares del core a todas las rutas de la app
appRoutes.use('*', authMiddleware)
appRoutes.use('*', tenantMiddleware)

// Rutas de la app
// appRoutes.route('/products', productRoutes)
// appRoutes.route('/sales', saleRoutes)
```

---

## Paso 3: Disenar la base de datos

### 3.1 Identificar las entidades

Listar todas las tablas que la app necesita. Para cada una:

- Nombre (plural, snake_case)
- Columnas con tipos
- Relaciones con otras tablas
- Indices necesarios

### 3.2 Crear las migraciones

Nombrar las migraciones con el prefijo de la app:

```
migrations/{prefijo}_0001_create_products.sql
migrations/{prefijo}_0002_create_categories.sql
migrations/{prefijo}_0003_create_sales.sql
```

### 3.3 Seguir las convenciones obligatorias

Toda tabla de la app DEBE incluir:

```sql
CREATE TABLE {nombre_tabla} (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES organizations(id),
    -- ... campos de la app ...
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indice en tenant_id
CREATE INDEX idx_{tabla}_tenant_id ON {tabla}(tenant_id);

-- RLS
ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON {tabla}
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_insert ON {tabla}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::UUID);

-- Trigger updated_at
CREATE TRIGGER trg_{tabla}_updated_at
    BEFORE UPDATE ON {tabla}
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.4 Relaciones con tablas del core

Las tablas de la app pueden referenciar tablas del core:

```sql
-- Referencia a organizations (tenant)
tenant_id UUID NOT NULL REFERENCES organizations(id)

-- Referencia a users (creador, asignado, etc.)
created_by UUID REFERENCES users(id)
```

**Nunca** crear FK desde tablas del core hacia tablas de la app. La dependencia es unidireccional: app --> core.

---

## Paso 4: Implementar la logica

### 4.1 Patron por recurso

Para cada recurso/entidad de la app, crear:

```
handlers/
  list-{recurso}.handler.ts
  get-{recurso}.handler.ts
  create-{recurso}.handler.ts
  update-{recurso}.handler.ts
  delete-{recurso}.handler.ts

services/
  {recurso}.service.ts

repositories/
  {recurso}.repository.ts

schemas/
  create-{recurso}.schema.ts
  update-{recurso}.schema.ts

models/
  {recurso}.model.ts
```

### 4.2 Usar los servicios del core

La app puede importar servicios del core:

```typescript
// Usar el servicio de auth para verificar permisos
import { authMiddleware, rbacMiddleware } from '../../core/auth'

// Usar el event bus para emitir eventos
import { eventBus } from '../../core/shared/events'

// Emitir un evento de la app
eventBus.emit('pos.sale.created', { id: sale.id, tenantId, total: sale.total })
```

### 4.3 No modificar el core

Si necesitas funcionalidad nueva en el core:

1. Proponer un nuevo modulo core (ver [guia de agregar modulo](./adding-a-module.md)).
2. Discutir con el equipo si realmente es transversal.
3. Si se aprueba, implementarlo como modulo core separado.
4. **Nunca** agregar codigo especifico de una app dentro de `src/core/`.

---

## Paso 5: Registrar la app en el gateway

### 5.1 Agregar las rutas

```typescript
// src/core/gateway/app.ts
import { posRoutes } from '../../apps/pos'

// ... rutas del core ...
app.route('/api/v1/auth', authRoutes)
app.route('/api/v1/organizations', orgRoutes)

// Rutas de apps
app.route('/api/v1/pos', posRoutes)
// app.route('/api/v1/logistics', logisticsRoutes)
```

### 5.2 Configurar rate limiting especifico (si aplica)

```typescript
// Si la app tiene endpoints con limites especiales
rateLimitConfig.endpoints['/api/v1/pos/sales'] = {
  limit: 200,
  window: '1m'
}
```

---

## Paso 6: Configurar feature flags por organizacion

Cada organizacion puede habilitar/deshabilitar apps via el campo `settings.features`:

```json
{
  "features": {
    "pos": true,
    "logistics": false,
    "inventory": true
  }
}
```

Crear un middleware que verifique si la org tiene la app habilitada:

```typescript
// src/apps/{prefijo}/middleware/feature-check.middleware.ts

export async function featureCheckMiddleware(c: Context, next: Next) {
  const org = c.get('organization')

  if (!org.settings?.features?.['{prefijo}']) {
    return c.json({
      error: {
        code: 'FEATURE_NOT_ENABLED',
        message: 'Esta funcionalidad no esta habilitada para tu organizacion'
      }
    }, 403)
  }

  await next()
}
```

---

## Paso 7: Escribir tests

### Tests minimos requeridos

1. **Unitarios**: Logica de negocio en services.
2. **Integracion**: Cada endpoint responde correctamente.
3. **Multi-tenant**: Datos aislados entre tenants.
4. **Permisos**: RBAC funciona correctamente.
5. **Feature flag**: App deshabilitada retorna 403.

### Estructura de tests

```
tests/apps/{prefijo}/
  services/
    {recurso}.service.test.ts
  handlers/
    {recurso}.handler.test.ts
  routes.test.ts
  multi-tenant.test.ts
```

### Test multi-tenant ejemplo

```typescript
describe('Aislamiento multi-tenant en {App}', () => {
  it('Tenant A no ve datos de Tenant B', async () => {
    // 1. Crear producto con Tenant A
    const productA = await createProduct(tenantAToken, { name: 'Producto A' })

    // 2. Listar productos con Tenant B
    const response = await app.request('/api/v1/pos/products', {
      headers: { Authorization: `Bearer ${tenantBToken}` }
    })
    const body = await response.json()

    // 3. Verificar que el producto de A no aparece
    expect(body.data).toHaveLength(0)
    expect(body.data.find(p => p.id === productA.id)).toBeUndefined()
  })
})
```

---

## Paso 8: Documentar la app

### 8.1 Crear la documentacion

Copiar la plantilla y completarla:

```
docs/apps/{prefijo}/
  README.md              <-- Copiar de docs/apps/_template/README.md
```

Ver la [plantilla de documentacion](../apps/_template/README.md) para el formato completo.

### 8.2 Actualizar la documentacion del core

- **docs/README.md**: Agregar la app al indice.
- **docs/apps/README.md**: Agregar la app a la lista de apps planeadas/existentes.
- **docs/database/schema.md**: Agregar las tablas de la app (o crear un schema.md separado en `docs/apps/{prefijo}/`).

---

## Paso 9: Despliegue

### 9.1 Migraciones

Las migraciones de la app se ejecutan junto con las del core, en orden secuencial:

```
0001_create_organizations.sql       <-- Core
0002_create_users.sql               <-- Core
0003_create_memberships.sql         <-- Core
pos_0001_create_products.sql        <-- App POS
pos_0002_create_categories.sql      <-- App POS
pos_0003_create_sales.sql           <-- App POS
logistics_0001_create_shipments.sql <-- App Logistics
```

### 9.2 Variables de entorno

Si la app necesita configuracion propia, agregar variables con prefijo:

```env
# Variables de SavvyPOS
POS_RECEIPT_PRINTER_ENABLED=true
POS_DEFAULT_TAX_RATE=0.19

# Variables de SavvyLogistics
LOGISTICS_GOOGLE_MAPS_API_KEY=xxx
LOGISTICS_DEFAULT_TRACKING_INTERVAL=30
```

---

## Checklist final

Antes de hacer merge de la nueva app:

- [ ] Prefijo unico definido y registrado
- [ ] Estructura de carpetas creada
- [ ] Migraciones de BD creadas y probadas
- [ ] RLS en todas las tablas con tenant_id
- [ ] Handlers, services, repositories implementados
- [ ] Schemas Zod para validacion de input
- [ ] Rutas registradas en el gateway
- [ ] Feature flag middleware implementado
- [ ] Tests unitarios (> 80% cobertura en services)
- [ ] Tests de integracion (todos los endpoints)
- [ ] Test de aislamiento multi-tenant
- [ ] Test de feature flag
- [ ] Documentacion creada (README.md de la app)
- [ ] Documentacion del core actualizada
- [ ] Variables de entorno documentadas
- [ ] Code review aprobado

---

## Diagrama resumen del proceso

```
+-------------------+     +-------------------+     +-------------------+
| 1. PLANIFICAR     |     | 2. ESTRUCTURA     |     | 3. BASE DE DATOS  |
|                   |     |                   |     |                   |
| - Definir alcance |---->| - Crear carpetas  |---->| - Disenar tablas  |
| - Elegir prefijo  |     | - index.ts        |     | - Migraciones     |
| - MVP features    |     | - routes.ts       |     | - RLS + indices   |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                            v
+-------------------+     +-------------------+     +-------------------+
| 6. DOCUMENTAR     |     | 5. TESTING        |     | 4. IMPLEMENTAR    |
|                   |     |                   |     |                   |
| - README app      |<----| - Unitarios       |<----| - Handlers        |
| - Actualizar core |     | - Integracion     |     | - Services        |
| - Endpoints       |     | - Multi-tenant    |     | - Repositories    |
+-------------------+     +-------------------+     +-------------------+
        |
        v
+-------------------+
| 7. DEPLOY         |
|                   |
| - Migraciones     |
| - Variables env   |
| - Feature flags   |
+-------------------+
```

---

## Referencias

- [Apps sobre SavvyCore](../apps/README.md)
- [Plantilla de app](../apps/_template/README.md)
- [Guia: Agregar un modulo](./adding-a-module.md)
- [Arquitectura General](../architecture/overview.md)
- [Convenciones de BD](../database/conventions.md)
- [Convenciones API](../api/README.md)
