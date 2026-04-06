# SavvyGroups — Estructura Organizacional y Agrupacion

## Tabla de Contenidos

1. [Proposito](#proposito)
2. [Entidades del Modulo](#entidades-del-modulo)
3. [Scopes Organizacionales](#scopes-organizacionales)
4. [Liderazgo por Scope](#liderazgo-por-scope)
5. [Permisos por Scope](#permisos-por-scope)
6. [Tipos de Grupo](#tipos-de-grupo)
7. [Grupos](#grupos)
8. [Miembros de Grupo](#miembros-de-grupo)
9. [Groups vs Classes](#groups-vs-classes)
10. [Endpoints API](#endpoints-api)
11. [Apps Consumidoras](#apps-consumidoras)
12. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Proposito

SavvyGroups provee la infraestructura para **agrupar personas en estructuras jerarquicas reutilizables** a traves de todo el ecosistema. Resuelve dos problemas fundamentales:

1. **Estructura organizacional**: Definir la jerarquia geografica/administrativa (pais, zona, distrito, iglesia/sucursal).
2. **Agrupacion de personas**: Crear grupos flexibles (ministerios, departamentos, equipos, celulas) dentro de cualquier nivel de la estructura.

```
+--------------------------------------------------------------+
|                  JERARQUIA ORGANIZACIONAL                    |
|                                                              |
|  Pais (Colombia)                                             |
|    |                                                         |
|    +-- Zona Norte                                            |
|    |     |                                                   |
|    |     +-- Distrito Barranquilla                           |
|    |     |     |                                             |
|    |     |     +-- Iglesia Central  --> [Grupos internos]    |
|    |     |     +-- Iglesia Sur      --> [Grupos internos]    |
|    |     |                                                   |
|    |     +-- Distrito Cartagena                              |
|    |           |                                             |
|    |           +-- Iglesia Principal --> [Grupos internos]   |
|    |                                                         |
|    +-- Zona Sur                                              |
|          |                                                   |
|          +-- ...                                             |
+--------------------------------------------------------------+
```

---

## Entidades del Modulo

| Entidad              | Tabla                    | Descripcion                                         |
|----------------------|--------------------------|-----------------------------------------------------|
| Scope Organizacional | `organizational_scopes`  | Nodos de la jerarquia organizacional                |
| Lider de Scope       | `scope_leaders`          | Lideres asignados por scope con rol y periodo       |
| Tipo de Grupo        | `group_types`            | Plantilla de configuracion para grupos              |
| Grupo                | `groups`                 | Instancia de agrupacion de personas                 |
| Miembro de Grupo     | `group_members`          | Vinculacion persona-grupo con rol y periodo         |

---

## Scopes Organizacionales

### Tabla `organizational_scopes`

```sql
CREATE TABLE organizational_scopes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    parent_id       UUID REFERENCES organizational_scopes(id),
    scope_type      VARCHAR(30) NOT NULL CHECK (scope_type IN (
        'country', 'zone', 'district', 'church', 'branch', 'region', 'area'
    )),
    name            VARCHAR(200) NOT NULL,
    code            VARCHAR(50),
    leader_id       UUID REFERENCES people(id),    -- Lider principal (legacy, migrar a scope_leaders)
    address         TEXT,
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(100),
    phone           VARCHAR(30),
    email           VARCHAR(255),
    metadata        JSONB DEFAULT '{}',
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (organization_id, code)
);

CREATE INDEX idx_scopes_org ON organizational_scopes(organization_id);
CREATE INDEX idx_scopes_parent ON organizational_scopes(parent_id);
CREATE INDEX idx_scopes_type ON organizational_scopes(organization_id, scope_type);
```

### Jerarquia Tipica

```
scope_type = 'country'     -->  Pais donde opera la organizacion
    |
    +-- scope_type = 'zone'        -->  Division geografica grande
            |
            +-- scope_type = 'district'    -->  Subdivision administrativa
                    |
                    +-- scope_type = 'church'      -->  Unidad operativa final
```

La jerarquia es **flexible**: no todas las organizaciones necesitan todos los niveles. Una organizacion pequena puede tener solo un nivel `church`. Una denominacion grande puede usar los cuatro niveles.

### Reglas de Jerarquia

- Un scope de tipo `zone` solo puede ser hijo de `country`.
- Un scope de tipo `district` solo puede ser hijo de `zone`.
- Un scope de tipo `church`/`branch` solo puede ser hijo de `district` (o de `zone` si no hay distritos).
- La raiz (sin `parent_id`) siempre es de tipo `country`.

---

## Liderazgo por Scope

### Tabla `scope_leaders`

Cada scope puede tener **multiples lideres** con roles especificos y periodos de servicio:

```sql
CREATE TABLE scope_leaders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_id        UUID NOT NULL REFERENCES organizational_scopes(id) ON DELETE CASCADE,
    person_id       UUID NOT NULL REFERENCES people(id),
    role            VARCHAR(50) NOT NULL CHECK (role IN (
        'bishop', 'supervisor', 'district_pastor', 'pastor',
        'co_pastor', 'administrator', 'treasurer', 'secretary'
    )),
    started_at      DATE NOT NULL DEFAULT CURRENT_DATE,
    ended_at        DATE,           -- NULL = actualmente en funciones
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    -- No puede haber dos lideres con el mismo rol activo en el mismo scope
    UNIQUE (scope_id, role, person_id)
);

CREATE INDEX idx_scope_leaders_scope ON scope_leaders(scope_id);
CREATE INDEX idx_scope_leaders_person ON scope_leaders(person_id);
CREATE INDEX idx_scope_leaders_active ON scope_leaders(scope_id) WHERE ended_at IS NULL;
```

### Roles por Nivel de Scope

| scope_type | Roles Tipicos                                     |
|------------|---------------------------------------------------|
| `country`  | `bishop` (obispo general)                         |
| `zone`     | `supervisor` (supervisor de zona)                 |
| `district` | `district_pastor` (pastor de distrito)            |
| `church`   | `pastor`, `co_pastor`, `administrator`, `treasurer`, `secretary` |

### Historial de Liderazgo

El campo `ended_at` permite mantener un **historial completo** de quien ha liderado cada scope:

```
Iglesia Central - Historial de Pastores:
+------------------+--------------+------------+
| Persona          | Rol          | Periodo    |
+------------------+--------------+------------+
| Pastor Martinez  | pastor       | 2018-2022  |
| Pastor Rodriguez | pastor       | 2022-actual|
| Dra. Gomez       | co_pastor    | 2023-actual|
+------------------+--------------+------------+
```

---

## Permisos por Scope

El scope determina **que datos puede ver cada lider**. La regla es simple: **un lider ve todo lo que esta en su scope y en los scopes descendientes**.

```
+-------------------------------------------------------------------+
|  Obispo (country scope)                                           |
|  --> Ve TODAS las iglesias del pais                               |
|                                                                   |
|  +---------------------------------------------------------------+|
|  |  Supervisor (zone scope)                                      ||
|  |  --> Ve todas las iglesias de su zona                         ||
|  |                                                               ||
|  |  +-----------------------------------------------------------+||
|  |  |  Pastor de Distrito (district scope)                      |||
|  |  |  --> Ve todas las iglesias de su distrito                  |||
|  |  |                                                           |||
|  |  |  +-------------------------------------------------------+|||
|  |  |  |  Pastor (church scope)                                 ||||
|  |  |  |  --> Solo ve SU iglesia                                ||||
|  |  |  +-------------------------------------------------------+|||
|  |  +-----------------------------------------------------------+||
|  +---------------------------------------------------------------+|
+-------------------------------------------------------------------+
```

### Implementacion de Filtrado por Scope

```python
async def get_accessible_scope_ids(user_scope_id: UUID) -> list[UUID]:
    """
    Retorna todos los scope IDs accesibles para un usuario,
    incluyendo el scope actual y todos sus descendientes.
    """
    query = """
        WITH RECURSIVE scope_tree AS (
            SELECT id FROM organizational_scopes WHERE id = :scope_id
            UNION ALL
            SELECT os.id
            FROM organizational_scopes os
            JOIN scope_tree st ON os.parent_id = st.id
        )
        SELECT id FROM scope_tree;
    """
    return await db.fetch_all(query, {"scope_id": user_scope_id})
```

### Ejemplo Practico

Si el **Supervisor de Zona Norte** consulta `/people`:

1. El sistema identifica su `scope_id` (Zona Norte).
2. Obtiene todos los scopes descendientes (distritos y iglesias dentro de Zona Norte).
3. Filtra: `WHERE scope_id IN (:accessible_scope_ids)`.
4. Resultado: ve personas de todas las iglesias de su zona.

---

## Tipos de Grupo

### Tabla `group_types`

Los tipos de grupo definen **plantillas de configuracion** que establecen las capacidades de los grupos que se creen bajo ellos:

```sql
CREATE TABLE group_types (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id       UUID NOT NULL REFERENCES organizations(id),
    code                  VARCHAR(50) NOT NULL,       -- 'ministry', 'cell_group', 'committee', 'department'
    name                  VARCHAR(100) NOT NULL,      -- 'Ministerio', 'Celula', 'Comite'
    description           TEXT,

    -- Capacidades
    requires_classes      BOOLEAN DEFAULT FALSE,     -- Los miembros deben completar clases
    requires_attendance   BOOLEAN DEFAULT FALSE,     -- Se toma asistencia en reuniones
    requires_activities   BOOLEAN DEFAULT FALSE,     -- Se registran actividades
    max_members           INTEGER,                    -- Limite de miembros (NULL = sin limite)
    allow_hierarchy       BOOLEAN DEFAULT TRUE,       -- Permite sub-grupos

    metadata              JSONB DEFAULT '{}',
    status                VARCHAR(20) DEFAULT 'active',
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (organization_id, code)
);
```

### Ejemplos de Tipos de Grupo

| Codigo       | Nombre       | requires_classes | requires_attendance | max_members | allow_hierarchy |
|-------------|-------------|------------------|---------------------|-------------|-----------------|
| `ministry`  | Ministerio  | true             | true                | NULL        | true            |
| `cell_group`| Celula      | false            | true                | 12          | false           |
| `committee` | Comite      | false            | false               | 10          | false           |
| `department`| Departamento| false            | false               | NULL        | true            |
| `team`      | Equipo      | false            | false               | NULL        | false           |

### Capacidades Explicadas

- **`requires_classes`**: Para unirse al grupo, la persona debe haber completado ciertas clases (ej: un ministerio requiere completar "Principios de Fe").
- **`requires_attendance`**: El grupo registra asistencia en sus reuniones/actividades.
- **`requires_activities`**: El grupo programa y registra actividades.
- **`max_members`**: Limite maximo de miembros (util para celulas de tamano controlado).
- **`allow_hierarchy`**: Permite crear sub-grupos (ej: Ministerio de Alabanza > Equipo de Guitarra).

---

## Grupos

### Tabla `groups`

```sql
CREATE TABLE groups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    scope_id        UUID NOT NULL REFERENCES organizational_scopes(id),
    group_type_id   UUID NOT NULL REFERENCES group_types(id),
    parent_id       UUID REFERENCES groups(id),      -- Jerarquia de grupos
    leader_id       UUID REFERENCES people(id),      -- Lider del grupo
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    meeting_day     VARCHAR(15),                      -- 'monday', 'tuesday', etc.
    meeting_time    TIME,
    meeting_place   VARCHAR(200),
    metadata        JSONB DEFAULT '{}',
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'archived')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_groups_org ON groups(organization_id);
CREATE INDEX idx_groups_scope ON groups(scope_id);
CREATE INDEX idx_groups_type ON groups(group_type_id);
CREATE INDEX idx_groups_parent ON groups(parent_id);
CREATE INDEX idx_groups_leader ON groups(leader_id);
```

### Jerarquia de Grupos

Los grupos pueden tener sub-grupos cuando `allow_hierarchy = true` en su tipo:

```
Ministerio de Alabanza (group_type: ministry)
    |
    +-- Equipo de Guitarra (parent_id = Ministerio de Alabanza)
    +-- Equipo Vocal (parent_id = Ministerio de Alabanza)
    +-- Equipo de Sonido (parent_id = Ministerio de Alabanza)
```

---

## Miembros de Grupo

### Tabla `group_members`

```sql
CREATE TABLE group_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id        UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    person_id       UUID NOT NULL REFERENCES people(id),
    role            VARCHAR(50) DEFAULT 'member' CHECK (role IN (
        'leader', 'co_leader', 'secretary', 'treasurer', 'member'
    )),
    joined_at       DATE NOT NULL DEFAULT CURRENT_DATE,
    left_at         DATE,           -- NULL = miembro activo
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (group_id, person_id)
);

CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_person ON group_members(person_id);
CREATE INDEX idx_group_members_active ON group_members(group_id) WHERE left_at IS NULL;
```

### Roles dentro de un Grupo

| Rol          | Descripcion                                    |
|-------------|------------------------------------------------|
| `leader`    | Lider principal del grupo                      |
| `co_leader` | Co-lider o lider asistente                     |
| `secretary` | Secretario (toma notas, lista de asistencia)   |
| `treasurer` | Tesorero (manejo de finanzas del grupo)        |
| `member`    | Miembro regular                                |

### Historial de Membresia

Al igual que los lideres de scope, los miembros tienen `joined_at` y `left_at` para mantener historial:

```sql
-- Miembros activos del grupo
SELECT * FROM group_members WHERE group_id = :id AND left_at IS NULL;

-- Historial completo
SELECT * FROM group_members WHERE group_id = :id ORDER BY joined_at;
```

---

## Groups vs Classes

Es fundamental entender la diferencia entre **Grupos** (SavvyGroups) y **Clases** (SavvyChurch):

```
+-------------------------+----------------------------+
|       GRUPOS            |         CLASES             |
|    (SavvyGroups)        |      (SavvyChurch)         |
+-------------------------+----------------------------+
| Permanentes             | Temporales                 |
| Sin fecha de fin        | Con fecha inicio y fin     |
| Organizacionales        | Educativos                 |
| Ministerios, celulas    | Clases biblicas, cursos    |
| Membresia continua      | Matricula con estado       |
| Rol del miembro         | Nota/calificacion          |
| Modulo compartido       | Especifico de Church       |
| Reutilizable por apps   | Solo para apps educativas  |
+-------------------------+----------------------------+
```

### Ejemplo Concreto

- **Grupo "Ministerio de Alabanza"**: Es permanente. Los miembros entran y salen a lo largo de los anos. Se usa en SavvyChurch, pero podria usarse en cualquier organizacion con ministerios.

- **Clase "Principios de Fe - Enero 2026"**: Empezo el 15 de enero, termina el 15 de marzo. Tiene 20 estudiantes matriculados. Al finalizar, cada uno tiene un estado (completado, abandonado). Es logica exclusiva de educacion eclesiastica.

---

## Endpoints API

### Scopes Organizacionales

| Metodo | Ruta                              | Descripcion                            |
|--------|-----------------------------------|----------------------------------------|
| GET    | `/scopes`                         | Listar scopes (arbol jerarquico)       |
| POST   | `/scopes`                         | Crear scope                            |
| GET    | `/scopes/{id}`                    | Obtener scope con hijos                |
| PATCH  | `/scopes/{id}`                    | Actualizar scope                       |
| DELETE | `/scopes/{id}`                    | Desactivar scope                       |
| GET    | `/scopes/{id}/tree`               | Obtener arbol completo desde un scope  |
| GET    | `/scopes/{id}/leaders`            | Listar lideres del scope               |
| POST   | `/scopes/{id}/leaders`            | Asignar lider al scope                 |
| PATCH  | `/scopes/{id}/leaders/{lid}`      | Actualizar lider (ej: finalizar)       |

### Tipos de Grupo

| Metodo | Ruta                    | Descripcion                          |
|--------|-------------------------|--------------------------------------|
| GET    | `/group-types`          | Listar tipos de grupo                |
| POST   | `/group-types`          | Crear tipo de grupo                  |
| PATCH  | `/group-types/{id}`     | Actualizar tipo de grupo             |
| DELETE | `/group-types/{id}`     | Desactivar tipo de grupo             |

### Grupos

| Metodo | Ruta                              | Descripcion                            |
|--------|-----------------------------------|----------------------------------------|
| GET    | `/groups`                         | Listar grupos (filtro por scope, tipo) |
| POST   | `/groups`                         | Crear grupo                            |
| GET    | `/groups/{id}`                    | Obtener grupo con miembros             |
| PATCH  | `/groups/{id}`                    | Actualizar grupo                       |
| DELETE | `/groups/{id}`                    | Archivar grupo                         |
| GET    | `/groups/{id}/members`            | Listar miembros del grupo              |
| POST   | `/groups/{id}/members`            | Agregar miembro al grupo               |
| PATCH  | `/groups/{id}/members/{mid}`      | Actualizar miembro (rol, left_at)      |
| DELETE | `/groups/{id}/members/{mid}`      | Remover miembro del grupo              |
| GET    | `/groups/{id}/subgroups`          | Listar sub-grupos                      |

### Parametros de Consulta

```
GET /groups?scope_id=uuid&group_type_id=uuid&status=active&page=1&limit=20
GET /scopes?scope_type=church&parent_id=uuid
```

---

## Apps Consumidoras

### SavvyChurch

- **Ministerios**: Usa `group_type.code = 'ministry'` para crear ministerios de la iglesia.
- **Celulas**: Usa `group_type.code = 'cell_group'` para grupos de crecimiento.
- **Estructura denominacional**: Usa scopes para representar pais/zona/distrito/iglesia.
- **Liderazgo pastoral**: Usa `scope_leaders` para asignar pastores, co-pastores, supervisores.

### SavvyPOS

- **Sucursales**: Usa scopes de tipo `branch` para representar sucursales.
- **Equipos de venta**: Usa grupos para equipos de vendedores.

### Futuras Apps

- **SavvyHR**: Departamentos y equipos como grupos. Oficinas como scopes.
- **SavvyEducation**: Salones y secciones como grupos. Sedes como scopes.

---

## Ejemplos de Uso

### Crear Estructura Denominacional Completa

```python
# 1. Crear scope raiz (pais)
pais = await scope_service.create(
    organization_id=org_id,
    scope_type="country",
    name="Colombia",
    code="CO"
)

# 2. Crear zona
zona_norte = await scope_service.create(
    organization_id=org_id,
    parent_id=pais.id,
    scope_type="zone",
    name="Zona Norte",
    code="ZN"
)

# 3. Crear distrito
distrito_baq = await scope_service.create(
    organization_id=org_id,
    parent_id=zona_norte.id,
    scope_type="district",
    name="Distrito Barranquilla",
    code="DBQ"
)

# 4. Crear iglesia
iglesia_central = await scope_service.create(
    organization_id=org_id,
    parent_id=distrito_baq.id,
    scope_type="church",
    name="Iglesia Central",
    code="IC-BQ"
)

# 5. Asignar pastor
await scope_leader_service.assign(
    scope_id=iglesia_central.id,
    person_id=pastor_rodriguez.id,
    role="pastor",
    started_at="2022-01-15"
)
```

### Crear Ministerio con Miembros

```python
# 1. Asegurar que existe el tipo de grupo 'ministry'
ministry_type = await group_type_service.find_by_code(org_id, "ministry")

# 2. Crear el grupo
ministerio_alabanza = await group_service.create(
    organization_id=org_id,
    scope_id=iglesia_central.id,
    group_type_id=ministry_type.id,
    name="Ministerio de Alabanza",
    leader_id=persona_lider.id,
    meeting_day="saturday",
    meeting_time="16:00",
    meeting_place="Salon principal"
)

# 3. Agregar miembros
await group_member_service.add(
    group_id=ministerio_alabanza.id,
    person_id=persona_musico.id,
    role="member"
)
```

---

> **Principio clave**: SavvyGroups no sabe nada sobre iglesias, tiendas o escuelas. Solo sabe agrupar personas en estructuras jerarquicas. Las apps le dan significado a esos grupos segun su dominio.
