# Modulo API Gateway

---

## Proposito

El API Gateway es el punto de entrada unico para todas las peticiones HTTP hacia SavvyCore. Su responsabilidad es:

- Ejecutar un pipeline secuencial de middlewares
- Enrutar peticiones al modulo correcto
- Gestionar versionado de la API
- Aplicar politicas transversales (seguridad, rate limiting, logging)

---

## Pipeline de middleware

Cada peticion pasa por los siguientes middlewares en orden estricto. Si cualquier middleware rechaza la peticion, la cadena se detiene y se retorna el error al cliente.

```
Peticion HTTP entrante
        |
        v
+-------------------+
| 1. Request ID     |  Asigna un ID unico (UUID) a cada peticion para trazabilidad.
| & Logging         |  Registra: metodo, ruta, IP, User-Agent, timestamp.
+-------------------+
        |
        v
+-------------------+
| 2. Rate Limiting  |  Limita peticiones por IP (global) y por tenant (si autenticado).
|                   |  - Global: 100 req/min por IP
|                   |  - Por tenant: segun plan (1000-10000 req/min)
|                   |  - Por endpoint: configurable (ej. login: 5 req/min)
+-------------------+
        |
        v
+-------------------+
| 3. CORS           |  Configura origenes permitidos, metodos, headers.
|                   |  - Dev: http://localhost:*
|                   |  - Prod: dominios registrados por tenant
+-------------------+
        |
        v
+-------------------+
| 4. Body Parser    |  Parsea el body de la peticion (JSON).
|                   |  - Limite de tamano: 1MB por defecto
|                   |  - Content-Type: application/json
+-------------------+
        |
        v
+-------------------+
| 5. Tenant         |  Identifica el tenant desde JWT o headers.
| Resolution        |  Establece SET app.current_tenant en PostgreSQL.
|                   |  Adjunta tenant al contexto de la peticion.
+-------------------+
        |
        v
+-------------------+
| 6. Authentication |  Valida el JWT del header Authorization.
|                   |  Si la ruta es publica, pasa sin validar.
|                   |  Si el JWT es invalido o expirado: 401.
+-------------------+
        |
        v
+-------------------+
| 7. Authorization  |  Verifica que el rol del usuario permite acceder
| (RBAC)            |  a esta ruta. Si no tiene permiso: 403.
+-------------------+
        |
        v
+-------------------+
| 8. Validation     |  Valida body, query params y path params contra
|                   |  schemas Zod del endpoint. Si falla: 400.
+-------------------+
        |
        v
+-------------------+
| 9. Handler        |  Ejecuta la logica de negocio del endpoint.
|                   |  Retorna la respuesta al cliente.
+-------------------+
        |
        v
+-------------------+
| 10. Response      |  Formatea la respuesta en el formato estandar.
| Formatter         |  Agrega headers de seguridad.
|                   |  Registra el tiempo de respuesta.
+-------------------+
        |
        v
  Respuesta HTTP
```

### Diagrama de decision en cada middleware

```
Middleware recibe peticion
        |
        v
  [Ejecutar logica]
        |
   +----+----+
   |         |
  PASS     FAIL
   |         |
   v         v
Siguiente   Retornar error
Middleware   { status, error, message }
```

---

## Routing y versionado

### Estructura de rutas

```
/api/v1/
  auth/
    POST   /register            --> Auth.register
    POST   /login               --> Auth.login
    POST   /refresh             --> Auth.refresh
    POST   /logout              --> Auth.logout
    GET    /me                  --> Auth.me
    POST   /switch-org          --> Auth.switchOrg

  organizations/
    POST   /                    --> Org.create
    GET    /                    --> Org.list
    GET    /:id                 --> Org.get
    PUT    /:id                 --> Org.update
    DELETE /:id                 --> Org.delete
    GET    /:id/members         --> Org.listMembers
    PUT    /:id/members/:uid    --> Org.updateMember
    DELETE /:id/members/:uid    --> Org.removeMember
    POST   /:id/invitations     --> Org.createInvitation
    GET    /:id/invitations     --> Org.listInvitations
    DELETE /:id/invitations/:iid --> Org.cancelInvitation

  invitations/
    POST   /:token/accept       --> Invitation.accept
    POST   /:token/reject       --> Invitation.reject

  # Rutas de apps SaaS (futuras)
  pos/
    ...                         --> Modulo POS
  logistics/
    ...                         --> Modulo Logistics
```

### Versionado de API

**Estrategia**: Versionado por URL (`/api/v1/`, `/api/v2/`).

| Criterio | Por URL | Por header | Por query param |
|----------|---------|-----------|-----------------|
| Claridad | Alta | Media | Baja |
| Cacheability | Alta | Baja | Media |
| Facilidad de routing | Alta | Media | Media |
| Estandar de industria | Si | Si | No |

**Reglas de versionado**:

1. Cambios retrocompatibles (agregar campos opcionales) NO requieren nueva version.
2. Cambios incompatibles (remover campos, cambiar tipos) SI requieren nueva version.
3. La version anterior se mantiene funcional por minimo 6 meses despues de deprecarla.
4. Respuestas de version deprecada incluyen header `Deprecation: true` y `Sunset: <date>`.

### Registro de rutas

Cada modulo exporta sus rutas que el gateway registra:

```typescript
// src/core/auth/routes.ts
export const authRoutes = new Hono()
  .post('/register', registerHandler)
  .post('/login', loginHandler)
  .post('/refresh', refreshHandler)
  .post('/logout', authMiddleware, logoutHandler)
  .get('/me', authMiddleware, meHandler)
  .post('/switch-org', authMiddleware, switchOrgHandler)

// src/core/gateway/app.ts
const app = new Hono()

// Middlewares globales
app.use('*', requestIdMiddleware)
app.use('*', loggingMiddleware)
app.use('*', rateLimitMiddleware)
app.use('*', corsMiddleware)

// Rutas versionadas
app.route('/api/v1/auth', authRoutes)
app.route('/api/v1/organizations', orgRoutes)
app.route('/api/v1/invitations', invitationRoutes)
```

---

## Rate Limiting

### Configuracion

| Ambito | Limite | Ventana | Almacenamiento |
|--------|--------|---------|----------------|
| Global por IP | 100 req | 1 minuto | Redis |
| Por tenant | Segun plan | 1 minuto | Redis |
| Login | 5 req | 15 minutos | Redis |
| Register | 3 req | 1 hora | Redis |
| Refresh | 10 req | 1 minuto | Redis |

### Algoritmo: Sliding Window

```
IP: 192.168.1.1
Ventana: 1 minuto
Limite: 100

Redis key: rate:ip:192.168.1.1
TTL: 60 segundos

Cada peticion:
  contador = INCR rate:ip:192.168.1.1
  if contador == 1:
    EXPIRE rate:ip:192.168.1.1 60
  if contador > 100:
    return 429 Too Many Requests
    Headers:
      Retry-After: <segundos restantes>
      X-RateLimit-Limit: 100
      X-RateLimit-Remaining: 0
      X-RateLimit-Reset: <timestamp>
```

---

## Logging

### Formato de log por peticion

```json
{
  "request_id": "req_abc123",
  "timestamp": "2026-03-28T10:30:00.000Z",
  "method": "POST",
  "path": "/api/v1/organizations",
  "status": 201,
  "duration_ms": 45,
  "ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "user_id": "550e8400-...",
  "tenant_id": "660e8400-...",
  "error": null
}
```

### Niveles de log

| Nivel | Uso |
|-------|-----|
| `info` | Peticiones exitosas, eventos normales |
| `warn` | Rate limiting, tokens expirados, intentos de acceso no autorizado |
| `error` | Errores de servidor (5xx), fallos de BD |
| `debug` | Solo en desarrollo: queries SQL, payloads completos |

---

## Manejo de errores

Todos los errores se capturan en un handler global y se retornan en formato estandar:

```
Handler lanza error
        |
        v
+-------------------+
| Error Handler     |
| Global            |
+-------------------+
        |
  +-----+-----+
  |           |
Error       Error
conocido    desconocido
  |           |
  v           v
Retornar    Log error +
status y    retornar 500
mensaje     generico
```

Ver [Convenciones API](../../api/README.md) para el formato de errores.

---

## Health Check

```
GET /health

Respuesta (200 OK):
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "checks": {
    "database": "connected",
    "redis": "connected"
  }
}

Si alguno falla (503 Service Unavailable):
{
  "status": "degraded",
  "version": "1.0.0",
  "uptime": 3600,
  "checks": {
    "database": "connected",
    "redis": "disconnected"
  }
}
```

---

## Estructura de carpetas del modulo

```
src/core/gateway/
  middleware/
    request-id.middleware.ts
    logging.middleware.ts
    rate-limit.middleware.ts
    cors.middleware.ts
    tenant.middleware.ts
    error-handler.middleware.ts
    response-formatter.middleware.ts
  config/
    cors.config.ts
    rate-limit.config.ts
  app.ts                          <-- Punto de entrada, registro de rutas
  health.ts                       <-- Health check endpoint
  index.ts                        <-- Export del modulo
```

---

## Referencias

- [Convenciones API](../../api/README.md)
- [Modulo Auth](../auth/README.md)
- [Modulo Organization](../organization/README.md)
