# Endpoints de Organizaciones

---

## Base URL

```
/api/v1/organizations
/api/v1/invitations
```

Todos los endpoints requieren autenticacion (`Authorization: Bearer <token>`) salvo que se indique lo contrario.

---

## POST /organizations

Crea una nueva organizacion. El usuario autenticado se convierte en owner automaticamente.

### Request

```http
POST /api/v1/organizations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Mi Restaurante El Buen Sabor"
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `name` | string | Si | 2-100 caracteres |

### Response (201 Created)

```http
HTTP/1.1 201 Created
Location: /api/v1/organizations/550e8400-e29b-41d4-a716-446655440000

{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Mi Restaurante El Buen Sabor",
    "slug": "mi-restaurante-el-buen-sabor",
    "type": "business",
    "settings": {},
    "created_at": "2026-03-28T10:00:00.000Z",
    "updated_at": "2026-03-28T10:00:00.000Z"
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `VALIDATION_ERROR` | Nombre vacio o fuera de rango |
| 401 | `UNAUTHORIZED` | Token invalido |
| 409 | `CONFLICT` | Slug generado ya existe (reintentar con variante) |

---

## GET /organizations

Lista las organizaciones a las que el usuario autenticado pertenece.

### Request

```http
GET /api/v1/organizations?page=1&per_page=20
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Mi Restaurante El Buen Sabor",
      "slug": "mi-restaurante-el-buen-sabor",
      "type": "business",
      "role": "owner",
      "members_count": 5,
      "created_at": "2026-03-28T10:00:00.000Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Juan Perez",
      "slug": "juan-perez",
      "type": "personal",
      "role": "owner",
      "members_count": 1,
      "created_at": "2026-03-28T09:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

## GET /organizations/:id

Obtiene el detalle de una organizacion. El usuario debe ser miembro.

### Request

```http
GET /api/v1/organizations/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Mi Restaurante El Buen Sabor",
    "slug": "mi-restaurante-el-buen-sabor",
    "type": "business",
    "settings": {
      "timezone": "America/Bogota",
      "currency": "COP",
      "language": "es"
    },
    "members_count": 5,
    "my_role": "owner",
    "created_at": "2026-03-28T10:00:00.000Z",
    "updated_at": "2026-03-28T10:00:00.000Z"
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 401 | `UNAUTHORIZED` | Token invalido |
| 403 | `FORBIDDEN` | El usuario no es miembro de esta organizacion |
| 404 | `NOT_FOUND` | La organizacion no existe |

---

## PUT /organizations/:id

Actualiza una organizacion. Requiere rol `admin` o `owner`.

### Request

```http
PUT /api/v1/organizations/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Restaurante El Buen Sabor - Sede Principal",
  "settings": {
    "timezone": "America/Bogota",
    "currency": "COP",
    "language": "es"
  }
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `name` | string | No | 2-100 caracteres (si se envia) |
| `settings` | object | No | Objeto JSON valido |

### Response (200 OK)

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Restaurante El Buen Sabor - Sede Principal",
    "slug": "restaurante-el-buen-sabor-sede-principal",
    "type": "business",
    "settings": {
      "timezone": "America/Bogota",
      "currency": "COP",
      "language": "es"
    },
    "updated_at": "2026-03-28T11:00:00.000Z"
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `VALIDATION_ERROR` | Datos invalidos |
| 403 | `INSUFFICIENT_PERMISSIONS` | Rol insuficiente (requiere admin) |
| 404 | `NOT_FOUND` | La organizacion no existe |

---

## DELETE /organizations/:id

Elimina una organizacion (soft delete). Solo el `owner` puede ejecutar esta accion. No se puede eliminar una organizacion de tipo `personal`.

### Request

```http
DELETE /api/v1/organizations/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "message": "Organizacion eliminada exitosamente"
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 403 | `INSUFFICIENT_PERMISSIONS` | No es owner |
| 404 | `NOT_FOUND` | No existe |
| 422 | `UNPROCESSABLE_ENTITY` | Es una organizacion personal (no eliminable) |

---

## GET /organizations/:id/members

Lista los miembros de una organizacion. Requiere ser miembro.

### Request

```http
GET /api/v1/organizations/550e8400-.../members?page=1&per_page=20
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "data": [
    {
      "id": "aaa-111",
      "user": {
        "id": "550e8400-...",
        "name": "Juan Perez",
        "email": "juan@ejemplo.com"
      },
      "role": "owner",
      "joined_at": "2026-03-28T10:00:00.000Z"
    },
    {
      "id": "bbb-222",
      "user": {
        "id": "660e8400-...",
        "name": "Maria Garcia",
        "email": "maria@ejemplo.com"
      },
      "role": "admin",
      "joined_at": "2026-03-28T12:00:00.000Z"
    },
    {
      "id": "ccc-333",
      "user": {
        "id": "770e8400-...",
        "name": "Carlos Lopez",
        "email": "carlos@ejemplo.com"
      },
      "role": "member",
      "joined_at": "2026-03-28T14:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 3,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

## PUT /organizations/:id/members/:user_id

Cambia el rol de un miembro. Requiere `admin` o `owner`.

### Request

```http
PUT /api/v1/organizations/550e8400-.../members/660e8400-...
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "role": "admin"
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `role` | string | Si | `owner`, `admin`, o `member` |

### Response (200 OK)

```json
{
  "data": {
    "id": "bbb-222",
    "user_id": "660e8400-...",
    "role": "admin",
    "updated_at": "2026-03-28T15:00:00.000Z"
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 403 | `INSUFFICIENT_PERMISSIONS` | Intenta asignar un rol mayor al propio |
| 404 | `NOT_FOUND` | El miembro no existe en esta org |
| 422 | `UNPROCESSABLE_ENTITY` | Intenta degradar al unico owner |

---

## DELETE /organizations/:id/members/:user_id

Remueve un miembro de la organizacion. Requiere `admin` o `owner`. Un miembro puede removerse a si mismo (abandonar la org).

### Request

```http
DELETE /api/v1/organizations/550e8400-.../members/770e8400-...
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "message": "Miembro removido exitosamente"
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 403 | `INSUFFICIENT_PERMISSIONS` | Intenta remover a alguien con rol mayor |
| 404 | `NOT_FOUND` | El miembro no existe |
| 422 | `UNPROCESSABLE_ENTITY` | Es el unico owner de la org |

---

## POST /organizations/:id/invitations

Envia una invitacion por email. Requiere `admin` o `owner`.

### Request

```http
POST /api/v1/organizations/550e8400-.../invitations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "email": "nuevo@ejemplo.com",
  "role": "member"
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `email` | string | Si | Formato email valido |
| `role` | string | No | `admin` o `member` (default: `member`) |

### Response (201 Created)

```json
{
  "data": {
    "id": "inv-123",
    "email": "nuevo@ejemplo.com",
    "role": "member",
    "status": "pending",
    "expires_at": "2026-04-04T10:00:00.000Z",
    "created_at": "2026-03-28T10:00:00.000Z"
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `VALIDATION_ERROR` | Email invalido |
| 403 | `INSUFFICIENT_PERMISSIONS` | Rol insuficiente |
| 409 | `ALREADY_EXISTS` | Ya es miembro de la org |
| 409 | `CONFLICT` | Ya hay una invitacion pendiente para este email |

---

## GET /organizations/:id/invitations

Lista las invitaciones de una organizacion. Requiere `admin` o `owner`.

### Request

```http
GET /api/v1/organizations/550e8400-.../invitations?status=pending
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "data": [
    {
      "id": "inv-123",
      "email": "nuevo@ejemplo.com",
      "role": "member",
      "status": "pending",
      "invited_by": {
        "id": "550e8400-...",
        "name": "Juan Perez"
      },
      "expires_at": "2026-04-04T10:00:00.000Z",
      "created_at": "2026-03-28T10:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

## DELETE /organizations/:id/invitations/:inv_id

Cancela una invitacion pendiente. Requiere `admin` o `owner`.

### Request

```http
DELETE /api/v1/organizations/550e8400-.../invitations/inv-123
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "message": "Invitacion cancelada exitosamente"
}
```

---

## POST /invitations/:token/accept

Acepta una invitacion. El usuario debe estar autenticado. Si el email de la invitacion coincide con el del usuario autenticado, se crea la membresia.

### Request

```http
POST /api/v1/invitations/tok_abc123def456/accept
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "data": {
    "organization": {
      "id": "550e8400-...",
      "name": "Mi Restaurante El Buen Sabor",
      "slug": "mi-restaurante-el-buen-sabor",
      "role": "member"
    },
    "message": "Te has unido a la organizacion exitosamente"
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `BAD_REQUEST` | La invitacion no esta en estado pendiente |
| 401 | `UNAUTHORIZED` | No autenticado |
| 403 | `FORBIDDEN` | El email del usuario no coincide con el de la invitacion |
| 404 | `NOT_FOUND` | Token invalido |
| 410 | `GONE` | La invitacion ha expirado |

---

## POST /invitations/:token/reject

Rechaza una invitacion.

### Request

```http
POST /api/v1/invitations/tok_abc123def456/reject
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "message": "Invitacion rechazada"
}
```

---

## Referencias

- [Modulo Organization](../modules/organization/README.md)
- [Convenciones API](./README.md)
