# Modulo API Gateway

---

## Proposito

El API Gateway es el punto de entrada unico para todas las peticiones HTTP hacia SavvyCore. Su responsabilidad es:

- Ejecutar un pipeline de middlewares y dependencies de FastAPI
- Enrutar peticiones al router correcto
- Gestionar versionado de la API
- Aplicar politicas transversales (seguridad, rate limiting, logging)

---

## Pipeline de middleware

Cada peticion pasa por los siguientes middlewares/dependencies en orden. Si cualquiera rechaza la peticion, la cadena se detiene y se retorna el error al cliente.

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
| 2. Rate Limiting  |  Limita peticiones por IP (global) y por organizacion (si autenticado).
|                   |  - Global: 100 req/min por IP
|                   |  - Por organizacion: segun plan (1000-10000 req/min)
|                   |  - Por endpoint: configurable (ej. login: 5 req/min)
+-------------------+
        |
        v
+-------------------+
| 3. CORS           |  Configura origenes permitidos, metodos, headers.
|                   |  - Dev: http://localhost:*
|                   |  - Prod: dominios registrados por organizacion
+-------------------+
        |
        v
+-------------------+
| 4. Body Parser    |  FastAPI parsea automaticamente el body (JSON).
|                   |  - Limite de tamano: 1MB por defecto
|                   |  - Content-Type: application/json
+-------------------+
        |
        v
+-------------------+
| 5. Authentication |  Dependency que valida el JWT del header Authorization.
| (get_current_user)|  Si la ruta es publica, no se aplica.
|                   |  Si el JWT es invalido o expirado: 401.
+-------------------+
        |
        v
+-------------------+
| 6. Organization   |  Dependency get_org_id que extrae org_id del JWT.
| Resolution        |  Establece SET app.current_org en PostgreSQL.
| (get_org_id)      |  Adjunta org_id al contexto de la peticion.
+-------------------+
        |
        v
+-------------------+
| 7. Authorization  |  Dependency que verifica que el rol del usuario permite
| (RBAC)            |  acceder a esta ruta. Si no tiene permiso: 403.
+-------------------+
        |
        v
+-------------------+
| 8. Validation     |  Pydantic valida body, query params y path params
|                   |  automaticamente contra los schemas definidos.
|                   |  Si falla: 422.
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

### Estructura de rutas (13 endpoints)

```
/api/v1/
  auth/
    POST   /register              --> Auth.register
    POST   /login                 --> Auth.login
    POST   /refresh               --> Auth.refresh
    POST   /logout                --> Auth.logout
    GET    /me                    --> Auth.getProfile
    PATCH  /me                    --> Auth.updateProfile
    POST   /change-password       --> Auth.changePassword

  organizations/
    GET    /me                    --> Org.getCurrent
    PATCH  /me                    --> Org.updateCurrent
    GET    /members               --> Org.listMembers
    POST   /members/invite        --> Org.inviteMember
    PATCH  /members/{id}/role     --> Org.updateMemberRole
    DELETE /members/{id}          --> Org.removeMember
    POST   /invitations/{token}/accept --> Org.acceptInvitation

  # Rutas de apps SaaS (futuras)
  pos/
    ...                           --> Modulo POS
  logistics/
    ...                           --> Modulo Logistics
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

Cada modulo exporta su router que el gateway registra en la aplicacion FastAPI:

```python
# app/routers/auth.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register")
async def register(...): ...

@router.post("/login")
async def login(...): ...

@router.post("/refresh")
async def refresh(...): ...

@router.post("/logout")
async def logout(...): ...

@router.get("/me")
async def get_profile(...): ...

@router.patch("/me")
async def update_profile(...): ...

@router.post("/change-password")
async def change_password(...): ...


# app/routers/organizations.py
router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])

@router.get("/me")
async def get_current_org(...): ...

# ... etc.


# app/main.py
from fastapi import FastAPI
from app.routers import auth, organizations

app = FastAPI()

# Middlewares globales
app.add_middleware(CORSMiddleware, ...)

# Routers
app.include_router(auth.router)
app.include_router(organizations.router)
```

---

## Rate Limiting

### Configuracion

| Ambito | Limite | Ventana | Almacenamiento |
|--------|--------|---------|----------------|
| Global por IP | 100 req | 1 minuto | Redis |
| Por organizacion | Segun plan | 1 minuto | Redis |
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
  "path": "/api/v1/organizations/members/invite",
  "status": 201,
  "duration_ms": 45,
  "ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "user_id": "550e8400-...",
  "org_id": "660e8400-...",
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
app/
  middleware/
    logging.py                  <-- Middleware de logging y request ID
    rate_limit.py               <-- Middleware de rate limiting
  core/
    config.py                   <-- Configuracion CORS, rate limits, etc.
    dependencies.py             <-- get_current_user, get_org_id
  main.py                       <-- Punto de entrada, registro de routers
```

---

## Referencias

- [Convenciones API](../../api/README.md)
- [Modulo Auth](../auth/README.md)
- [Modulo Organization](../organization/README.md)
