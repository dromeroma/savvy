# Arquitectura General de SavvyCore

---

## Resumen ejecutivo

SavvyCore es la plataforma base sobre la cual Savvitrix Solutions construye todas sus aplicaciones SaaS. Su arquitectura sigue tres principios fundamentales:

1. **Monolito modular** -- Un solo deployable con modulos bien separados internamente.
2. **API-first** -- Toda funcionalidad se expone como API REST antes que cualquier interfaz.
3. **Multi-tenant** -- Una sola instancia sirve a multiples organizaciones de forma aislada y segura.

---

## Diagrama de alto nivel

```
+-----------------------------------------------------------------------+
|                          CLIENTES                                     |
|  +-------------+  +----------------+  +--------------+  +-----------+ |
|  | SavvyPOS    |  | SavvyLogistics |  | SavvyInvent. |  | Admin Web | |
|  | (Frontend)  |  | (Frontend)     |  | (Frontend)   |  | (SPA)     | |
|  +------+------+  +-------+--------+  +------+-------+  +-----+-----+|
+---------|-----------------|--------------------|---------------|-------+
          |                 |                    |               |
          v                 v                    v               v
+-----------------------------------------------------------------------+
|                       API GATEWAY (FastAPI)                           |
|  +----------+  +-----------+  +------+  +-----+  +------+           |
|  | Logging  |->| RateLimit |->| CORS |->| Org |->| Auth |-> Handler |
|  +----------+  +-----------+  +------+  +-----+  +------+           |
+-----------------------------------------------------------------------+
          |                 |                    |               |
          v                 v                    v               v
+-----------------------------------------------------------------------+
|                     SAVVY CORE (Monolito Modular)                     |
|                                                                       |
|  +-------------+  +------------------+  +---------------------------+ |
|  | Auth Module |  | Organization Mod.|  | [Futuros modulos core]    | |
|  | - JWT       |  | - CRUD Orgs      |  | - Billing                | |
|  | - RBAC      |  | - Memberships    |  | - Notifications          | |
|  | - Sessions  |  | - Invitations    |  | - Audit Log              | |
|  +------+------+  +--------+---------+  +-------------+-------------+ |
|         |                  |                           |               |
+---------|------------------|---------------------------|---------------+
          |                  |                           |
          v                  v                           v
+-----------------------------------------------------------------------+
|                    CAPA DE DATOS                                      |
|  +-------------------+  +------------------+  +--------------------+  |
|  | PostgreSQL        |  | Redis            |  | S3/Object Storage  |  |
|  | (Datos primarios) |  | (Cache/Sessions) |  | (Archivos)         |  |
|  +-------------------+  +------------------+  +--------------------+  |
+-----------------------------------------------------------------------+
```

---

## Principios arquitectonicos

### 1. Monolito modular

**Decision**: Comenzar como un monolito modular en lugar de microservicios.

**Razonamiento**:

| Factor | Monolito modular | Microservicios |
|--------|-----------------|----------------|
| Complejidad inicial | Baja | Alta |
| Tiempo al mercado | Rapido | Lento |
| Costo operativo | Bajo (1 servidor) | Alto (orquestacion, networking) |
| Debugging | Simple (un proceso) | Complejo (distribuido) |
| Consistencia de datos | Transacciones locales | Sagas, eventual consistency |
| Equipo requerido | Pequeno (1-5 devs) | Grande (equipos por servicio) |
| Escalabilidad | Vertical + horizontal basica | Horizontal granular |

**Conclusion**: Para un equipo pequeno con presupuesto limitado, el monolito modular ofrece velocidad de desarrollo, simplicidad operativa y suficiente escalabilidad para las primeras etapas. La modularidad interna permite extraer microservicios cuando el crecimiento lo justifique.

**Reglas del monolito modular**:
- Cada modulo tiene su propia carpeta con estructura estandar.
- Los modulos se comunican entre si a traves de interfaces definidas, nunca accediendo directamente a la base de datos de otro modulo.
- Cada modulo puede tener sus propias migraciones de BD.
- Las dependencias entre modulos son explicitas y unidireccionales.

### 2. API-first

**Decision**: Disenar y construir la API antes que cualquier frontend.

**Razonamiento**:
- Permite que multiples clientes (web, movil, terceros) consuman la misma API.
- Facilita la documentacion y testing automatizado.
- Desacopla completamente frontend de backend.
- Habilita integraciones con terceros desde el dia uno.

**Implementacion**:
- Toda la API sigue convenciones REST.
- Versionado via URL: `/api/v1/`.
- Documentacion OpenAPI/Swagger generada automaticamente por FastAPI.
- Respuestas estandarizadas en formato JSON.

### 3. Multi-tenant

**Decision**: Soportar multiples organizaciones (tenants) en una sola instancia.

**Razonamiento**:
- Reduce costos operativos drasticamente (una BD, un servidor).
- Simplifica despliegues y actualizaciones.
- Permite ofrecer planes gratuitos/basicos sin costo marginal significativo.

**Implementacion**: Ver [Multi-tenancy](./multi-tenancy.md) para detalles completos.

---

## Capas de la arquitectura

### Capa 1: API Gateway

El gateway es el punto de entrada unico para todas las peticiones HTTP. Ejecuta un pipeline secuencial de middlewares (dependencies en FastAPI):

1. **Logging** -- Registra cada peticion con ID de correlacion.
2. **Rate Limiting** -- Limita peticiones por IP y por organizacion.
3. **CORS** -- Configura origenes permitidos.
4. **Organization Resolution** -- Identifica la organizacion desde el JWT.
5. **Authentication** -- Valida JWT y adjunta usuario al contexto.
6. **Authorization** -- Verifica permisos RBAC para la ruta.
7. **Handler** -- Ejecuta la logica del endpoint.

### Capa 2: Modulos de negocio

Cada modulo encapsula un dominio de negocio completo:

- **Auth**: Registro, login, JWT, refresh tokens, RBAC.
- **Organization**: Gestion de orgs, membresias, invitaciones.
- **(Futuros)**: Billing, Notifications, Audit, etc.

### Capa 3: Datos

- **PostgreSQL**: Almacen principal. Las tablas de negocio incluyen `organization_id` con RLS.
- **Redis**: Cache de sesiones, rate limiting, datos temporales.
- **Object Storage**: Archivos, imagenes, exports.

---

## Flujo tipico de una peticion

```
Cliente envia: GET /api/v1/organizations/me
                          |
                          v
                  [API Gateway]
                    |  |  |  |  |
                    v  v  v  v  v
            Log  Rate CORS Org Auth
            Mid  Lim  Mid  Mid Mid
                          |
                          v
            [Organization Module - Router]
                          |
                          v
            [Organization Module - Service]
                          |
                          v
            [Organization Module - Repository]
                          |
                          v
                   [PostgreSQL]
                          |
                          v
            Respuesta: 200 OK
            { "data": { "id": "uuid", "name": "Mi Empresa" } }
```

---

## Estructura de carpetas del proyecto

```
savvy/
  app/
    core/
      config.py               <-- Configuracion con prefijo SAVVY_
      database.py             <-- Conexion a BD (SQLAlchemy async)
      security.py             <-- JWT, hashing de passwords
      dependencies.py         <-- Dependencies compartidas (get_org_id, etc.)
    models/                   <-- Modelos SQLAlchemy
      base.py                 <-- Base, OrgMixin, timestamps
      user.py
      organization.py
      membership.py
      refresh_token.py
      invitation.py
    routers/                  <-- Routers FastAPI
      auth.py
      organizations.py
    schemas/                  <-- Schemas Pydantic
      auth.py
      organization.py
    services/                 <-- Logica de negocio
      auth_service.py
      organization_service.py
    middleware/                <-- Middlewares
      logging.py
      rate_limit.py
    main.py                   <-- Punto de entrada FastAPI
  migrations/                 <-- Migraciones Alembic
  tests/                      <-- Tests automatizados
  docs/                       <-- Esta documentacion
  docker-compose.yml
  pyproject.toml
  requirements.txt
```

---

## Decisiones de diseno documentadas

| Decision | Alternativas evaluadas | Elegida | Razon |
|----------|----------------------|---------|-------|
| Monolito modular | Microservicios, Serverless | Monolito modular | Velocidad, simplicidad, costo |
| API-first | Frontend-first, Full-stack framework | API-first | Flexibilidad de clientes |
| Multi-tenant compartido | BD por tenant, Schema por tenant | BD compartida | Costo, simplicidad operativa |
| PostgreSQL | MySQL, MongoDB, CockroachDB | PostgreSQL | RLS nativo, JSON, extensiones |
| JWT + Refresh | Sessions, OAuth solo | JWT + Refresh | Stateless, escalable, estandar |
| Python + FastAPI | Bun + Hono, Node + Express | Python + FastAPI | Productividad, ecosistema IA, tipado |
| SQLAlchemy 2.0 | Tortoise ORM, SQLModel | SQLAlchemy | Madurez, flexibilidad, async |

---

## Referencias

- [Multi-tenancy](./multi-tenancy.md)
- [Escalabilidad](./scalability.md)
- [Stack Tecnologico](./tech-stack.md)
- [Esquema de BD](../database/schema.md)
