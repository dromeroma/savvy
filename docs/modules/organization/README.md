# Modulo de Organizaciones (Organization)

---

## Proposito

El modulo de Organization gestiona las entidades tenant del sistema. Cada organizacion representa una empresa o equipo que usa la plataforma. Funcionalidades principales:

- Consulta y actualizacion de la organizacion activa
- Gestion de membresias (usuarios dentro de una org)
- Sistema de invitaciones
- Configuracion por organizacion

---

## Modelo de datos

### Diagrama de relaciones

```
+------------------+        +------------------+        +------------------+
|   organizations  |        |   memberships    |        |     users        |
+------------------+        +------------------+        +------------------+
| id (PK)          |<------o| organization_id  |o------>| id (PK)          |
| name             |        | user_id          |        | name             |
| slug             |        | role             |        | email            |
| type             |        | joined_at        |        | password_hash    |
| settings (jsonb) |        | created_at       |        | email_verified_at|
| created_at       |        | updated_at       |        | last_login_at    |
| updated_at       |        +------------------+        | created_at       |
| deleted_at       |                                    | updated_at       |
+------------------+                                    | deleted_at       |
         |                                              +------------------+
         |
         o
+------------------+
|   invitations    |
+------------------+
| id (PK)          |
| organization_id  |
| email            |
| role             |
| token            |
| invited_by       |
| status           |
| expires_at       |
| accepted_at      |
| created_at       |
+------------------+
```

**Nota importante**: Los usuarios son **globales** -- no tienen FK directa a organizaciones. Un usuario se relaciona con organizaciones exclusivamente a traves de la tabla `memberships`. Un usuario puede pertenecer a multiples organizaciones.

### Tipos de organizacion

| Tipo | Codigo | Descripcion |
|------|--------|-------------|
| Personal | `personal` | Creada automaticamente al registrarse. Una por usuario. No se puede eliminar. |
| Empresa | `business` | Creada manualmente. Puede tener multiples miembros. |

### Configuracion por organizacion (settings)

El campo `settings` es JSONB y almacena configuracion especifica:

```json
{
  "timezone": "America/Bogota",
  "currency": "COP",
  "language": "es",
  "features": {
    "pos": true,
    "logistics": false,
    "inventory": true
  },
  "branding": {
    "logo_url": null,
    "primary_color": "#2563EB"
  }
}
```

---

## Endpoints

| Metodo | Ruta | Descripcion | Rol minimo |
|--------|------|-------------|-----------|
| GET | `/api/v1/organizations/me` | Obtener organizacion activa | member |
| PATCH | `/api/v1/organizations/me` | Actualizar organizacion activa | admin |
| GET | `/api/v1/organizations/members` | Listar miembros de la org activa | member |
| POST | `/api/v1/organizations/members/invite` | Enviar invitacion | admin |
| PATCH | `/api/v1/organizations/members/{membership_id}/role` | Cambiar rol de miembro | admin |
| DELETE | `/api/v1/organizations/members/{membership_id}` | Remover miembro | admin |
| POST | `/api/v1/organizations/invitations/{token}/accept` | Aceptar invitacion | Autenticado |

Ver [Endpoints detallados](../../api/organization-endpoints.md) para ejemplos de request/response.

---

## Flujo de consulta de organizacion activa

```
1. Usuario autenticado envia GET /api/v1/organizations/me
   (El org_id viene del JWT)

2. Servidor:
   - Extrae org_id del JWT via dependency get_org_id
   - Busca la organizacion en BD
   - Retorna los datos de la organizacion activa

3. Servidor responde:
   - 200 OK
   - Body: { data: { id, name, slug, type, settings, ... } }
```

---

## Gestion de membresias

### Reglas de negocio

1. Un usuario puede pertenecer a **multiples organizaciones**.
2. Cada membresia tiene exactamente **un rol** (`owner`, `admin`, `member`).
3. Toda organizacion debe tener **al menos un owner**.
4. Un owner **no puede removerse** a si mismo si es el unico owner.
5. Un admin puede cambiar roles **hasta admin** (no puede crear owners).
6. Solo un owner puede **transferir ownership** o **promover a owner**.
7. Al remover un miembro, sus datos en la org se mantienen (auditoria).

### Cambio de rol

```
PATCH /api/v1/organizations/members/{membership_id}/role
{ "role": "admin" }

Validaciones:
- El solicitante debe ser admin o owner
- No puede asignar un rol mayor al propio
- No puede degradar a alguien con rol mayor al propio
- No puede degradarse a si mismo si es el unico owner
```

### Remocion de miembro

```
DELETE /api/v1/organizations/members/{membership_id}

Validaciones:
- El solicitante debe ser admin o owner
- No puede remover a alguien con rol mayor al propio
- No puede remover al unico owner de la org
- Un miembro puede removerse a si mismo (abandonar la org)
```

---

## Sistema de invitaciones

### Flujo completo de invitacion

```
Admin/Owner                Servidor              Email              Invitado
   |                          |                    |                    |
   | POST /members/invite     |                    |                    |
   | { email, role }          |                    |                    |
   |------------------------->|                    |                    |
   |                          |                    |                    |
   |                          | 1. Validar:        |                    |
   |                          |    - email valido   |                    |
   |                          |    - no es miembro  |                    |
   |                          |    - no hay inv.    |                    |
   |                          |      pendiente      |                    |
   |                          |                    |                    |
   |                          | 2. Crear invitacion |                    |
   |                          |    token = nanoid() |                    |
   |                          |    expires = 7 dias |                    |
   |                          |    status = pending |                    |
   |                          |                    |                    |
   |                          | 3. Enviar email     |                    |
   |                          |------------------->|                    |
   |                          |                    | Email con link     |
   |                          |                    |------------------->|
   |                          |                    |                    |
   |  201 Created             |                    |                    |
   |<-------------------------|                    |                    |
   |                          |                    |                    |
   |                          |                    |    Clic en link    |
   |                          |                    |                    |
   |                          | POST /invitations/{token}/accept       |
   |                          |<---------------------------------------|
   |                          |                    |                    |
   |                          | 4. Validar token    |                    |
   |                          | 5. Crear membresia  |                    |
   |                          | 6. Actualizar inv.  |                    |
   |                          |    status=accepted   |                    |
   |                          |    accepted_at=NOW() |                    |
   |                          |                    |                    |
   |                          | 200 OK              |                    |
   |                          |--------------------------------------->|
   |                          |                    |                    |
```

### Estados de una invitacion

| Estado | Codigo | Descripcion |
|--------|--------|-------------|
| Pendiente | `pending` | Enviada, esperando respuesta |
| Aceptada | `accepted` | El invitado acepto y fue agregado como miembro. Se registra `accepted_at`. |
| Rechazada | `rejected` | El invitado rechazo la invitacion |
| Expirada | `expired` | Pasaron 7 dias sin respuesta |
| Cancelada | `cancelled` | El admin cancelo la invitacion |

### Reglas de invitaciones

1. Solo `admin` y `owner` pueden enviar invitaciones.
2. No se puede invitar a alguien que ya es miembro.
3. No se puede enviar invitacion duplicada (mismo email, misma org, estado pendiente).
4. Un admin solo puede invitar con rol `member` o `admin`.
5. Solo un owner puede invitar con rol `admin`.
6. Las invitaciones expiran en 7 dias.
7. Si el invitado no tiene cuenta, debe registrarse primero y luego aceptar.

---

## Slug de organizacion

El slug se genera automaticamente a partir del nombre y se usa para URLs amigables:

```
Nombre: "Mi Restaurante El Buen Sabor"
Slug:   "mi-restaurante-el-buen-sabor"

Si ya existe:
Slug:   "mi-restaurante-el-buen-sabor-1"
```

**Reglas del slug**:
- Lowercase, sin caracteres especiales, espacios reemplazados por guiones.
- Unico globalmente.
- No editable directamente (se regenera al cambiar el nombre).
- Longitud maxima: 100 caracteres.

---

## Estructura de carpetas del modulo

```
app/
  routers/
    organizations.py           <-- Router FastAPI con endpoints de org
  schemas/
    organization.py            <-- Schemas Pydantic (request/response)
  services/
    organization_service.py    <-- Logica de negocio
  models/
    organization.py            <-- Modelo SQLAlchemy de organizations
    membership.py              <-- Modelo SQLAlchemy de memberships
    invitation.py              <-- Modelo SQLAlchemy de invitations
```

---

## Referencias

- [Endpoints detallados de Organization](../../api/organization-endpoints.md)
- [Esquema de BD](../../database/schema.md)
- [Multi-tenancy](../../architecture/multi-tenancy.md)
