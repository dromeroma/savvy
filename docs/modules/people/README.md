# SavvyPeople — Gestion Universal de Personas

## Tabla de Contenidos

1. [Proposito](#proposito)
2. [Entidades del Modulo](#entidades-del-modulo)
3. [Esquema Detallado](#esquema-detallado)
4. [Familiograma](#familiograma)
5. [Extensibilidad — person_contacts V2](#extensibilidad--person_contacts-v2)
6. [Endpoints API](#endpoints-api)
7. [Apps Consumidoras](#apps-consumidoras)
8. [Integracion con Apps de Dominio](#integracion-con-apps-de-dominio)
9. [Ejemplo de Codigo](#ejemplo-de-codigo)

---

## Proposito

SavvyPeople es la **fuente unica de verdad** para todas las personas dentro del ecosistema Savvy. Cualquier app que necesite representar a un ser humano (cliente, congregante, empleado, paciente, estudiante) **no crea su propia tabla de personas**, sino que:

1. Crea un registro en `people` (o reutiliza uno existente).
2. Vincula ese `person_id` a su tabla de dominio especifica.

Esto garantiza:

- **Cero duplicacion** de datos demograficos entre apps.
- **Vision 360** de una persona a traves de todas las apps que la involucran.
- **Consistencia** en nombres, documentos de identidad y datos de contacto.
- **Busqueda centralizada** a nivel de organizacion.

```
+------------------------------------------------------------------+
|                       ECOSISTEMA SAVVY                           |
|                                                                  |
|  +-------------------+                                           |
|  |   SavvyPeople     |  <-- Fuente unica de verdad              |
|  |   (people)        |                                           |
|  +--------+----------+                                           |
|           |                                                      |
|     +-----+------+----------+-----------+                        |
|     |            |          |           |                        |
|  +--v---+   +---v----+  +--v----+  +---v-------+               |
|  |Church |   | POS    |  | Acct  |  | Futuras   |               |
|  |Congreg|   | Client |  | Party |  | Apps      |               |
|  +-------+   +--------+  +-------+  +-----------+               |
+------------------------------------------------------------------+
```

---

## Entidades del Modulo

| Entidad                | Tabla                    | Estado  | Descripcion                                      |
|------------------------|--------------------------|---------|--------------------------------------------------|
| Persona                | `people`                 | Activa  | Registro central de toda persona                 |
| Relacion Familiar      | `family_relationships`   | Activa  | Vinculos familiares bidireccionales              |
| Contacto de Emergencia | `emergency_contacts`     | Activa  | Persona de contacto en caso de emergencia        |
| Contacto Multiple      | `person_contacts`        | V2      | Multiples emails, telefonos, redes sociales      |

---

## Esquema Detallado

### Tabla `people`

```sql
CREATE TABLE people (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    scope_id        UUID REFERENCES organizational_scopes(id),

    -- Datos personales
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    second_last_name VARCHAR(100),
    email           VARCHAR(255),
    phone           VARCHAR(30),
    mobile          VARCHAR(30),

    -- Direccion
    address         TEXT,
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(100),

    -- Datos demograficos
    date_of_birth   DATE,
    gender          VARCHAR(20) CHECK (gender IN ('male', 'female', 'other')),
    document_type   VARCHAR(30),   -- cedula, pasaporte, DNI, SSN, etc.
    document_number VARCHAR(50),
    marital_status  VARCHAR(20) CHECK (marital_status IN (
        'single', 'married', 'divorced', 'widowed', 'separated', 'common_law'
    )),
    occupation      VARCHAR(150),
    photo_url       TEXT,

    -- Campos flexibles
    tags            JSONB DEFAULT '[]',       -- ["voluntario", "lider", "nuevo"]
    metadata        JSONB DEFAULT '{}',       -- Datos arbitrarios por app

    -- Estado
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'deceased')),

    -- Auditoria
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Restricciones
    UNIQUE (organization_id, document_type, document_number)
);

-- Indices
CREATE INDEX idx_people_org ON people(organization_id);
CREATE INDEX idx_people_scope ON people(scope_id);
CREATE INDEX idx_people_name ON people(organization_id, last_name, first_name);
CREATE INDEX idx_people_email ON people(organization_id, email);
CREATE INDEX idx_people_document ON people(organization_id, document_type, document_number);
CREATE INDEX idx_people_tags ON people USING GIN (tags);
CREATE INDEX idx_people_metadata ON people USING GIN (metadata);
```

#### Descripcion de Campos

| Campo              | Tipo         | Requerido | Descripcion                                                  |
|--------------------|--------------|-----------|--------------------------------------------------------------|
| `id`               | UUID         | Auto      | Identificador unico universal                                |
| `organization_id`  | UUID         | Si        | Organizacion propietaria (multi-tenancy)                     |
| `scope_id`         | UUID         | No        | Scope organizacional (iglesia, sucursal) al que pertenece    |
| `first_name`       | VARCHAR(100) | Si        | Nombre(s) de pila                                            |
| `last_name`        | VARCHAR(100) | Si        | Primer apellido                                              |
| `second_last_name` | VARCHAR(100) | No        | Segundo apellido (comun en Latinoamerica)                    |
| `email`            | VARCHAR(255) | No        | Correo electronico principal                                 |
| `phone`            | VARCHAR(30)  | No        | Telefono fijo                                                |
| `mobile`           | VARCHAR(30)  | No        | Telefono celular                                             |
| `address`          | TEXT         | No        | Direccion completa                                           |
| `city`             | VARCHAR(100) | No        | Ciudad                                                       |
| `state`            | VARCHAR(100) | No        | Estado/Departamento/Provincia                                |
| `country`          | VARCHAR(100) | No        | Pais                                                         |
| `date_of_birth`    | DATE         | No        | Fecha de nacimiento                                          |
| `gender`           | VARCHAR(20)  | No        | Genero: male, female, other                                  |
| `document_type`    | VARCHAR(30)  | No        | Tipo de documento de identidad                               |
| `document_number`  | VARCHAR(50)  | No        | Numero de documento                                          |
| `marital_status`   | VARCHAR(20)  | No        | Estado civil                                                 |
| `occupation`       | VARCHAR(150) | No        | Profesion u ocupacion                                        |
| `photo_url`        | TEXT         | No        | URL de la foto de perfil                                     |
| `tags`             | JSONB        | No        | Etiquetas libres para busqueda y filtrado                    |
| `metadata`         | JSONB        | No        | Datos adicionales estructurados (key-value)                  |
| `status`           | VARCHAR(20)  | Auto      | Estado del registro: active, inactive, deceased              |

### Tabla `family_relationships`

```sql
CREATE TABLE family_relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    person_id       UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    related_person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    relationship_type VARCHAR(30) NOT NULL CHECK (relationship_type IN (
        'spouse', 'parent', 'child', 'sibling', 'grandparent', 'grandchild',
        'uncle_aunt', 'nephew_niece', 'cousin', 'in_law', 'step_parent',
        'step_child', 'godparent', 'godchild', 'other'
    )),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Restricciones
    CONSTRAINT no_self_relationship CHECK (person_id != related_person_id),
    UNIQUE (organization_id, person_id, related_person_id, relationship_type)
);
```

### Tabla `emergency_contacts`

```sql
CREATE TABLE emergency_contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    contact_name    VARCHAR(200) NOT NULL,
    relationship    VARCHAR(50),
    phone           VARCHAR(30) NOT NULL,
    email           VARCHAR(255),
    is_primary      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Familiograma

El familiograma permite construir el arbol familiar completo de cualquier persona. Se implementa mediante **relaciones bidireccionales automaticas**.

### Tabla de Relaciones Inversas

Cuando se crea una relacion A -> B, el sistema automaticamente crea la relacion inversa B -> A:

```
INVERSE_RELATIONSHIPS = {
    'spouse'       : 'spouse',        -- Simetrica
    'sibling'      : 'sibling',       -- Simetrica
    'cousin'       : 'cousin',        -- Simetrica
    'parent'       : 'child',         -- Asimetrica
    'child'        : 'parent',        -- Asimetrica
    'grandparent'  : 'grandchild',    -- Asimetrica
    'grandchild'   : 'grandparent',   -- Asimetrica
    'uncle_aunt'   : 'nephew_niece',  -- Asimetrica
    'nephew_niece' : 'uncle_aunt',    -- Asimetrica
    'in_law'       : 'in_law',        -- Simetrica
    'step_parent'  : 'step_child',    -- Asimetrica
    'step_child'   : 'step_parent',   -- Asimetrica
    'godparent'    : 'godchild',      -- Asimetrica
    'godchild'     : 'godparent',     -- Asimetrica
    'other'        : 'other',         -- Simetrica
}
```

### Validaciones del Familiograma

1. **No auto-relacion**: Una persona no puede tener relacion consigo misma (`person_id != related_person_id`).
2. **No duplicados**: No puede existir el mismo par (person_id, related_person_id, relationship_type) dos veces.
3. **Maximo 1 conyuge activo**: Validacion a nivel de servicio — una persona solo puede tener una relacion `spouse` activa.
4. **Bidireccionalidad atomica**: La creacion de la relacion directa e inversa se ejecuta en una sola transaccion.

### Flujo de Creacion

```
POST /people/{id}/family
Body: { "related_person_id": "uuid-B", "relationship_type": "parent" }

1. Validar que person_id != related_person_id
2. Validar que no existe duplicado
3. Si type = 'spouse', validar que no hay otro spouse activo
4. BEGIN TRANSACTION
   a. INSERT family_relationships (A -> B, type: 'parent')
   b. INSERT family_relationships (B -> A, type: 'child')  -- Inversa automatica
5. COMMIT
```

### Consulta del Arbol Familiar

```
GET /people/{id}/family

Response:
{
  "person_id": "uuid-juan",
  "full_name": "Juan Perez",
  "relationships": [
    {
      "related_person": { "id": "uuid-maria", "full_name": "Maria Lopez" },
      "relationship_type": "spouse"
    },
    {
      "related_person": { "id": "uuid-carlos", "full_name": "Carlos Perez" },
      "relationship_type": "child"
    },
    {
      "related_person": { "id": "uuid-ana", "full_name": "Ana Perez" },
      "relationship_type": "child"
    }
  ]
}
```

---

## Extensibilidad — person_contacts V2

En la version actual, cada persona tiene un solo `email`, `phone` y `mobile` directamente en la tabla `people`. En V2 se agregara la tabla `person_contacts` para soportar multiples canales de contacto:

```sql
-- V2 FUTURO
CREATE TABLE person_contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    contact_type    VARCHAR(30) NOT NULL, -- 'email', 'phone', 'mobile', 'whatsapp', 'telegram', 'instagram'
    contact_value   VARCHAR(255) NOT NULL,
    label           VARCHAR(50),          -- 'personal', 'trabajo', 'iglesia'
    is_primary      BOOLEAN DEFAULT FALSE,
    verified        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**Estrategia de migracion V2**: Los campos `email`, `phone` y `mobile` de `people` se migraran a `person_contacts` con `is_primary = true`. Los campos originales se mantendran como campos calculados (views) para compatibilidad retroactiva.

---

## Endpoints API

### CRUD de Personas

| Metodo | Ruta                        | Descripcion                              |
|--------|-----------------------------|------------------------------------------|
| GET    | `/people`                   | Listar personas (paginado, filtros)      |
| POST   | `/people`                   | Crear nueva persona                      |
| GET    | `/people/{id}`              | Obtener persona por ID                   |
| PATCH  | `/people/{id}`              | Actualizar persona                       |
| DELETE | `/people/{id}`              | Eliminar persona (soft delete)           |

### Familiograma

| Metodo | Ruta                             | Descripcion                              |
|--------|----------------------------------|------------------------------------------|
| GET    | `/people/{id}/family`            | Obtener arbol familiar completo          |
| POST   | `/people/{id}/family`            | Crear relacion familiar                  |
| DELETE | `/people/{id}/family/{rel_id}`   | Eliminar relacion (y su inversa)         |

### Busqueda y Estadisticas

| Metodo | Ruta                  | Descripcion                                              |
|--------|-----------------------|----------------------------------------------------------|
| GET    | `/people/search`      | Busqueda por nombre, documento, email, tags              |
| GET    | `/people/stats`       | Estadisticas: total, por genero, por estado civil, etc.  |

### Contactos de Emergencia

| Metodo | Ruta                                     | Descripcion                          |
|--------|------------------------------------------|--------------------------------------|
| GET    | `/people/{id}/emergency-contacts`        | Listar contactos de emergencia       |
| POST   | `/people/{id}/emergency-contacts`        | Crear contacto de emergencia         |
| PATCH  | `/people/{id}/emergency-contacts/{cid}`  | Actualizar contacto                  |
| DELETE | `/people/{id}/emergency-contacts/{cid}`  | Eliminar contacto                    |

### Parametros de Consulta Comunes

```
GET /people?scope_id=uuid&status=active&gender=female&page=1&limit=20&sort=last_name
GET /people/search?q=juan+perez&tags=voluntario,lider
```

---

## Apps Consumidoras

### SavvyChurch

- **Congregante = Persona + datos eclesiasticos**
- `church_congregants.person_id` -> `people.id`
- Datos eclesiasticos: `membership_date`, `baptism_date`, `spiritual_status`, etc.
- Al crear un congregante, se crea (o vincula) una persona en `people`.

### SavvyPOS

- **Cliente = Persona + historial de compras**
- `pos_customers.person_id` -> `people.id`
- Datos comerciales: `customer_code`, `credit_limit`, `loyalty_points`, etc.
- Al registrar un cliente, se crea (o vincula) una persona en `people`.

### SavvyAccounting

- **Parte contable = Persona como entidad en asientos**
- `journal_entries.party_id` -> `people.id`
- Permite rastrear la persona involucrada en cada transaccion contable.

### Futuras Apps

- **SavvyHR**: Empleado = Persona + datos laborales
- **SavvyCRM**: Contacto = Persona + pipeline de ventas
- **SavvyEducation**: Estudiante = Persona + historial academico

---

## Integracion con Apps de Dominio

### Flujo: Como una App Crea una Persona y la Vincula

```
App de Dominio (ej. SavvyChurch)
        |
        v
1. Recibe datos del formulario (nombre, email, datos eclesiasticos, etc.)
        |
        v
2. Busca si la persona ya existe en `people`
   - Busqueda por document_type + document_number
   - O por email
   - O por nombre + fecha de nacimiento
        |
        +--- SI EXISTE ---> Usa el person_id existente
        |
        +--- NO EXISTE ---> Crea registro en `people`, obtiene person_id
        |
        v
3. Crea registro en tabla de dominio
   - INSERT INTO church_congregants (person_id, membership_date, ...)
        |
        v
4. Responde con el registro completo (persona + datos de dominio)
```

### Principio de Responsabilidad

- **SavvyPeople** es dueno de: nombre, documento, contacto, direccion, genero, estado civil.
- **La app de dominio** es duena de: datos especificos de su contexto.
- **Nunca** una app duplica campos que ya existen en `people`.

---

## Ejemplo de Codigo

### CongregantService: Crear Congregante (Persona + Registro Eclesiastico)

```python
# backend/app/services/church/congregant_service.py

from uuid import UUID
from app.services.people.people_service import PeopleService
from app.repositories.church.congregant_repository import CongregantRepository

class CongregantService:
    def __init__(
        self,
        people_service: PeopleService,
        congregant_repo: CongregantRepository
    ):
        self.people_service = people_service
        self.congregant_repo = congregant_repo

    async def create_congregant(
        self,
        organization_id: UUID,
        scope_id: UUID,
        person_data: dict,
        church_data: dict
    ) -> dict:
        """
        Crea un congregante: primero la persona, luego el registro eclesiastico.

        Args:
            organization_id: ID de la organizacion (multi-tenancy)
            scope_id: ID del scope (iglesia especifica)
            person_data: {first_name, last_name, email, phone, ...}
            church_data: {membership_date, baptism_date, spiritual_status, ...}

        Returns:
            Registro completo del congregante con datos de persona
        """

        # Paso 1: Buscar si la persona ya existe
        existing_person = None

        if person_data.get("document_type") and person_data.get("document_number"):
            existing_person = await self.people_service.find_by_document(
                organization_id=organization_id,
                document_type=person_data["document_type"],
                document_number=person_data["document_number"]
            )

        if not existing_person and person_data.get("email"):
            existing_person = await self.people_service.find_by_email(
                organization_id=organization_id,
                email=person_data["email"]
            )

        # Paso 2: Crear o reutilizar persona
        if existing_person:
            person = existing_person
            # Verificar que no sea ya congregante en este scope
            existing_congregant = await self.congregant_repo.find_by_person_and_scope(
                person_id=person.id,
                scope_id=scope_id
            )
            if existing_congregant:
                raise ValueError("Esta persona ya es congregante en esta iglesia")
        else:
            person = await self.people_service.create(
                organization_id=organization_id,
                scope_id=scope_id,
                **person_data
            )

        # Paso 3: Crear registro eclesiastico
        congregant = await self.congregant_repo.create(
            person_id=person.id,
            scope_id=scope_id,
            **church_data
        )

        # Paso 4: Retornar registro completo
        return {
            "id": congregant.id,
            "person": person.to_dict(),
            "membership_date": congregant.membership_date,
            "baptism_date": congregant.baptism_date,
            "spiritual_status": congregant.spiritual_status,
            "pastoral_notes": congregant.pastoral_notes,
        }
```

### Endpoint del Router

```python
# backend/app/routers/church/congregants.py

@router.post("/congregants", status_code=201)
async def create_congregant(
    payload: CreateCongregantSchema,
    org_id: UUID = Depends(get_current_org),
    scope_id: UUID = Depends(get_current_scope),
    service: CongregantService = Depends()
):
    return await service.create_congregant(
        organization_id=org_id,
        scope_id=scope_id,
        person_data=payload.person.dict(),
        church_data=payload.church.dict()
    )
```

---

> **Principio clave**: SavvyPeople no sabe nada sobre iglesias, tiendas o contabilidad. Solo sabe gestionar personas. Las apps construyen significado sobre esa base.
