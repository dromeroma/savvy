# Esquema de Base de Datos - Fase 1

---

## Resumen

Este documento describe el esquema completo de base de datos para la Fase 1 de SavvyCore. Incluye las tablas fundamentales para autenticacion, organizaciones, membresias e invitaciones.

**Motor**: PostgreSQL 16
**Encoding**: UTF-8
**Collation**: en_US.UTF-8

---

## Diagrama general

```
+========================+       +========================+
|     organizations      |       |         users          |
+========================+       +========================+
| id          UUID    PK |       | id          UUID    PK |
| name        VARCHAR    |       | name        VARCHAR    |
| slug        VARCHAR UK |       | email       VARCHAR UK |
| type        VARCHAR    |       | password_hash VARCHAR  |
| settings    JSONB      |       | email_verified_at TZ   |
| created_at  TIMESTAMPTZ|       | last_login_at TIMESTMPZ|
| updated_at  TIMESTAMPTZ|       | created_at  TIMESTAMPTZ|
| deleted_at  TIMESTAMPTZ|       | updated_at  TIMESTAMPTZ|
+============+===========+       | deleted_at  TIMESTAMPTZ|
             |                   +============+===========+
             |                                |
             |        +======================+|
             |        |                       |
             v        v                       |
+========================+                    |
|      memberships       |                    |
+========================+                    |
| id          UUID    PK |                    |
| organization_id UUID FK|----+               |
| user_id     UUID    FK |--------+           |
| role        VARCHAR    |    |   |           |
| joined_at   TIMESTAMPTZ|   |   |           |
| created_at  TIMESTAMPTZ|   |   |           |
| updated_at  TIMESTAMPTZ|   |   |           |
+========================+   |   |           |
                              |   |           |
+========================+   |   |           |
|     refresh_tokens     |   |   |           |
+========================+   |   |           |
| id          UUID    PK |   |   |           |
| user_id     UUID    FK |---|---|---------->|
| token_hash  VARCHAR UK |   |               |
| family_id   UUID       |   |               |
| device_info VARCHAR    |   |               |
| ip_address  VARCHAR    |   |               |
| expires_at  TIMESTAMPTZ|   |               |
| revoked_at  TIMESTAMPTZ|   |               |
| created_at  TIMESTAMPTZ|   |               |
+========================+   |               |
                              |               |
+========================+   |               |
|      invitations       |   |               |
+========================+   |               |
| id          UUID    PK |   |               |
| organization_id UUID FK|---+               |
| email       VARCHAR    |                   |
| role        VARCHAR    |                   |
| token       VARCHAR UK |                   |
| invited_by  UUID    FK |------------------>|
| status      VARCHAR    |
| expires_at  TIMESTAMPTZ|
| accepted_at TIMESTAMPTZ|
| created_at  TIMESTAMPTZ|
+========================+
```

---

## Tabla: organizations

Almacena las organizaciones (tenants) del sistema.

```sql
CREATE TABLE organizations (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(120) NOT NULL UNIQUE,
    type        VARCHAR(20)  NOT NULL DEFAULT 'business'
                            CHECK (type IN ('personal', 'business')),
    settings    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ          DEFAULT NULL
);
```

| Columna | Tipo | Nullable | Default | Descripcion |
|---------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Identificador unico, usado como `organization_id` en otras tablas |
| `name` | VARCHAR(100) | NO | - | Nombre de la organizacion |
| `slug` | VARCHAR(120) | NO | - | Slug unico para URLs. Generado a partir del nombre |
| `type` | VARCHAR(20) | NO | `'business'` | Tipo: `personal` o `business` |
| `settings` | JSONB | NO | `'{}'` | Configuracion JSON (timezone, currency, features, branding) |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de creacion |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de ultima actualizacion |
| `deleted_at` | TIMESTAMPTZ | SI | `NULL` | Fecha de eliminacion logica (soft delete) |

**Indices**:

```sql
-- PK ya crea indice en id
CREATE UNIQUE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_type ON organizations(type) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_deleted_at ON organizations(deleted_at) WHERE deleted_at IS NOT NULL;
```

**Constraints**:
- `CHECK (type IN ('personal', 'business'))` -- Solo tipos validos.
- `UNIQUE (slug)` -- Slugs no se repiten.

---

## Tabla: users

Almacena los usuarios del sistema. Un usuario puede pertenecer a multiples organizaciones.

```sql
CREATE TABLE users (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(100) NOT NULL,
    email             VARCHAR(255) NOT NULL UNIQUE,
    password_hash     VARCHAR(255) NOT NULL,
    email_verified_at TIMESTAMPTZ          DEFAULT NULL,
    last_login_at     TIMESTAMPTZ          DEFAULT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ          DEFAULT NULL
);
```

| Columna | Tipo | Nullable | Default | Descripcion |
|---------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Identificador unico del usuario |
| `name` | VARCHAR(100) | NO | - | Nombre completo |
| `email` | VARCHAR(255) | NO | - | Email unico, usado para login |
| `password_hash` | VARCHAR(255) | NO | - | Hash bcrypt del password (cost 12) |
| `email_verified_at` | TIMESTAMPTZ | SI | `NULL` | Fecha de verificacion de email |
| `last_login_at` | TIMESTAMPTZ | SI | `NULL` | Fecha del ultimo login exitoso |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de creacion |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de ultima actualizacion |
| `deleted_at` | TIMESTAMPTZ | SI | `NULL` | Fecha de eliminacion logica |

**Indices**:

```sql
CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;
```

**Nota**: El indice unico en `email` es parcial (solo filas activas) para permitir que un email eliminado pueda re-registrarse.

---

## Tabla: memberships

Relaciona usuarios con organizaciones y define su rol.

```sql
CREATE TABLE memberships (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL DEFAULT 'member'
                                CHECK (role IN ('owner', 'admin', 'member')),
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, user_id)
);
```

| Columna | Tipo | Nullable | Default | Descripcion |
|---------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Identificador unico de la membresia |
| `organization_id` | UUID | NO | - | FK a `organizations.id` |
| `user_id` | UUID | NO | - | FK a `users.id` |
| `role` | VARCHAR(20) | NO | `'member'` | Rol: `owner`, `admin`, o `member` |
| `joined_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha en que el usuario se unio |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de creacion del registro |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de ultima actualizacion |

**Indices**:

```sql
CREATE UNIQUE INDEX idx_memberships_org_user ON memberships(organization_id, user_id);
CREATE INDEX idx_memberships_user_id ON memberships(user_id);
CREATE INDEX idx_memberships_org_role ON memberships(organization_id, role);
```

**Constraints**:
- `UNIQUE (organization_id, user_id)` -- Un usuario solo puede tener una membresia por organizacion.
- `CHECK (role IN ('owner', 'admin', 'member'))` -- Solo roles validos.
- `ON DELETE CASCADE` -- Si se elimina la org o el usuario, se elimina la membresia.

---

## Tabla: refresh_tokens

Almacena los refresh tokens para renovacion de sesiones.

```sql
CREATE TABLE refresh_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    family_id   UUID        NOT NULL,
    device_info VARCHAR(255)         DEFAULT NULL,
    ip_address  VARCHAR(45)          DEFAULT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ          DEFAULT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

| Columna | Tipo | Nullable | Default | Descripcion |
|---------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Identificador unico |
| `user_id` | UUID | NO | - | FK a `users.id` |
| `token_hash` | VARCHAR(255) | NO | - | Hash SHA-256 del token (nunca texto plano) |
| `family_id` | UUID | NO | - | ID de la familia de tokens (para deteccion de reuso) |
| `device_info` | VARCHAR(255) | SI | `NULL` | User-Agent del dispositivo |
| `ip_address` | VARCHAR(45) | SI | `NULL` | IP desde donde se creo (IPv4 o IPv6) |
| `expires_at` | TIMESTAMPTZ | NO | - | Fecha de expiracion (created_at + 7 dias) |
| `revoked_at` | TIMESTAMPTZ | SI | `NULL` | Fecha de revocacion (NULL = activo) |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de creacion |

**Indices**:

```sql
CREATE UNIQUE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_family_id ON refresh_tokens(family_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at)
    WHERE revoked_at IS NULL;
```

**Notas**:
- `token_hash` almacena el hash SHA-256, nunca el token en texto plano.
- `family_id` agrupa tokens de una misma cadena de rotacion. Si se detecta reuso de un token revocado, se revocan todos los tokens de la familia.
- El indice parcial en `expires_at` optimiza la limpieza de tokens expirados.

---

## Tabla: invitations

Almacena las invitaciones enviadas a usuarios para unirse a una organizacion.

```sql
CREATE TABLE invitations (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'member'
                                CHECK (role IN ('owner', 'admin', 'member')),
    token           VARCHAR(64)  NOT NULL UNIQUE,
    invited_by      UUID        NOT NULL REFERENCES users(id),
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending', 'accepted', 'rejected', 'expired', 'cancelled')),
    expires_at      TIMESTAMPTZ NOT NULL,
    accepted_at     TIMESTAMPTZ          DEFAULT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

| Columna | Tipo | Nullable | Default | Descripcion |
|---------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Identificador unico |
| `organization_id` | UUID | NO | - | FK a `organizations.id` |
| `email` | VARCHAR(255) | NO | - | Email del invitado |
| `role` | VARCHAR(20) | NO | `'member'` | Rol que tendra al aceptar |
| `token` | VARCHAR(64) | NO | - | Token unico para el link de invitacion (nanoid) |
| `invited_by` | UUID | NO | - | FK a `users.id` del usuario que invito |
| `status` | VARCHAR(20) | NO | `'pending'` | Estado de la invitacion |
| `expires_at` | TIMESTAMPTZ | NO | - | Fecha de expiracion (created_at + 7 dias) |
| `accepted_at` | TIMESTAMPTZ | SI | `NULL` | Fecha en que fue aceptada |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Fecha de creacion |

**Indices**:

```sql
CREATE UNIQUE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_org_id ON invitations(organization_id);
CREATE INDEX idx_invitations_email_status ON invitations(email, status)
    WHERE status = 'pending';
CREATE INDEX idx_invitations_org_email_pending
    ON invitations(organization_id, email)
    WHERE status = 'pending';
```

**Constraint notable**: El indice parcial `idx_invitations_org_email_pending` se usa para verificar rapidamente si ya existe una invitacion pendiente para el mismo email en la misma organizacion.

---

## Script completo de migracion (Fase 1)

```sql
-- ==========================================================
-- Migracion: Fase 1 - SavvyCore Base
-- Fecha: 2026-03-28
-- Descripcion: Tablas base para auth, orgs, membresias,
--              refresh tokens e invitaciones.
-- ==========================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- --------------------------------------------------------
-- Tabla: organizations
-- --------------------------------------------------------
CREATE TABLE organizations (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(120) NOT NULL UNIQUE,
    type        VARCHAR(20)  NOT NULL DEFAULT 'business'
                            CHECK (type IN ('personal', 'business')),
    settings    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ          DEFAULT NULL
);

CREATE INDEX idx_organizations_type ON organizations(type)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_deleted_at ON organizations(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- --------------------------------------------------------
-- Tabla: users
-- --------------------------------------------------------
CREATE TABLE users (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(100) NOT NULL,
    email             VARCHAR(255) NOT NULL,
    password_hash     VARCHAR(255) NOT NULL,
    email_verified_at TIMESTAMPTZ          DEFAULT NULL,
    last_login_at     TIMESTAMPTZ          DEFAULT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ          DEFAULT NULL
);

CREATE UNIQUE INDEX idx_users_email ON users(email)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_users_deleted_at ON users(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- --------------------------------------------------------
-- Tabla: memberships
-- --------------------------------------------------------
CREATE TABLE memberships (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL DEFAULT 'member'
                                CHECK (role IN ('owner', 'admin', 'member')),
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_memberships_org_user ON memberships(organization_id, user_id);
CREATE INDEX idx_memberships_user_id ON memberships(user_id);
CREATE INDEX idx_memberships_org_role ON memberships(organization_id, role);

-- --------------------------------------------------------
-- Tabla: refresh_tokens
-- --------------------------------------------------------
CREATE TABLE refresh_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    family_id   UUID        NOT NULL,
    device_info VARCHAR(255)         DEFAULT NULL,
    ip_address  VARCHAR(45)          DEFAULT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ          DEFAULT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_family_id ON refresh_tokens(family_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at)
    WHERE revoked_at IS NULL;

-- --------------------------------------------------------
-- Tabla: invitations
-- --------------------------------------------------------
CREATE TABLE invitations (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'member'
                                CHECK (role IN ('owner', 'admin', 'member')),
    token           VARCHAR(64)  NOT NULL UNIQUE,
    invited_by      UUID        NOT NULL REFERENCES users(id),
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending', 'accepted', 'rejected', 'expired', 'cancelled')),
    expires_at      TIMESTAMPTZ NOT NULL,
    accepted_at     TIMESTAMPTZ          DEFAULT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_invitations_org_id ON invitations(organization_id);
CREATE INDEX idx_invitations_email_status ON invitations(email, status)
    WHERE status = 'pending';
CREATE INDEX idx_invitations_org_email_pending
    ON invitations(organization_id, email)
    WHERE status = 'pending';

-- --------------------------------------------------------
-- Trigger: updated_at automatico
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_memberships_updated_at
    BEFORE UPDATE ON memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Referencias

- [Convenciones de BD](./conventions.md)
- [Multi-tenancy](../architecture/multi-tenancy.md)
