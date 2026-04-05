# Endpoints de Autenticacion

---

## Base URL

```
/api/v1/auth
```

---

## POST /register

Registra un nuevo usuario. Crea automaticamente una organizacion personal y devuelve tokens de acceso.

### Request

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "Juan Perez",
  "email": "juan@ejemplo.com",
  "password": "MiPassword123!"
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `name` | string | Si | 2-100 caracteres |
| `email` | string | Si | Formato email valido, unico en el sistema |
| `password` | string | Si | Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero |

### Response (201 Created)

```http
HTTP/1.1 201 Created
Content-Type: application/json
Set-Cookie: refresh_token=rt_abc123...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=604800

{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Juan Perez",
      "email": "juan@ejemplo.com",
      "created_at": "2026-03-28T10:00:00.000Z"
    },
    "organization": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Juan Perez",
      "slug": "juan-perez",
      "type": "personal"
    }
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `VALIDATION_ERROR` | Datos invalidos (email mal formado, password debil) |
| 409 | `ALREADY_EXISTS` | El email ya esta registrado |
| 429 | `RATE_LIMIT_EXCEEDED` | Mas de 3 registros por hora desde esta IP |

**Ejemplo de error**:

```json
{
  "error": {
    "code": "ALREADY_EXISTS",
    "message": "Ya existe una cuenta con este email",
    "details": [
      {
        "field": "email",
        "message": "El email juan@ejemplo.com ya esta registrado"
      }
    ]
  }
}
```

---

## POST /login

Inicia sesion con email y password.

### Request

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "juan@ejemplo.com",
  "password": "MiPassword123!"
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `email` | string | Si | Formato email valido |
| `password` | string | Si | No vacio |

### Response (200 OK)

```http
HTTP/1.1 200 OK
Content-Type: application/json
Set-Cookie: refresh_token=rt_def456...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=604800

{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Juan Perez",
      "email": "juan@ejemplo.com",
      "last_login_at": "2026-03-28T10:00:00.000Z"
    },
    "organization": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Mi Restaurante",
      "slug": "mi-restaurante",
      "type": "business",
      "role": "owner"
    }
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `VALIDATION_ERROR` | Datos invalidos |
| 401 | `UNAUTHORIZED` | Email no registrado o password incorrecto |
| 423 | `ACCOUNT_LOCKED` | Cuenta bloqueada por exceso de intentos fallidos |
| 429 | `RATE_LIMIT_EXCEEDED` | Mas de 5 intentos de login en 15 minutos |

**Ejemplo de error**:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Email o contrasena incorrectos"
  }
}
```

**Nota de seguridad**: El mensaje de error no indica si el email existe o no, para evitar enumeracion de cuentas.

---

## POST /refresh

Renueva el access token usando el refresh token de la cookie. El servidor calcula el hash SHA-256 del token recibido y lo busca en la tabla `refresh_tokens` por `token_hash`.

### Request

```http
POST /api/v1/auth/refresh
Cookie: refresh_token=rt_abc123...
```

No requiere body ni header `Authorization`.

### Response (200 OK)

```http
HTTP/1.1 200 OK
Content-Type: application/json
Set-Cookie: refresh_token=rt_ghi789...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=604800

{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Nota**: El refresh token en la cookie cambia (rotacion). El token anterior se revoca (`revoked_at = NOW()`). El nuevo token mantiene el mismo `family_id` para deteccion de reuso.

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 401 | `UNAUTHORIZED` | Refresh token ausente, invalido o expirado |
| 401 | `TOKEN_REUSE_DETECTED` | Se detecto reuso de un token revocado (posible robo) |

**Ejemplo de error por reuso**:

```json
{
  "error": {
    "code": "TOKEN_REUSE_DETECTED",
    "message": "Se detecto un uso anomalo de sesion. Por seguridad, todas las sesiones han sido cerradas. Por favor inicie sesion nuevamente."
  }
}
```

Cuando se detecta reuso, **todos los refresh tokens de la familia se revocan** (por `family_id`), forzando al usuario a hacer login de nuevo.

---

## POST /logout

Cierra la sesion actual revocando el refresh token (`revoked_at = NOW()`).

### Request

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Cookie: refresh_token=rt_abc123...
```

### Response (200 OK)

```http
HTTP/1.1 200 OK
Content-Type: application/json
Set-Cookie: refresh_token=; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=0

{
  "message": "Sesion cerrada exitosamente"
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 401 | `UNAUTHORIZED` | Access token invalido o expirado |

---

## GET /me

Obtiene la informacion del usuario autenticado y su organizacion activa.

### Request

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Juan Perez",
      "email": "juan@ejemplo.com",
      "email_verified_at": "2026-03-28T10:00:00.000Z",
      "created_at": "2026-03-28T10:00:00.000Z"
    },
    "organization": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Mi Restaurante",
      "slug": "mi-restaurante",
      "type": "business",
      "role": "owner"
    },
    "organizations": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "Mi Restaurante",
        "slug": "mi-restaurante",
        "type": "business",
        "role": "owner"
      },
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Juan Perez",
        "slug": "juan-perez",
        "type": "personal",
        "role": "owner"
      }
    ]
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 401 | `UNAUTHORIZED` | Access token invalido o expirado |

---

## PATCH /me

Actualiza la informacion del perfil del usuario autenticado.

### Request

```http
PATCH /api/v1/auth/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Juan Carlos Perez"
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `name` | string | No | 2-100 caracteres (si se envia) |

### Response (200 OK)

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Juan Carlos Perez",
    "email": "juan@ejemplo.com",
    "updated_at": "2026-03-28T11:00:00.000Z"
  }
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `VALIDATION_ERROR` | Datos invalidos |
| 401 | `UNAUTHORIZED` | Access token invalido |

---

## POST /change-password

Cambia la contrasena del usuario autenticado. Requiere la contrasena actual para confirmar.

### Request

```http
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "MiPassword123!",
  "new_password": "NuevoPassword456!"
}
```

| Campo | Tipo | Obligatorio | Validacion |
|-------|------|-------------|-----------|
| `current_password` | string | Si | No vacio |
| `new_password` | string | Si | Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero |

### Response (200 OK)

```json
{
  "message": "Contrasena actualizada exitosamente"
}
```

### Errores posibles

| Status | Codigo | Cuando |
|--------|--------|--------|
| 400 | `VALIDATION_ERROR` | Nueva contrasena no cumple requisitos |
| 401 | `UNAUTHORIZED` | Access token invalido o contrasena actual incorrecta |

---

## Resumen de flujos

```
REGISTRO:
  POST /register --> 201 + access_token + refresh_token cookie

ACCESO DIARIO:
  POST /login --> 200 + access_token + refresh_token cookie

USAR LA API:
  GET /any-endpoint + Authorization: Bearer <access_token>

CUANDO EL ACCESS TOKEN EXPIRA (cada 15 min):
  POST /refresh (con cookie) --> 200 + nuevo access_token + nueva cookie

VER PERFIL:
  GET /me --> 200 + datos del usuario y organizacion activa

ACTUALIZAR PERFIL:
  PATCH /me --> 200 + datos actualizados

CAMBIAR CONTRASENA:
  POST /change-password --> 200

CERRAR SESION:
  POST /logout --> 200 + cookie eliminada
```

---

## Referencias

- [Modulo Auth](../modules/auth/README.md)
- [Convenciones API](./README.md)
