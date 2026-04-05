# Convenciones de la API

---

## Resumen

Todas las APIs de SavvyCore siguen estas convenciones para garantizar consistencia, previsibilidad y facilidad de integracion.

---

## Principios

1. **RESTful**: Recursos como sustantivos, verbos HTTP como acciones.
2. **JSON**: Todas las respuestas son JSON con `Content-Type: application/json`.
3. **Versionado**: Todas las rutas bajo `/api/v1/`.
4. **Consistencia**: Toda respuesta sigue el mismo formato envelope.
5. **Seguridad**: HTTPS obligatorio, auth via JWT, headers de seguridad.

---

## URL Base

```
Desarrollo:  http://localhost:8000/api/v1/
Produccion:  https://api.savvycore.com/api/v1/
```

---

## Versionado

- Versionado por URL: `/api/v1/`, `/api/v2/`.
- Cambios retrocompatibles no requieren nueva version.
- Versiones deprecadas incluyen headers `Deprecation` y `Sunset`.

---

## Autenticacion

### Header de autorizacion

```
Authorization: Bearer <access_token>
```

### Endpoints publicos (sin auth)

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /health`

### Endpoints protegidos

Todos los demas endpoints requieren un JWT valido en el header `Authorization`.

---

## Formato de respuestas

### Respuesta exitosa (un recurso)

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Mi Empresa",
    "slug": "mi-empresa",
    "created_at": "2026-03-28T10:00:00.000Z"
  }
}
```

### Respuesta exitosa (lista de recursos)

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Mi Empresa"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Otra Empresa"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### Respuesta exitosa (sin datos)

```json
{
  "message": "Recurso eliminado exitosamente"
}
```

### Respuesta de creacion

- Status: `201 Created`

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Mi Empresa",
    "slug": "mi-empresa"
  }
}
```

---

## Formato de errores

Todos los errores siguen este formato:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos enviados no son validos",
    "details": [
      {
        "field": "email",
        "message": "El email no tiene un formato valido"
      },
      {
        "field": "password",
        "message": "La contrasena debe tener al menos 8 caracteres"
      }
    ]
  }
}
```

### Codigos de error estandar

| Codigo HTTP | Codigo de error | Descripcion |
|-------------|----------------|-------------|
| 400 | `VALIDATION_ERROR` | Datos de entrada invalidos |
| 400 | `BAD_REQUEST` | Peticion malformada |
| 401 | `UNAUTHORIZED` | Token ausente, invalido o expirado |
| 401 | `TOKEN_EXPIRED` | El access token expiro (el cliente debe hacer refresh) |
| 403 | `FORBIDDEN` | Sin permisos para esta accion |
| 403 | `INSUFFICIENT_PERMISSIONS` | El rol del usuario no permite esta accion |
| 404 | `NOT_FOUND` | Recurso no encontrado |
| 409 | `CONFLICT` | Conflicto (ej. email ya registrado, slug duplicado) |
| 409 | `ALREADY_EXISTS` | El recurso ya existe |
| 422 | `UNPROCESSABLE_ENTITY` | Datos validos sintacticamente pero con error de negocio |
| 429 | `RATE_LIMIT_EXCEEDED` | Demasiadas peticiones |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |
| 503 | `SERVICE_UNAVAILABLE` | Servicio temporalmente no disponible |

### Headers de error en rate limiting

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1711584900
```

---

## Paginacion

### Parametros de query

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Numero de pagina (1-based) |
| `per_page` | integer | 20 | Elementos por pagina (max 100) |
| `sort` | string | `created_at` | Campo por el cual ordenar |
| `order` | string | `desc` | Direccion: `asc` o `desc` |

### Ejemplo de peticion paginada

```
GET /api/v1/organizations/members?page=2&per_page=10&sort=joined_at&order=asc
```

### Objeto de paginacion en la respuesta

```json
{
  "pagination": {
    "page": 2,
    "per_page": 10,
    "total": 45,
    "total_pages": 5,
    "has_next": true,
    "has_prev": true
  }
}
```

### Reglas de paginacion

1. `per_page` maximo: 100 (si se pide mas, se limita a 100 silenciosamente).
2. `page` minimo: 1 (si se pide 0 o negativo, se usa 1).
3. Si `page` excede `total_pages`, se retorna `data: []` con la paginacion correcta.
4. Toda lista debe estar paginada -- no se permiten endpoints que retornen todos los registros.

---

## Filtros

### Formato de filtros en query params

```
GET /api/v1/pos/products?status=active&min_price=1000&max_price=5000
```

### Filtros comunes

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `search` | string | Busqueda por texto (nombre, email, etc.) |
| `status` | string | Filtrar por estado |
| `created_after` | ISO 8601 | Creados despues de esta fecha |
| `created_before` | ISO 8601 | Creados antes de esta fecha |

---

## Verbos HTTP

| Verbo | Uso | Idempotente | Body |
|-------|-----|-------------|------|
| GET | Obtener recurso(s) | Si | No |
| POST | Crear recurso | No | Si |
| PATCH | Actualizar parcialmente | Si | Si |
| DELETE | Eliminar recurso | Si | No |

### Convenciones de rutas

```
GET    /api/v1/resources            --> Listar recursos (paginado)
POST   /api/v1/resources            --> Crear recurso
GET    /api/v1/resources/:id        --> Obtener un recurso
PATCH  /api/v1/resources/:id        --> Actualizar recurso
DELETE /api/v1/resources/:id        --> Eliminar recurso

GET    /api/v1/resources/:id/sub    --> Listar sub-recursos
POST   /api/v1/resources/:id/sub    --> Crear sub-recurso
```

---

## Headers

### Headers de peticion requeridos

| Header | Valor | Obligatorio |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Si (en POST/PATCH) |
| `Authorization` | `Bearer <token>` | Si (rutas protegidas) |
| `Accept` | `application/json` | Recomendado |

### Headers de respuesta estandar

| Header | Descripcion |
|--------|-------------|
| `Content-Type` | `application/json; charset=utf-8` |
| `X-Request-ID` | ID unico de la peticion para trazabilidad |
| `X-RateLimit-Limit` | Limite de peticiones por ventana |
| `X-RateLimit-Remaining` | Peticiones restantes |
| `X-RateLimit-Reset` | Timestamp cuando se reinicia el limite |

---

## Formato de fechas

Todas las fechas en la API usan **ISO 8601** con timezone UTC:

```
2026-03-28T10:30:00.000Z
```

- En peticiones: aceptar ISO 8601 con o sin timezone (si falta, asumir UTC).
- En respuestas: siempre retornar con `Z` (UTC).

---

## Referencias

- [Endpoints de Auth](./auth-endpoints.md)
- [Endpoints de Organization](./organization-endpoints.md)
- [API Gateway](../modules/gateway/README.md)
