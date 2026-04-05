# Endpoints de Organizaciones

---

## Base URL

```
/api/v1/organizations
```

Todos los endpoints requieren autenticacion (`Authorization: Bearer <token>`) salvo que se indique lo contrario.

---

## GET /organizations/me

Obtiene el detalle de la organizacion activa (la del `org_id` en el JWT). El usuario debe ser miembro.

### Request

```http
GET /api/v1/organizations/me
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

## PATCH /organizations/me

Actualiza la organizacion activa. Requiere rol `admin` o `owner`.

### Request

```http
PATCH /api/v1/organizations/me
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

## GET /organizations/members

Lista los miembros de la organizacion activa. Requiere ser miembro.

### Request

```http
GET /api/v1/organizations/members?page=1&per_page=20
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

## POST /organizations/members/invite

Envia una invitacion por email para unirse a la organizacion activa. Requiere `admin` o `owner`.

### Request

```http
POST /api/v1/organizations/members/invite
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

## PATCH /organizations/members/{membership_id}/role

Cambia el rol de un miembro. Requiere `admin` o `owner`.

### Request

```http
PATCH /api/v1/organizations/members/bbb-222/role
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

## DELETE /organizations/members/{membership_id}

Remueve un miembro de la organizacion activa. Requiere `admin` o `owner`. Un miembro puede removerse a si mismo (abandonar la org).

### Request

```http
DELETE /api/v1/organizations/members/ccc-333
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

## POST /organizations/invitations/{token}/accept

Acepta una invitacion. El usuario debe estar autenticado. Si el email de la invitacion coincide con el del usuario autenticado, se crea la membresia y se actualiza la invitacion (`status = accepted`, `accepted_at = NOW()`).

### Request

```http
POST /api/v1/organizations/invitations/tok_abc123def456/accept
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
| 400 | `BAD_REQUEST` | La invitacion no esta en estado `pending` |
| 401 | `UNAUTHORIZED` | No autenticado |
| 403 | `FORBIDDEN` | El email del usuario no coincide con el de la invitacion |
| 404 | `NOT_FOUND` | Token invalido |
| 410 | `GONE` | La invitacion ha expirado |

---

## Referencias

- [Modulo Organization](../modules/organization/README.md)
- [Convenciones API](./README.md)
