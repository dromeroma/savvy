# Modulo de Organizaciones (Organization)

---

## Proposito

El modulo de Organization gestiona las entidades tenant del sistema. Cada organizacion representa una empresa o equipo que usa la plataforma. Funcionalidades principales:

- CRUD de organizaciones
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
| settings (jsonb) |        | created_at       |        | created_at       |
| created_at       |        | updated_at       |        | updated_at       |
| updated_at       |        +------------------+        +------------------+
| deleted_at       |
+------------------+
         |
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
| created_at       |
+------------------+
```

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
| POST | `/api/v1/organizations` | Crear organizacion | Autenticado |
| GET | `/api/v1/organizations` | Listar mis organizaciones | Autenticado |
| GET | `/api/v1/organizations/:id` | Obtener detalle de org | member |
| PUT | `/api/v1/organizations/:id` | Actualizar organizacion | admin |
| DELETE | `/api/v1/organizations/:id` | Eliminar organizacion | owner |
| GET | `/api/v1/organizations/:id/members` | Listar miembros | member |
| PUT | `/api/v1/organizations/:id/members/:uid` | Cambiar rol de miembro | admin |
| DELETE | `/api/v1/organizations/:id/members/:uid` | Remover miembro | admin |
| POST | `/api/v1/organizations/:id/invitations` | Enviar invitacion | admin |
| GET | `/api/v1/organizations/:id/invitations` | Listar invitaciones | admin |
| DELETE | `/api/v1/organizations/:id/invitations/:inv_id` | Cancelar invitacion | admin |
| POST | `/api/v1/invitations/:token/accept` | Aceptar invitacion | Autenticado |
| POST | `/api/v1/invitations/:token/reject` | Rechazar invitacion | Autenticado |

Ver [Endpoints detallados](../../api/organization-endpoints.md) para ejemplos de request/response.

---

## Flujo de creacion de organizacion

```
1. Usuario autenticado envia POST /api/v1/organizations
   { "name": "Mi Restaurante", "type": "business" }

2. Servidor valida:
   - Nombre no vacio, longitud 2-100 caracteres
   - Tipo valido ("business")
   - Generar slug unico a partir del nombre ("mi-restaurante")

3. Servidor crea (en transaccion):
   a) INSERT en `organizations` con los datos
   b) INSERT en `memberships` con rol "owner" para el usuario creador

4. Servidor responde:
   - 201 Created
   - Body: { data: { id, name, slug, type, ... } }
```

```
Usuario               Servidor                    Base de datos
  |                      |                              |
  | POST /organizations  |                              |
  | { name, type }       |                              |
  |--------------------->|                              |
  |                      |                              |
  |                      | BEGIN TRANSACTION             |
  |                      |----------------------------->|
  |                      |                              |
  |                      | INSERT organization           |
  |                      |----------------------------->|
  |                      |              org_id          |
  |                      |<-----------------------------|
  |                      |                              |
  |                      | INSERT membership             |
  |                      | (user, org, role=owner)       |
  |                      |----------------------------->|
  |                      |                              |
  |                      | COMMIT                        |
  |                      |----------------------------->|
  |                      |                              |
  | 201 Created          |                              |
  | { data: org }        |                              |
  |<---------------------|                              |
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
PUT /api/v1/organizations/:id/members/:uid
{ "role": "admin" }

Validaciones:
- El solicitante debe ser admin o owner
- No puede asignar un rol mayor al propio
- No puede degradar a alguien con rol mayor al propio
- No puede degradarse a si mismo si es el unico owner
```

### Remocion de miembro

```
DELETE /api/v1/organizations/:id/members/:uid

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
   | POST /invitations        |                    |                    |
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
   |                          | POST /invitations/:token/accept        |
   |                          |<---------------------------------------|
   |                          |                    |                    |
   |                          | 4. Validar token    |                    |
   |                          | 5. Crear membresia  |                    |
   |                          | 6. Marcar inv.      |                    |
   |                          |    como aceptada    |                    |
   |                          |                    |                    |
   |                          | 200 OK              |                    |
   |                          |--------------------------------------->|
   |                          |                    |                    |
```

### Estados de una invitacion

| Estado | Codigo | Descripcion |
|--------|--------|-------------|
| Pendiente | `pending` | Enviada, esperando respuesta |
| Aceptada | `accepted` | El invitado acepto y fue agregado como miembro |
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
src/core/organization/
  handlers/
    create-org.handler.ts
    get-org.handler.ts
    list-orgs.handler.ts
    update-org.handler.ts
    delete-org.handler.ts
    list-members.handler.ts
    update-member.handler.ts
    remove-member.handler.ts
    create-invitation.handler.ts
    list-invitations.handler.ts
    cancel-invitation.handler.ts
    accept-invitation.handler.ts
    reject-invitation.handler.ts
  services/
    organization.service.ts
    membership.service.ts
    invitation.service.ts
    slug.service.ts
  repositories/
    organization.repository.ts
    membership.repository.ts
    invitation.repository.ts
  schemas/
    create-org.schema.ts
    update-org.schema.ts
    create-invitation.schema.ts
    update-member.schema.ts
  routes.ts
  index.ts
```

---

## Referencias

- [Endpoints detallados de Organization](../../api/organization-endpoints.md)
- [Esquema de BD](../../database/schema.md)
- [Multi-tenancy](../../architecture/multi-tenancy.md)
