# Guia: Agregar un nuevo modulo a SavvyCore

---

## Resumen

Esta guia describe el proceso paso a paso para agregar un nuevo modulo al core de SavvyCore. Un modulo core provee funcionalidad compartida que todas las aplicaciones SaaS pueden utilizar (ej: notifications, billing, audit-log).

**Antes de empezar**: Asegurate de que la funcionalidad realmente pertenece al core y no a una app especifica. Si solo la necesita una app, deberia ser parte de esa app, no del core.

---

## Criterios para un modulo core

Un modulo pertenece al core si cumple AL MENOS dos de estos criterios:

- [ ] Lo necesitan (o necesitaran) multiples aplicaciones SaaS.
- [ ] Es funcionalidad transversal (auth, notifications, billing, audit).
- [ ] Gestiona datos que son compartidos entre apps.
- [ ] Es infraestructura que toda app requiere.

---

## Paso 1: Definir el modulo

Antes de escribir codigo, documentar:

1. **Nombre del modulo**: Sustantivo en ingles, singular o plural segun convenga (ej: `notifications`, `billing`, `audit`).
2. **Proposito**: Una frase que resuma que hace.
3. **Alcance**: Que incluye y que NO incluye.
4. **Dependencias**: Que otros modulos necesita.
5. **Tabla de endpoints** preliminar.
6. **Tablas de BD** preliminares.

Crear un documento en `docs/modules/{nombre}/README.md` con esta informacion.

---

## Paso 2: Crear la estructura de carpetas

```
src/core/{nombre_modulo}/
  handlers/              <-- Handlers HTTP (uno por endpoint)
  services/              <-- Logica de negocio
  repositories/          <-- Acceso a base de datos
  schemas/               <-- Schemas de validacion Zod
  middleware/             <-- Middlewares especificos del modulo (si aplica)
  routes.ts              <-- Definicion de rutas
  index.ts               <-- Export publico del modulo
```

### Archivo index.ts

El `index.ts` es la interfaz publica del modulo. Solo exporta lo que otros modulos necesitan:

```typescript
// src/core/{nombre}/index.ts

// Rutas (para registrar en el gateway)
export { nombreRoutes } from './routes'

// Servicios (para uso por otros modulos, si aplica)
export { NombreService } from './services/nombre.service'

// Tipos (para tipado en otros modulos)
export type { NombreEntity, CreateNombreInput } from './schemas/nombre.schema'
```

---

## Paso 3: Crear las tablas de base de datos

### 3.1 Crear la migracion

```
migrations/{numero_secuencial}_create_{nombre_tabla}.sql
```

### 3.2 Seguir las convenciones de BD

Checklist obligatorio:

- [ ] `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- [ ] `tenant_id UUID NOT NULL REFERENCES organizations(id)` (si la tabla tiene datos por org)
- [ ] `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- [ ] `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- [ ] Trigger `trg_{tabla}_updated_at`
- [ ] Indices en foreign keys
- [ ] Indice en `tenant_id` (si aplica)
- [ ] RLS habilitado (si tiene `tenant_id`)
- [ ] `deleted_at TIMESTAMPTZ` si se necesita soft delete

### 3.3 Crear el schema Drizzle

```typescript
// src/core/{nombre}/models/{tabla}.model.ts
import { pgTable, uuid, varchar, timestamptz, jsonb } from 'drizzle-orm/pg-core'

export const nombreTabla = pgTable('{tabla}', {
  id: uuid('id').primaryKey().defaultRandom(),
  tenantId: uuid('tenant_id').notNull().references(() => organizations.id),
  // ... campos
  createdAt: timestamptz('created_at').notNull().defaultNow(),
  updatedAt: timestamptz('updated_at').notNull().defaultNow(),
})
```

---

## Paso 4: Implementar el repositorio

El repositorio encapsula las queries a base de datos. Nunca hacer queries directamente desde handlers o services.

```typescript
// src/core/{nombre}/repositories/{nombre}.repository.ts

export class NombreRepository {
  constructor(private db: Database) {}

  async findById(id: string): Promise<NombreEntity | null> {
    // Query con Drizzle
  }

  async findByTenant(tenantId: string, pagination: Pagination): Promise<PaginatedResult<NombreEntity>> {
    // Query paginada
  }

  async create(data: CreateNombreInput): Promise<NombreEntity> {
    // Insert
  }

  async update(id: string, data: UpdateNombreInput): Promise<NombreEntity> {
    // Update
  }

  async softDelete(id: string): Promise<void> {
    // UPDATE SET deleted_at = NOW()
  }
}
```

---

## Paso 5: Implementar el servicio

El servicio contiene la logica de negocio. Valida reglas de negocio, coordina repositorios, y emite eventos.

```typescript
// src/core/{nombre}/services/{nombre}.service.ts

export class NombreService {
  constructor(
    private repo: NombreRepository,
    private eventBus: EventBus // Si emite eventos
  ) {}

  async create(input: CreateNombreInput, context: RequestContext): Promise<NombreEntity> {
    // 1. Validar reglas de negocio
    // 2. Crear en BD via repositorio
    // 3. Emitir evento (si aplica)
    // 4. Retornar resultado
  }
}
```

---

## Paso 6: Implementar los schemas de validacion

Usar Zod para definir schemas de input:

```typescript
// src/core/{nombre}/schemas/create-{nombre}.schema.ts
import { z } from 'zod'

export const createNombreSchema = z.object({
  name: z.string().min(2).max(100),
  description: z.string().max(500).optional(),
  // ... campos
})

export type CreateNombreInput = z.infer<typeof createNombreSchema>
```

---

## Paso 7: Implementar los handlers

Un handler por endpoint. Cada handler:
1. Extrae y valida el input.
2. Llama al servicio.
3. Retorna la respuesta formateada.

```typescript
// src/core/{nombre}/handlers/create-{nombre}.handler.ts
import { Context } from 'hono'
import { createNombreSchema } from '../schemas/create-nombre.schema'

export async function createNombreHandler(c: Context) {
  const body = await c.req.json()
  const input = createNombreSchema.parse(body)
  const context = c.get('requestContext')

  const result = await nombreService.create(input, context)

  return c.json({ data: result }, 201)
}
```

---

## Paso 8: Definir las rutas

```typescript
// src/core/{nombre}/routes.ts
import { Hono } from 'hono'
import { authMiddleware } from '../shared/middleware/auth.middleware'
import { rbacMiddleware } from '../shared/middleware/rbac.middleware'
import { createNombreHandler } from './handlers/create-nombre.handler'
import { listNombreHandler } from './handlers/list-nombre.handler'
// ...

export const nombreRoutes = new Hono()
  .get('/', authMiddleware, listNombreHandler)
  .post('/', authMiddleware, rbacMiddleware('admin'), createNombreHandler)
  .get('/:id', authMiddleware, getNombreHandler)
  .put('/:id', authMiddleware, rbacMiddleware('admin'), updateNombreHandler)
  .delete('/:id', authMiddleware, rbacMiddleware('admin'), deleteNombreHandler)
```

---

## Paso 9: Registrar en el gateway

Agregar las rutas del modulo al gateway:

```typescript
// src/core/gateway/app.ts
import { nombreRoutes } from '../{nombre}/routes'

// ... rutas existentes ...
app.route('/api/v1/{nombre}', nombreRoutes)
```

---

## Paso 10: Escribir tests

### Tests unitarios (services)

```typescript
// tests/core/{nombre}/services/{nombre}.service.test.ts
import { describe, it, expect, vi } from 'vitest'

describe('NombreService', () => {
  it('debe crear un recurso correctamente', async () => {
    // Arrange: mock del repositorio
    // Act: llamar al servicio
    // Assert: verificar resultado y efectos secundarios
  })

  it('debe validar reglas de negocio', async () => {
    // ...
  })
})
```

### Tests de integracion (endpoints)

```typescript
// tests/core/{nombre}/routes.test.ts
import { describe, it, expect } from 'vitest'

describe('POST /api/v1/{nombre}', () => {
  it('debe crear y retornar 201', async () => {
    const response = await app.request('/api/v1/{nombre}', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${testToken}`
      },
      body: JSON.stringify({ name: 'Test' })
    })

    expect(response.status).toBe(201)
    const body = await response.json()
    expect(body.data.name).toBe('Test')
  })

  it('debe retornar 403 si no tiene permisos', async () => {
    // ...
  })
})
```

### Test de aislamiento multi-tenant

```typescript
it('no debe acceder a datos de otro tenant', async () => {
  // Crear recurso con tenant A
  // Intentar acceder con tenant B
  // Verificar que retorna 404 o lista vacia
})
```

---

## Paso 11: Documentar

Actualizar la documentacion:

1. **Crear** `docs/modules/{nombre}/README.md` con la documentacion completa del modulo.
2. **Crear** `docs/api/{nombre}-endpoints.md` con los endpoints detallados.
3. **Actualizar** `docs/database/schema.md` con las nuevas tablas.
4. **Actualizar** `docs/README.md` agregando el modulo al indice.

---

## Checklist final

Antes de hacer merge del modulo:

- [ ] Estructura de carpetas correcta
- [ ] Migracion de BD creada y probada
- [ ] RLS configurado en tablas con tenant_id
- [ ] Schemas Zod para toda validacion de input
- [ ] Handlers, services y repositories implementados
- [ ] Rutas registradas en el gateway
- [ ] Tests unitarios con cobertura > 80%
- [ ] Tests de integracion para endpoints principales
- [ ] Test de aislamiento multi-tenant
- [ ] Documentacion creada y actualizada
- [ ] Code review aprobado

---

## Ejemplo completo: Modulo Notifications

Para ver un ejemplo completo de un modulo, revisa la estructura del modulo Auth en `src/core/auth/` y su documentacion en [docs/modules/auth/README.md](../modules/auth/README.md).

---

## Referencias

- [Arquitectura General](../architecture/overview.md)
- [Convenciones de BD](../database/conventions.md)
- [Convenciones API](../api/README.md)
