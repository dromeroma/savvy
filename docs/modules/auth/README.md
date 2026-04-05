# Modulo de Autenticacion (Auth)

---

## Proposito

El modulo de Auth es responsable de toda la gestion de identidad y acceso en SavvyCore:

- Registro de usuarios
- Inicio de sesion (login)
- Gestion de tokens JWT (access + refresh)
- Perfil de usuario (consulta y actualizacion)
- Cambio de contrasena
- Control de acceso basado en roles (RBAC)
- Cierre de sesion y revocacion de tokens

---

## Flujo de autenticacion JWT

SavvyCore utiliza un esquema de **doble token**:

| Token | Tipo | Duracion | Almacenamiento | Uso |
|-------|------|----------|----------------|-----|
| Access Token | JWT | 15 minutos | Memoria (frontend) | Autenticar cada peticion API |
| Refresh Token | Opaco (UUID) | 7 dias | HttpOnly cookie + BD (hash SHA-256) | Obtener nuevo access token |

### Diagrama del flujo de tokens

```
REGISTRO / LOGIN
=================

Cliente                          Servidor                         Base de Datos
  |                                |                                   |
  | POST /api/v1/auth/login        |                                   |
  | { email, password }            |                                   |
  |------------------------------->|                                   |
  |                                |                                   |
  |                                | 1. Validar credenciales           |
  |                                |---------------------------------->|
  |                                |          Usuario encontrado       |
  |                                |<----------------------------------|
  |                                |                                   |
  |                                | 2. Verificar password (bcrypt)    |
  |                                |                                   |
  |                                | 3. Generar Access Token (JWT)     |
  |                                |    - sub: user_id                 |
  |                                |    - org_id: org seleccionada     |
  |                                |    - role: rol en la org          |
  |                                |    - exp: now + 15min             |
  |                                |                                   |
  |                                | 4. Generar Refresh Token (UUID)   |
  |                                |    - Guardar hash SHA-256 en BD   |
  |                                |    - Registrar family_id,         |
  |                                |      device_info, ip_address      |
  |                                |---------------------------------->|
  |                                |          Token guardado           |
  |                                |<----------------------------------|
  |                                |                                   |
  |  200 OK                        |                                   |
  |  { access_token, user }        |                                   |
  |  Set-Cookie: refresh_token     |                                   |
  |<-------------------------------|                                   |
  |                                |                                   |


PETICION AUTENTICADA
=====================

Cliente                          Servidor
  |                                |
  | GET /api/v1/organizations/me   |
  | Authorization: Bearer <access> |
  |------------------------------->|
  |                                |
  |                                | 1. Verificar firma JWT
  |                                | 2. Verificar expiracion
  |                                | 3. Extraer user_id, org_id, role
  |                                | 4. Establecer contexto de organizacion
  |                                | 5. Verificar permisos RBAC
  |                                | 6. Ejecutar handler
  |                                |
  |  200 OK { data: [...] }       |
  |<-------------------------------|
  |                                |


REFRESH DEL TOKEN
==================

Cliente                          Servidor                         Base de Datos
  |                                |                                   |
  | POST /api/v1/auth/refresh      |                                   |
  | Cookie: refresh_token=<token>  |                                   |
  |------------------------------->|                                   |
  |                                |                                   |
  |                                | 1. Hash SHA-256 del token         |
  |                                | 2. Buscar token_hash en BD        |
  |                                |---------------------------------->|
  |                                |          Token encontrado         |
  |                                |<----------------------------------|
  |                                |                                   |
  |                                | 3. Verificar que no este expirado |
  |                                | 4. Verificar que revoked_at       |
  |                                |    sea NULL                       |
  |                                |                                   |
  |                                | 5. ROTACION: Revocar token viejo  |
  |                                |    (SET revoked_at = NOW())       |
  |                                |---------------------------------->|
  |                                |                                   |
  |                                | 6. Crear nuevo refresh token      |
  |                                |    (mismo family_id)              |
  |                                |---------------------------------->|
  |                                |                                   |
  |                                | 7. Generar nuevo access token     |
  |                                |                                   |
  |  200 OK                        |                                   |
  |  { access_token }              |                                   |
  |  Set-Cookie: refresh_token     |                                   |
  |  (nuevo)                       |                                   |
  |<-------------------------------|                                   |
  |                                |                                   |
```

### Rotacion de refresh tokens

Cada vez que se usa un refresh token, este se **revoca** (se establece `revoked_at`) y se emite uno nuevo con el mismo `family_id`. Esto limita la ventana de ataque si un refresh token es robado:

```
Uso normal:
  Token A (activo) ---> Refresh ---> Token A (revoked_at = NOW()) + Token B (activo)
  Token B (activo) ---> Refresh ---> Token B (revoked_at = NOW()) + Token C (activo)

Deteccion de robo:
  Si Token A (revocado) se intenta usar de nuevo:
    --> ALERTA: posible robo de token
    --> Revocar TODA la familia de tokens (por family_id)
    --> Forzar re-login
```

---

## Estructura del Access Token (JWT)

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@ejemplo.com",
    "org_id": "660e8400-e29b-41d4-a716-446655440001",
    "role": "admin",
    "iat": 1711584000,
    "exp": 1711584900
  }
}
```

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `sub` | UUID | ID del usuario |
| `email` | string | Email del usuario |
| `org_id` | UUID | ID de la organizacion activa |
| `role` | string | Rol del usuario en la organizacion |
| `iat` | number | Timestamp de emision |
| `exp` | number | Timestamp de expiracion (iat + 15min) |

---

## Endpoints

| Metodo | Ruta | Descripcion | Auth requerida |
|--------|------|-------------|----------------|
| POST | `/api/v1/auth/register` | Registrar nuevo usuario | No |
| POST | `/api/v1/auth/login` | Iniciar sesion | No |
| POST | `/api/v1/auth/refresh` | Renovar access token | Cookie refresh_token |
| POST | `/api/v1/auth/logout` | Cerrar sesion | Si |
| GET | `/api/v1/auth/me` | Obtener usuario actual | Si |
| PATCH | `/api/v1/auth/me` | Actualizar perfil del usuario | Si |
| POST | `/api/v1/auth/change-password` | Cambiar contrasena | Si |

Ver [Endpoints detallados de Auth](../../api/auth-endpoints.md) para ejemplos de request/response.

---

## Flujo de registro

```
1. Cliente envia POST /api/v1/auth/register
   {
     "name": "Juan Perez",
     "email": "juan@ejemplo.com",
     "password": "MiPassword123!"
   }

2. Servidor valida:
   - Email no registrado previamente
   - Password cumple requisitos (min 8 chars, 1 mayuscula, 1 numero)
   - Nombre no vacio

3. Servidor crea (en transaccion):
   a) Usuario en tabla `users` (password hasheado con bcrypt, cost 12)
   b) Organizacion personal en tabla `organizations` (type: personal)
   c) Membresia en tabla `memberships` (role: owner)
   d) Refresh token en tabla `refresh_tokens` (token_hash SHA-256)

4. Servidor responde:
   - 201 Created
   - Body: { access_token, user: { id, name, email } }
   - Cookie: refresh_token (HttpOnly, Secure, SameSite=Strict, Max-Age=7d)
```

### Diagrama del flujo de registro

```
+--------+     +-----------+     +-----------+     +----------+     +----------+
| Validar|---->| Crear     |---->| Crear Org |---->| Crear    |---->| Generar  |
| Input  |     | Usuario   |     | Personal  |     | Membresia|     | Tokens   |
+--------+     +-----------+     +-----------+     +----------+     +----------+
                    |                 |                  |
                    v                 v                  v
              [users table]    [organizations]    [memberships]
                                                        |
                                                        v
                                                  [refresh_tokens]
```

---

## Flujo de login

```
1. Cliente envia POST /api/v1/auth/login
   {
     "email": "juan@ejemplo.com",
     "password": "MiPassword123!"
   }

2. Servidor valida:
   - Buscar usuario por email
   - Comparar password con hash (bcrypt.compare)
   - Si falla: incrementar contador de intentos fallidos
   - Si supera 5 intentos en 15 min: bloquear temporalmente

3. Servidor determina organizacion:
   - Si el usuario tiene una sola org: seleccionarla automaticamente
   - Si tiene multiples orgs: usar la ultima org activa o la personal

4. Servidor genera tokens:
   - Access token con org_id y role de la org seleccionada
   - Refresh token nuevo (hash SHA-256, family_id, device_info, ip_address)

5. Servidor responde:
   - 200 OK
   - Body: { access_token, user, organization }
   - Cookie: refresh_token
```

---

## RBAC (Control de acceso basado en roles)

### Roles disponibles

| Rol | Codigo | Nivel | Descripcion |
|-----|--------|-------|-------------|
| **Owner** | `owner` | 100 | Creador de la organizacion. Control total, incluyendo eliminar la org y gestionar billing. |
| **Admin** | `admin` | 50 | Administrador. Puede gestionar miembros, configuracion, y todos los datos de la org. |
| **Member** | `member` | 10 | Miembro estandar. Acceso a funcionalidades operativas segun la app. |

### Jerarquia de permisos

```
owner (nivel 100)
  |
  |-- Eliminar organizacion
  |-- Gestionar billing/suscripcion
  |-- Transferir ownership
  |-- Todo lo de admin
  |
  +-- admin (nivel 50)
        |
        |-- Invitar/remover miembros
        |-- Cambiar roles (hasta admin)
        |-- Configurar la organizacion
        |-- Todo lo de member
        |
        +-- member (nivel 10)
              |
              |-- Acceder a funcionalidades de la app
              |-- Ver datos de la organizacion
              |-- Editar datos propios
              |-- Acciones operativas (ventas, pedidos, etc.)
```

### Middleware de autorizacion

El middleware RBAC verifica el rol del usuario antes de ejecutar el handler:

```
Peticion con JWT (role: "member")
          |
          v
  [RBAC Dependency]
          |
  Ruta requiere: "admin"
          |
  member (10) >= admin (50)?
          |
         NO --> 403 Forbidden
          |     { "error": "INSUFFICIENT_PERMISSIONS" }
```

### Tabla de permisos por endpoint

| Endpoint | owner | admin | member |
|----------|-------|-------|--------|
| GET /organizations/me | Si | Si | Si |
| PATCH /organizations/me | Si | Si | No |
| GET /organizations/members | Si | Si | Si |
| POST /organizations/members/invite | Si | Si | No |
| PATCH /organizations/members/{id}/role | Si | Si | No |
| DELETE /organizations/members/{id} | Si | Si | No |

---

## Seguridad

### Almacenamiento de passwords

- Algoritmo: **bcrypt** con cost factor 12.
- Nunca almacenar passwords en texto plano.
- Nunca loguear passwords ni tokens.

### Almacenamiento de refresh tokens

- Se almacena el **hash SHA-256** del token, nunca el token en texto plano.
- Cada token tiene un `family_id` para agrupar cadenas de rotacion.
- Se registra `device_info` (User-Agent) e `ip_address` para auditoria.
- Revocacion mediante `revoked_at` (timestamp nullable, no booleano).

### Proteccion contra ataques

| Ataque | Mitigacion |
|--------|-----------|
| Brute force | Rate limiting + bloqueo temporal (5 intentos / 15 min) |
| Token theft (access) | Expiracion corta (15 min), HTTPS obligatorio |
| Token theft (refresh) | HttpOnly cookie, rotacion, deteccion de reuso via family_id |
| XSS | Access token en memoria (no localStorage), CSP headers |
| CSRF | SameSite=Strict en cookies, validar Origin header |
| Timing attacks | Comparacion constant-time en bcrypt y JWT |

### Headers de seguridad

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
Content-Security-Policy: default-src 'self'
```

---

## Estructura de carpetas del modulo

```
app/
  routers/
    auth.py                    <-- Router FastAPI con endpoints de auth
  schemas/
    auth.py                    <-- Schemas Pydantic (request/response)
  services/
    auth_service.py            <-- Logica de negocio principal
  models/
    user.py                    <-- Modelo SQLAlchemy de users
    refresh_token.py           <-- Modelo SQLAlchemy de refresh_tokens
  core/
    security.py                <-- JWT, hashing de passwords
    dependencies.py            <-- get_current_user, get_org_id
```

---

## Referencias

- [Endpoints detallados de Auth](../../api/auth-endpoints.md)
- [Esquema de BD](../../database/schema.md)
- [Convenciones API](../../api/README.md)
