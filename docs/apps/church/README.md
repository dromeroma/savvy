# SavvyChurch — Gestion Integral de Iglesias

## Tabla de Contenidos

1. [Proposito](#proposito)
2. [Principio Arquitectonico](#principio-arquitectonico)
3. [Entidades Propias](#entidades-propias)
4. [Congregantes](#congregantes)
5. [Clases Biblicas](#clases-biblicas)
6. [Matriculas (Enrollments)](#matriculas-enrollments)
7. [Actividades](#actividades)
8. [Asistencia](#asistencia)
9. [Consumo de SavvyPeople](#consumo-de-savvypeople)
10. [Consumo de SavvyGroups](#consumo-de-savvygroups)
11. [Consumo de SavvyFinance](#consumo-de-savvyfinance)
12. [Diezmo del Diezmo](#diezmo-del-diezmo)
13. [Reportes Especificos](#reportes-especificos)
14. [Diagrama de Relaciones](#diagrama-de-relaciones)

---

## Proposito

SavvyChurch es la app de **gestion integral de iglesias** dentro del ecosistema Savvy. Su alcance es **exclusivamente eclesiastico**: solo contiene logica y datos que son unicos del contexto de una iglesia cristiana.

**Todo lo que NO es exclusivo de iglesias se delega a modulos compartidos**:

| Responsabilidad        | Delegado a         | SavvyChurch solo tiene...              |
|------------------------|--------------------|----------------------------------------|
| Datos de personas      | SavvyPeople        | `person_id` + datos eclesiasticos      |
| Estructura jerarquica  | SavvyGroups        | Ministerios = grupos con tipo especifico|
| Ingresos y egresos     | SavvyFinance       | Categorias church: TITHE, OFFERING     |
| Contabilidad           | SavvyAccounting    | Nada — delegado completamente          |

---

## Principio Arquitectonico

```
+-------------------------------------------------------------------+
|                                                                   |
|  SavvyChurch NO tiene:                                           |
|  x Tabla de personas (usa people)                                 |
|  x Tabla de grupos/ministerios (usa groups)                       |
|  x Tabla de ingresos/egresos (usa finance_transactions)           |
|  x Motor contable (usa journal_entries)                           |
|                                                                   |
|  SavvyChurch SI tiene:                                           |
|  + church_congregants (datos eclesiasticos)                       |
|  + church_classes (clases biblicas)                               |
|  + church_class_enrollments (matriculas)                          |
|  + church_activities (cultos, eventos)                            |
|  + church_attendance (registro de asistencia)                     |
|                                                                   |
+-------------------------------------------------------------------+
```

---

## Entidades Propias

| Entidad              | Tabla                       | Descripcion                                    |
|----------------------|-----------------------------|------------------------------------------------|
| Congregante          | `church_congregants`        | Persona + datos eclesiasticos                  |
| Clase Biblica        | `church_classes`            | Curso educativo con fecha inicio/fin           |
| Matricula            | `church_class_enrollments`  | Inscripcion de persona a clase                 |
| Actividad            | `church_activities`         | Cultos, eventos, campanas, reuniones           |
| Asistencia           | `church_attendance`         | Check-in de persona por actividad              |

---

## Congregantes

### Tabla `church_congregants`

Un congregante es una **persona** (de SavvyPeople) con **datos eclesiasticos adicionales**:

```sql
CREATE TABLE church_congregants (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id         UUID NOT NULL REFERENCES people(id),
    scope_id          UUID NOT NULL REFERENCES organizational_scopes(id),

    -- Datos eclesiasticos
    membership_date   DATE,                       -- Fecha de membresia oficial
    baptism_date      DATE,                       -- Fecha de bautismo
    conversion_date   DATE,                       -- Fecha de conversion
    spiritual_status  VARCHAR(30) DEFAULT 'visitor' CHECK (spiritual_status IN (
        'visitor', 'regular', 'member', 'active_member', 'leader', 'inactive'
    )),
    referred_by       UUID REFERENCES people(id), -- Quien lo invito
    pastoral_notes    TEXT,                        -- Notas pastorales (confidencial)

    -- Auditoria
    status            VARCHAR(20) DEFAULT 'active'
                      CHECK (status IN ('active', 'inactive', 'transferred', 'deceased')),
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),

    -- Una persona solo puede ser congregante una vez por iglesia
    UNIQUE (person_id, scope_id)
);

CREATE INDEX idx_congregants_person ON church_congregants(person_id);
CREATE INDEX idx_congregants_scope ON church_congregants(scope_id);
CREATE INDEX idx_congregants_status ON church_congregants(scope_id, spiritual_status);
CREATE INDEX idx_congregants_referred ON church_congregants(referred_by);
```

### Estados Espirituales (Flujo)

```
visitor -> regular -> member -> active_member -> leader
                                     |
                                     v
                                  inactive
```

| Estado          | Descripcion                                              |
|-----------------|----------------------------------------------------------|
| `visitor`       | Primera vez o visitas esporadicas                        |
| `regular`       | Asiste regularmente pero no es miembro formal            |
| `member`        | Miembro bautizado y registrado oficialmente              |
| `active_member` | Miembro activo participando en ministerios/celulas       |
| `leader`        | Lider de algun ministerio, celula o area                 |
| `inactive`      | Dejo de asistir o fue dado de baja temporalmente         |

### Datos que NO estan en church_congregants

Los siguientes datos estan en `people` (SavvyPeople) y NO se duplican:

- Nombre, apellidos
- Email, telefono, celular
- Direccion, ciudad, pais
- Fecha de nacimiento, genero
- Documento de identidad
- Estado civil, ocupacion
- Foto

---

## Clases Biblicas

### Tabla `church_classes`

Las clases son **cursos educativos temporales**, independientes de los grupos (ministerios):

```sql
CREATE TABLE church_classes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    scope_id        UUID NOT NULL REFERENCES organizational_scopes(id),

    -- Datos de la clase
    name            VARCHAR(200) NOT NULL,        -- 'Principios de Fe', 'Escuela Dominical'
    description     TEXT,
    teacher_id      UUID REFERENCES people(id),   -- Maestro/instructor
    category        VARCHAR(50),                   -- 'foundational', 'intermediate', 'advanced', 'special'

    -- Programacion
    schedule        VARCHAR(200),                  -- 'Sabados 3:00 PM'
    location        VARCHAR(200),                  -- 'Salon 2'
    start_date      DATE NOT NULL,
    end_date        DATE,

    -- Capacidad
    max_students    INTEGER,                       -- Limite de inscritos

    -- Estado
    status          VARCHAR(20) DEFAULT 'planned'
                    CHECK (status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_classes_scope ON church_classes(scope_id);
CREATE INDEX idx_classes_teacher ON church_classes(teacher_id);
CREATE INDEX idx_classes_dates ON church_classes(start_date, end_date);
CREATE INDEX idx_classes_status ON church_classes(scope_id, status);
```

### Ciclo de Vida de una Clase

```
planned ---(fecha de inicio llega)---> in_progress ---(fecha fin llega)---> completed
    |                                       |
    +-------(se cancela)--->  cancelled <---+
```

### Diferencia clave: Classes vs Groups

| Aspecto           | church_classes                    | groups (SavvyGroups)              |
|-------------------|-----------------------------------|-----------------------------------|
| Duracion          | Temporal (start_date - end_date)  | Permanente                        |
| Proposito         | Educativo                         | Organizacional                    |
| Participantes     | Estudiantes con matricula         | Miembros con rol                  |
| Estado salida     | completed, dropped                | left_at (fecha)                   |
| Instructor        | teacher_id                        | leader_id                         |
| Modulo            | SavvyChurch (exclusivo)           | SavvyGroups (compartido)          |

---

## Matriculas (Enrollments)

### Tabla `church_class_enrollments`

```sql
CREATE TABLE church_class_enrollments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id        UUID NOT NULL REFERENCES church_classes(id) ON DELETE CASCADE,
    person_id       UUID NOT NULL REFERENCES people(id),

    -- Estado de la matricula
    status          VARCHAR(20) DEFAULT 'enrolled' CHECK (status IN (
        'enrolled', 'completed', 'dropped', 'failed'
    )),
    enrolled_at     TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    grade           DECIMAL(5,2),                  -- Nota/calificacion (opcional)
    notes           TEXT,

    UNIQUE (class_id, person_id)
);

CREATE INDEX idx_enrollments_class ON church_class_enrollments(class_id);
CREATE INDEX idx_enrollments_person ON church_class_enrollments(person_id);
CREATE INDEX idx_enrollments_status ON church_class_enrollments(class_id, status);
```

### Estados de Matricula

```
enrolled ---(completa la clase)----> completed
    |
    +----(abandona)---------------> dropped
    |
    +----(no aprueba)-------------> failed
```

### Requisito de Clases para Ministerios

Cuando un `group_type` tiene `requires_classes = true`, el sistema verifica que la persona haya completado las clases requeridas antes de unirse al grupo:

```python
async def validate_class_requirements(person_id: UUID, group_type_id: UUID) -> bool:
    """
    Verifica si la persona cumple con las clases requeridas
    para unirse a un grupo de este tipo.
    """
    required_classes = await get_required_classes_for_group_type(group_type_id)

    for class_category in required_classes:
        has_completed = await enrollment_service.has_completed_category(
            person_id=person_id,
            category=class_category
        )
        if not has_completed:
            return False

    return True
```

---

## Actividades

### Tabla `church_activities`

```sql
CREATE TABLE church_activities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    scope_id        UUID NOT NULL REFERENCES organizational_scopes(id),

    -- Datos de la actividad
    name            VARCHAR(200) NOT NULL,         -- 'Culto Dominical', 'Vigilia de Oracion'
    description     TEXT,
    activity_type   VARCHAR(30) NOT NULL CHECK (activity_type IN (
        'service', 'event', 'campaign', 'meeting', 'retreat',
        'conference', 'workshop', 'other'
    )),

    -- Programacion
    date            DATE NOT NULL,
    start_time      TIME,
    end_time        TIME,
    location        VARCHAR(200),

    -- Vinculacion
    group_id        UUID REFERENCES groups(id),    -- Grupo responsable (opcional)
    responsible_id  UUID REFERENCES people(id),    -- Persona responsable

    -- Recurrencia (simple)
    is_recurring    BOOLEAN DEFAULT FALSE,
    recurrence_rule VARCHAR(100),                   -- 'weekly:sunday', 'monthly:first_sunday'

    -- Estado
    status          VARCHAR(20) DEFAULT 'scheduled'
                    CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activities_scope ON church_activities(scope_id);
CREATE INDEX idx_activities_date ON church_activities(scope_id, date);
CREATE INDEX idx_activities_type ON church_activities(scope_id, activity_type);
CREATE INDEX idx_activities_group ON church_activities(group_id);
```

### Tipos de Actividad

| Tipo          | Descripcion                              | Ejemplo                        |
|---------------|------------------------------------------|--------------------------------|
| `service`     | Culto/servicio religioso regular         | Culto Dominical                |
| `event`       | Evento especial                          | Bazar Navideno                 |
| `campaign`    | Campana multidia                         | Campana de Evangelismo         |
| `meeting`     | Reunion administrativa o pastoral        | Junta de Lideres               |
| `retreat`     | Retiro espiritual                        | Retiro de Jovenes              |
| `conference`  | Conferencia o seminario                  | Conferencia de Mujeres         |
| `workshop`    | Taller practico                          | Taller de Liderazgo            |
| `other`       | Otro tipo de actividad                   | Jornada de limpieza            |

---

## Asistencia

### Tabla `church_attendance`

```sql
CREATE TABLE church_attendance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id     UUID NOT NULL REFERENCES church_activities(id) ON DELETE CASCADE,
    person_id       UUID NOT NULL REFERENCES people(id),

    -- Check-in
    checked_in_at   TIMESTAMPTZ DEFAULT NOW(),
    checked_in_by   UUID REFERENCES auth.users(id),  -- Quien registro la asistencia
    check_in_method VARCHAR(20) DEFAULT 'manual' CHECK (check_in_method IN (
        'manual', 'qr_code', 'self_check_in', 'automatic'
    )),

    notes           TEXT,

    UNIQUE (activity_id, person_id)
);

CREATE INDEX idx_attendance_activity ON church_attendance(activity_id);
CREATE INDEX idx_attendance_person ON church_attendance(person_id);
CREATE INDEX idx_attendance_date ON church_attendance(checked_in_at);
```

### Flujo de Registro de Asistencia

```
1. Se crea la actividad (ej: Culto Dominical 2026-04-06)
2. Las personas llegan y se registran:
   - Manual: Un ujier marca la asistencia en tablet
   - QR Code: La persona escanea un QR al entrar
   - Self check-in: La persona se registra desde su celular
3. Al finalizar la actividad, se tiene el conteo de asistentes
4. Los reportes muestran tendencias de asistencia
```

---

## Consumo de SavvyPeople

### Como se crea un congregante

```python
# Crear congregante = Crear persona + Crear registro eclesiastico

async def create_congregant(person_data: dict, church_data: dict):
    # 1. Buscar si la persona ya existe (por documento o email)
    person = await people_service.find_or_create(person_data)

    # 2. Crear el registro eclesiastico
    congregant = await congregant_repo.create(
        person_id=person.id,
        scope_id=church_data["scope_id"],
        spiritual_status="visitor",
        **church_data
    )

    return congregant
```

### Consulta de congregantes con datos de persona

```sql
SELECT
    c.id AS congregant_id,
    c.spiritual_status,
    c.membership_date,
    c.baptism_date,
    p.first_name,
    p.last_name,
    p.email,
    p.phone,
    p.date_of_birth,
    p.gender,
    p.marital_status
FROM church_congregants c
JOIN people p ON c.person_id = p.id
WHERE c.scope_id = :church_scope_id
  AND c.status = 'active'
ORDER BY p.last_name, p.first_name;
```

### Una persona puede ser congregante en multiples iglesias

```
Juan Perez (people.id = uuid-juan)
    |
    +-- Congregante en Iglesia Central (scope_id = uuid-ic)
    |   spiritual_status: 'active_member'
    |
    +-- Congregante en Iglesia del Sur (scope_id = uuid-is)
        spiritual_status: 'visitor'  (visita ocasional)
```

---

## Consumo de SavvyGroups

### Ministerios = Groups con tipo especifico

SavvyChurch no tiene tabla propia de ministerios. Usa `groups` de SavvyGroups con `group_type.code = 'ministry'`:

```python
# Crear ministerio para una iglesia
ministerio = await group_service.create(
    organization_id=org_id,
    scope_id=iglesia_central.id,
    group_type_id=ministry_type.id,    # group_type.code = 'ministry'
    name="Ministerio de Alabanza",
    leader_id=persona_lider.id
)

# Listar ministerios de una iglesia
ministerios = await group_service.list(
    scope_id=iglesia_central.id,
    group_type_code="ministry"
)

# Agregar miembro a ministerio
await group_member_service.add(
    group_id=ministerio.id,
    person_id=persona.id,
    role="member"
)
```

### Celulas de crecimiento

```python
# Celulas = Groups con group_type.code = 'cell_group'
celula = await group_service.create(
    scope_id=iglesia_central.id,
    group_type_id=cell_group_type.id,   # max_members: 12
    name="Celula Sector Norte",
    leader_id=lider_celula.id,
    meeting_day="wednesday",
    meeting_time="19:00",
    meeting_place="Casa del Hno. Martinez"
)
```

### Estructura denominacional

```python
# La jerarquia de la denominacion usa scopes de SavvyGroups:
# country -> zone -> district -> church

# SavvyChurch simplemente filtra por scope_type = 'church'
# para obtener la lista de iglesias de la denominacion
```

---

## Consumo de SavvyFinance

### Diezmos y ofrendas como finance_transactions

SavvyChurch no tiene tabla propia de ingresos/egresos. Usa `finance_transactions` con `app_code = 'church'`:

```python
# Registrar diezmo
await finance_service.create_transaction(
    scope_id=iglesia.id,
    category_id=tithe_category.id,      # finance_categories.code = 'TITHE'
    type="income",
    app_code="church",
    amount=Decimal("500000"),
    payment_method="cash",
    person_id=congregante.person_id,
    reference_type="church_activity",
    reference_id=culto_dominical.id,
    description="Diezmo - Culto Dominical 2026-04-06"
)

# Registrar ofrenda
await finance_service.create_transaction(
    scope_id=iglesia.id,
    category_id=offering_category.id,   # finance_categories.code = 'OFFERING'
    type="income",
    app_code="church",
    amount=Decimal("50000"),
    payment_method="cash",
    person_id=None,                      # Ofrenda anonima
    reference_type="church_activity",
    reference_id=culto_dominical.id,
    description="Ofrenda general - Culto Dominical"
)
```

### Consulta de finanzas de la iglesia

```python
# SavvyChurch consulta SavvyFinance filtrado por app_code='church'

# Total diezmos del mes
total_tithes = await finance_service.sum_transactions(
    scope_id=iglesia.id,
    app_code="church",
    category_code="TITHE",
    date_from="2026-04-01",
    date_to="2026-04-30"
)

# Diezmos por persona
tithes_by_person = await finance_service.report_by_person(
    scope_id=iglesia.id,
    app_code="church",
    category_code="TITHE",
    year=2026
)
```

---

## Diezmo del Diezmo

El "diezmo del diezmo" es el aporte que cada iglesia local envia al nivel superior de la denominacion (distrito, zona o pais). Se calcula como un porcentaje de los ingresos por diezmos y ofrendas.

### Calculo

```python
async def calculate_tithe_of_tithe(
    scope_id: UUID,            # Iglesia
    period_start: date,
    period_end: date,
    percentage: Decimal = Decimal("0.10")
) -> dict:
    """
    Base de calculo: Diezmos + Ofrendas del periodo
    Monto a enviar: Base * porcentaje (tipicamente 10%)
    """
    # Filtrar transacciones de SavvyFinance
    base = await finance_service.sum_transactions(
        scope_id=scope_id,
        app_code="church",
        category_codes=["TITHE", "OFFERING"],
        type="income",
        date_from=period_start,
        date_to=period_end
    )

    return {
        "scope_id": scope_id,
        "period": f"{period_start} a {period_end}",
        "total_tithes": base.tithe_total,
        "total_offerings": base.offering_total,
        "base_amount": base.grand_total,
        "percentage": percentage,
        "amount_due": base.grand_total * percentage,
    }
```

### Reporte para el Distrito

El supervisor de distrito puede ver el diezmo del diezmo de todas sus iglesias:

```
GET /church/reports/tithe-of-tithe?scope_id=uuid-distrito&period=2026-Q1

Response:
{
  "district": "Distrito Barranquilla",
  "period": "2026-Q1",
  "churches": [
    {
      "church": "Iglesia Central",
      "tithes": 15000000,
      "offerings": 5000000,
      "base": 20000000,
      "tithe_of_tithe": 2000000,
      "paid": true
    },
    {
      "church": "Iglesia Sur",
      "tithes": 8000000,
      "offerings": 2500000,
      "base": 10500000,
      "tithe_of_tithe": 1050000,
      "paid": false
    }
  ],
  "total_due": 3050000,
  "total_paid": 2000000,
  "total_pending": 1050000
}
```

---

## Reportes Especificos

### Reportes de Congregantes

| Reporte                      | Descripcion                                          |
|------------------------------|------------------------------------------------------|
| Listado de congregantes      | Filtro por spiritual_status, genero, edad             |
| Nuevos visitantes            | Personas con spiritual_status='visitor' en periodo    |
| Cumpleanos del mes           | Congregantes con date_of_birth en el mes actual       |
| Historial de un congregante  | Timeline: conversion, bautismo, membresia, ministerios|
| Arbol de referidos           | Quien invito a quien (cadena de referred_by)          |

### Reportes de Clases

| Reporte                      | Descripcion                                          |
|------------------------------|------------------------------------------------------|
| Clases activas               | Clases en status='in_progress' con conteo de alumnos |
| Avance de matriculas         | % completados vs % en curso vs % abandonados          |
| Historial de clases persona  | Todas las clases que una persona ha tomado            |
| Requisitos de ministerio     | Personas que han completado las clases requeridas     |

### Reportes de Asistencia

| Reporte                      | Descripcion                                          |
|------------------------------|------------------------------------------------------|
| Asistencia por actividad     | Conteo de asistentes por culto/evento                |
| Tendencia de asistencia      | Grafico mensual de asistencia a cultos               |
| Asistencia por persona       | Frecuencia de asistencia de cada congregante         |
| Congregantes inactivos       | Personas que no han asistido en X semanas            |

### Reportes Financieros (via SavvyFinance)

| Reporte                      | Descripcion                                          |
|------------------------------|------------------------------------------------------|
| Diezmos del periodo          | Total y desglose por persona                         |
| Ofrendas del periodo         | Total por tipo de ofrenda                            |
| Ingresos vs Egresos          | Balance financiero de la iglesia                     |
| Diezmo del diezmo            | Calculo de aporte al nivel superior                  |
| Historico por congregante    | Todos los aportes de una persona en el tiempo        |

---

## Diagrama de Relaciones

```
+-------------------------------------------------------------------+
|                    SAVVYCHURCH - DIAGRAMA DE ENTIDADES             |
+-------------------------------------------------------------------+
|                                                                   |
|  +-----------+     +--------------------+     +----------------+  |
|  | people    |<----| church_congregants |     | church_classes  |  |
|  | (Module)  |     |                    |     |                |  |
|  |           |     | person_id      FK  |     | teacher_id  FK--->|
|  |           |     | scope_id       FK  |     | scope_id    FK |  |
|  |           |     | membership_date   |     | name           |  |
|  |           |     | baptism_date      |     | start_date     |  |
|  |           |     | conversion_date   |     | end_date       |  |
|  |           |     | spiritual_status  |     | max_students   |  |
|  |           |     | referred_by    FK-+---->| status         |  |
|  |           |     | pastoral_notes    |     +-------+--------+  |
|  +-----+-----+     +--------------------+             |           |
|        |                                               |           |
|        |           +------------------------+          |           |
|        |           | church_class_enrollments|<---------+           |
|        +---------->|                        |                     |
|        |           | class_id           FK  |                     |
|        |           | person_id          FK  |                     |
|        |           | status (enrolled,      |                     |
|        |           |   completed, dropped)  |                     |
|        |           | grade                  |                     |
|        |           +------------------------+                     |
|        |                                                          |
|        |           +--------------------+                         |
|        +---------->| church_attendance  |                         |
|        |           |                    |                         |
|        |           | activity_id    FK  |                         |
|        |           | person_id      FK  |                         |
|        |           | checked_in_at      |                         |
|        |           | check_in_method    |                         |
|        |           +--------+-----------+                         |
|        |                    |                                     |
|        |           +--------v-----------+                         |
|        |           | church_activities   |                        |
|        |           |                    |                         |
|        |           | scope_id       FK  |                         |
|        |           | activity_type      |                         |
|        |           | date, start_time   |                         |
|        |           | group_id       FK--+--> groups (Module)      |
|        |           | responsible_id FK  |                         |
|        |           +--------------------+                         |
|        |                                                          |
|  +-----v------+                   +-------------------+           |
|  | groups     |                   | finance_           |          |
|  | (Module)   |                   | transactions      |           |
|  |            |                   | (Module)          |           |
|  | group_type:|                   |                   |           |
|  |  'ministry'|                   | app_code='church' |           |
|  |  'cell_grp'|                   | category: TITHE,  |           |
|  |            |                   |   OFFERING, etc.  |           |
|  +------------+                   +-------------------+           |
|                                                                   |
+-------------------------------------------------------------------+

Modulos compartidos consumidos:
- SavvyPeople:   people (datos personales)
- SavvyGroups:   groups, group_types, organizational_scopes
- SavvyFinance:  finance_transactions, finance_categories
- SavvyAccounting: journal_entries (via SavvyFinance, indirecto)
```

---

### Endpoints API de SavvyChurch

#### Congregantes

| Metodo | Ruta                                       | Descripcion                          |
|--------|--------------------------------------------|--------------------------------------|
| GET    | `/church/congregants`                      | Listar congregantes                  |
| POST   | `/church/congregants`                      | Crear congregante                    |
| GET    | `/church/congregants/{id}`                 | Obtener congregante completo         |
| PATCH  | `/church/congregants/{id}`                 | Actualizar datos eclesiasticos       |
| DELETE | `/church/congregants/{id}`                 | Desactivar congregante               |
| GET    | `/church/congregants/{id}/timeline`        | Timeline del congregante             |

#### Clases

| Metodo | Ruta                                       | Descripcion                          |
|--------|--------------------------------------------|--------------------------------------|
| GET    | `/church/classes`                          | Listar clases                        |
| POST   | `/church/classes`                          | Crear clase                          |
| GET    | `/church/classes/{id}`                     | Obtener clase con alumnos            |
| PATCH  | `/church/classes/{id}`                     | Actualizar clase                     |
| POST   | `/church/classes/{id}/enroll`              | Matricular persona                   |
| PATCH  | `/church/classes/{id}/enrollments/{eid}`   | Actualizar matricula (status, grade) |

#### Actividades y Asistencia

| Metodo | Ruta                                       | Descripcion                          |
|--------|--------------------------------------------|--------------------------------------|
| GET    | `/church/activities`                       | Listar actividades                   |
| POST   | `/church/activities`                       | Crear actividad                      |
| GET    | `/church/activities/{id}`                  | Obtener actividad con asistencia     |
| PATCH  | `/church/activities/{id}`                  | Actualizar actividad                 |
| POST   | `/church/activities/{id}/check-in`         | Registrar asistencia                 |
| GET    | `/church/activities/{id}/attendance`       | Listar asistentes                    |

#### Reportes

| Metodo | Ruta                                       | Descripcion                          |
|--------|--------------------------------------------|--------------------------------------|
| GET    | `/church/reports/attendance-trend`         | Tendencia de asistencia              |
| GET    | `/church/reports/new-visitors`             | Nuevos visitantes del periodo        |
| GET    | `/church/reports/birthdays`                | Cumpleanos del mes                   |
| GET    | `/church/reports/inactive`                 | Congregantes inactivos               |
| GET    | `/church/reports/tithe-of-tithe`           | Calculo diezmo del diezmo            |
| GET    | `/church/reports/class-progress`           | Avance de clases                     |

---

> **Principio clave**: SavvyChurch solo contiene lo que es exclusivamente eclesiastico. Todo lo demas (personas, grupos, finanzas, contabilidad) se delega a modulos compartidos, permitiendo que cualquier otra app del ecosistema reutilice esa infraestructura sin duplicacion.
