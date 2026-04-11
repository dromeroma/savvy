# SavvyFamily — Familiograma y Gestion Familiar

## Tabla de Contenidos

1. [Proposito](#proposito)
2. [Principio Arquitectonico](#principio-arquitectonico)
3. [Entidades Propias](#entidades-propias)
4. [Unidades Familiares](#unidades-familiares)
5. [Miembros de Familia](#miembros-de-familia)
6. [Metadata de Relaciones](#metadata-de-relaciones)
7. [Anotaciones Clinicas/Pastorales](#anotaciones-clinicaspastorales)
8. [Genograma](#genograma)
9. [Simbologia del Genograma](#simbologia-del-genograma)
10. [Consumo Multi-App](#consumo-multi-app)
11. [Endpoints API](#endpoints-api)
12. [Diagrama de Relaciones](#diagrama-de-relaciones)

---

## Proposito

SavvyFamily es la app de **familiograma, arbol genealogico y diagnostico familiar** del ecosistema Savvy. Es una app **multi-industria** — puede ser usada por:

- **Iglesias**: Diagnostico pastoral de familias de la congregacion
- **Clinicas**: Genograma clinico para psicologia, trabajo social, medicina familiar
- **Educacion**: Contexto familiar de los estudiantes
- **Trabajo social**: Evaluacion de nucleos familiares

### Funcionalidades principales

1. **Unidades familiares**: Agrupacion de personas en hogares con tipo (nuclear, extendida, monoparental, reconstituida)
2. **Genograma visual**: Diagrama interactivo con simbologia clinica estandar renderizado con D3.js
3. **Anotaciones clinicas**: Marcadores de diagnostico por persona o familia (19 categorias de severidad)
4. **Metadata de relaciones**: Datos enriquecidos de vinculos (fechas de matrimonio, divorcios, estado)
5. **Multi-app**: Accesible desde cualquier app del ecosistema (church, health, edu)

---

## Principio Arquitectonico

```
+-------------------------------------------------------------------+
|  SavvyFamily NO tiene:                                            |
|  x Tabla de personas (usa people via PeopleService)               |
|  x Relaciones basicas (usa family_relationships de SavvyPeople)   |
|                                                                   |
|  SavvyFamily SI tiene:                                            |
|  + family_units (hogares/nucleos familiares)                      |
|  + family_members (persona + rol + generacion en la familia)      |
|  + family_relationship_meta (matrimonios, divorcios, fechas)      |
|  + family_annotations (marcadores clinicos/pastorales)            |
+-------------------------------------------------------------------+
```

SavvyFamily **extiende** la tabla `family_relationships` existente en SavvyPeople con metadata enriquecida, sin duplicar los vinculos basicos.

---

## Entidades Propias

| Entidad              | Tabla                        | Descripcion                                     |
|----------------------|------------------------------|-------------------------------------------------|
| Unidad Familiar      | `family_units`               | Hogar/nucleo familiar con tipo y datos de contacto |
| Miembro de Familia   | `family_members`             | Persona + rol + generacion + posicion genograma  |
| Metadata de Relacion | `family_relationship_meta`   | Datos de matrimonio/divorcio con fechas y estado |
| Anotacion            | `family_annotations`         | Marcador clinico/pastoral por persona o familia  |

---

## Unidades Familiares

### Tabla `family_units`

```sql
CREATE TABLE family_units (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,    -- 'Familia Rodriguez Lopez'
    type            VARCHAR(30) NOT NULL DEFAULT 'nuclear',
    address         TEXT,
    city            VARCHAR(100),
    phone           VARCHAR(50),
    notes           TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
);
```

### Tipos de Familia

| Tipo            | Descripcion                                    |
|-----------------|------------------------------------------------|
| `nuclear`       | Padre, madre e hijos                           |
| `extended`      | Nuclear + abuelos, tios, primos                |
| `single_parent` | Un solo padre/madre con hijos                  |
| `blended`       | Reconstituida (segunda union con hijos previos)|
| `other`         | Otra estructura                                |

---

## Miembros de Familia

### Tabla `family_members`

```sql
CREATE TABLE family_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    family_unit_id  UUID NOT NULL REFERENCES family_units(id) ON DELETE CASCADE,
    person_id       UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    role            VARCHAR(30) NOT NULL DEFAULT 'member',
    is_deceased     BOOLEAN NOT NULL DEFAULT FALSE,
    death_date      DATE,
    generation      INTEGER NOT NULL DEFAULT 0,    -- 0=ref, -1=padres, 1=hijos
    position_x      INTEGER,                       -- Posicion en genograma
    position_y      INTEGER,
    UNIQUE(family_unit_id, person_id)
);
```

### Roles

| Rol           | Descripcion          |
|---------------|----------------------|
| `head`        | Cabeza de familia    |
| `spouse`      | Conyuge              |
| `child`       | Hijo/a               |
| `grandchild`  | Nieto/a              |
| `grandparent` | Abuelo/a             |
| `uncle_aunt`  | Tio/a                |
| `cousin`      | Primo/a              |
| `in_law`      | Familiar politico    |
| `other`       | Otro                 |

### Generaciones

El campo `generation` posiciona verticalmente en el genograma:

```
-2  Bisabuelos
-1  Abuelos / Padres
 0  Generacion de referencia (cabeza de familia + conyuge)
 1  Hijos
 2  Nietos
```

---

## Metadata de Relaciones

### Tabla `family_relationship_meta`

Extiende los vinculos basicos de `family_relationships` con datos enriquecidos:

```sql
CREATE TABLE family_relationship_meta (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_unit_id    UUID NOT NULL REFERENCES family_units(id) ON DELETE CASCADE,
    person_id         UUID NOT NULL REFERENCES people(id),
    related_to_id     UUID NOT NULL REFERENCES people(id),
    relationship_type VARCHAR(30) NOT NULL,     -- married, divorced, separated, etc.
    start_date        DATE,
    end_date          DATE,
    status            VARCHAR(20) NOT NULL DEFAULT 'active',
    notes             TEXT,
    UNIQUE(family_unit_id, person_id, related_to_id)
);
```

### Tipos de Relacion

| Tipo          | Linea en Genograma          | Descripcion                |
|---------------|-----------------------------|----------------------------|
| `married`     | Linea solida horizontal     | Matrimonio activo          |
| `divorced`    | Linea punteada + slash      | Divorciados                |
| `separated`   | Linea punteada              | Separados                  |
| `engaged`     | Linea fina                  | Comprometidos              |
| `cohabiting`  | Linea solida fina           | Union libre                |
| `widowed`     | Linea solida + X en persona | Viudo/a                    |

---

## Anotaciones Clinicas/Pastorales

### Tabla `family_annotations`

```sql
CREATE TABLE family_annotations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    family_unit_id  UUID NOT NULL REFERENCES family_units(id) ON DELETE CASCADE,
    person_id       UUID REFERENCES people(id),  -- NULL = aplica a la familia
    category        VARCHAR(50) NOT NULL,
    severity        VARCHAR(20) NOT NULL DEFAULT 'moderate',
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    diagnosed_date  DATE,
    resolved_date   DATE,
    source_app      VARCHAR(20)                   -- 'church', 'health', 'edu'
);
```

### Categorias (19 marcadores estandar del genograma)

| Categoria          | Descripcion                          | Icono genograma    |
|--------------------|--------------------------------------|--------------------|
| `substance_abuse`  | Abuso de sustancias (alcohol, drogas)| Relleno parcial    |
| `mental_health`    | Trastorno de salud mental            | Punto interior     |
| `physical_illness` | Enfermedad fisica cronica            | Relleno diagonal   |
| `violence`         | Violencia domestica                  | Linea zigzag       |
| `sexual_abuse`     | Abuso sexual                         | Doble circulo      |
| `emotional_abuse`  | Abuso emocional                      | Linea ondulada     |
| `conflict`         | Conflicto relacional                 | Linea zigzag entre |
| `cutoff`           | Ruptura total de relacion            | Linea cortada      |
| `enmeshment`       | Relacion enmeshada/fusionada         | Linea triple       |
| `estrangement`     | Distanciamiento                      | Linea punteada     |
| `disability`       | Discapacidad                         | Marca especial     |
| `incarceration`    | Encarcelamiento                      | Barras             |
| `adoption`         | Adopcion                             | Linea punteada     |
| `miscarriage`      | Aborto espontaneo                    | Triangulo pequeño  |
| `abortion`         | Aborto                               | X pequeña          |
| `stillbirth`       | Muerte fetal                         | Cuadro con X       |
| `spiritual`        | Anotacion espiritual (para iglesias) | Cruz               |
| `financial`        | Situacion financiera critica         | Signo $            |
| `other`            | Otro                                 | Punto generico     |

### Severidad

| Nivel      | Color en genograma | Significado                |
|------------|-------------------|----------------------------|
| `mild`     | Azul              | Leve, bajo monitoreo       |
| `moderate` | Amarillo          | Moderado, requiere atencion|
| `severe`   | Rojo              | Severo, intervencion urgente|

---

## Genograma

### Tecnologia

El genograma se renderiza en el **frontend** con **D3.js** (SVG):

- Layout automatico por generaciones (eje Y = generacion)
- Posicionamiento horizontal por orden dentro de generacion
- Simbologia clinica estandar
- Soporte dark mode

### Endpoint de datos

```
GET /family/units/{unit_id}/genogram
```

Retorna:

```json
{
  "family_unit": { ... },
  "nodes": [
    {
      "id": "member-uuid",
      "person_id": "person-uuid",
      "first_name": "Juan",
      "last_name": "Rodriguez",
      "gender": "male",
      "is_deceased": false,
      "role": "head",
      "generation": 0,
      "annotations": [
        {"category": "substance_abuse", "severity": "moderate"}
      ]
    }
  ],
  "edges": [
    {
      "source_person_id": "uuid-1",
      "target_person_id": "uuid-2",
      "relationship_type": "married",
      "status": "active"
    }
  ]
}
```

Los `edges` combinan datos de `family_relationship_meta` (matrimonios, etc.) y `family_relationships` (parent/child/sibling).

---

## Simbologia del Genograma

```
Personas:
  +-----+          Hombre (cuadrado)
  |     |
  +-----+

    ___
   /   \           Mujer (circulo)
   \___/

   /\
  /  \              Genero desconocido (diamante)
  \  /
   \/

   +--X--+         Fallecido (X sobre forma)
   | / \ |
   +-----+

Relaciones:
  ━━━━━━━           Matrimonio (linea solida)
  ╌╌╌╌╌╌╌           Separacion (linea punteada)
  ╌╌/╌╌╌╌           Divorcio (punteada + slash)
     |
     |              Padre-hijo (linea vertical + horizontal)
   +-+-+
   |   |

Anotaciones:
  ●                 Punto rojo = severidad severa
  ●                 Punto amarillo = severidad moderada
  ●                 Punto azul = severidad leve
```

---

## Consumo Multi-App

SavvyFamily es accesible desde cualquier app del ecosistema a traves del campo `source_app` en las anotaciones:

| App          | Uso                                                |
|--------------|----------------------------------------------------|
| SavvyChurch  | Diagnostico pastoral de familias de congregantes   |
| SavvyHealth  | Genograma clinico para psicologia/medicina familiar|
| SavvyEdu     | Contexto familiar de estudiantes                   |

Una anotacion creada desde SavvyChurch (`source_app='church'`) es visible cuando se accede al genograma desde SavvyHealth.

---

## Endpoints API

### Base URL: `/api/v1/family/`

#### Unidades Familiares

| Metodo | Ruta                               | Descripcion                     |
|--------|------------------------------------|---------------------------------|
| GET    | `/units`                           | Listar familias                 |
| POST   | `/units`                           | Crear familia                   |
| GET    | `/units/{id}`                      | Obtener familia                 |
| PATCH  | `/units/{id}`                      | Actualizar familia              |

#### Miembros

| Metodo | Ruta                               | Descripcion                     |
|--------|------------------------------------|---------------------------------|
| GET    | `/units/{id}/members`              | Listar miembros con datos persona|
| POST   | `/units/{id}/members`              | Agregar miembro                 |
| PATCH  | `/members/{id}`                    | Actualizar miembro              |
| DELETE | `/members/{id}`                    | Remover miembro                 |

#### Relaciones

| Metodo | Ruta                               | Descripcion                     |
|--------|------------------------------------|---------------------------------|
| GET    | `/units/{id}/relationships`        | Listar metadata de relaciones   |
| POST   | `/units/{id}/relationships`        | Agregar relacion (matrimonio, etc)|

#### Anotaciones

| Metodo | Ruta                               | Descripcion                     |
|--------|------------------------------------|---------------------------------|
| GET    | `/units/{id}/annotations`          | Listar anotaciones              |
| POST   | `/units/{id}/annotations`          | Crear anotacion                 |
| PATCH  | `/annotations/{id}`                | Actualizar anotacion            |

#### Genograma

| Metodo | Ruta                               | Descripcion                     |
|--------|------------------------------------|---------------------------------|
| GET    | `/units/{id}/genogram`             | Datos completos para renderizar |

---

## Diagrama de Relaciones

```
+------------------------------------------------------------------------+
|                   SAVVYFAMILY - DIAGRAMA DE ENTIDADES                   |
+------------------------------------------------------------------------+
|                                                                        |
|  +---------------------+                                              |
|  | family_units        |                                              |
|  | (hogar/nucleo)      |                                              |
|  +----------+----------+                                              |
|             |                                                          |
|     +-------+-------+--------+                                        |
|     |               |        |                                        |
|     v               v        v                                        |
|  +-----------+  +----------+  +-------------------+                   |
|  | family_   |  | family_  |  | family_           |                   |
|  | members   |  | relation |  | annotations       |                   |
|  |           |  | _meta    |  |                   |                   |
|  | person_id |  | person   |  | person_id (opt)   |                   |
|  | role      |  | related  |  | category          |                   |
|  | generation|  | type     |  | severity           |                   |
|  | deceased  |  | dates    |  | source_app         |                   |
|  | pos x/y   |  | status   |  | is_active          |                   |
|  +-----+-----+  +----+-----+  +-------------------+                   |
|        |              |                                                |
|        v              v                                                |
|  +---------------------+                                              |
|  | people (Module)     |    +------------------------+                |
|  | SavvyPeople         |    | family_relationships   |                |
|  |                     |<---| (Module - SavvyPeople) |                |
|  | first_name, gender, |    | person_id, related_to, |                |
|  | date_of_birth, etc. |    | relationship (basic)   |                |
|  +---------------------+    +------------------------+                |
|                                                                        |
|  El genograma combina datos de:                                       |
|  1. family_members (nodos con rol, generacion, deceased)              |
|  2. family_relationship_meta (edges: matrimonios, divorcios)          |
|  3. family_relationships (edges: parent/child/sibling)                |
|  4. family_annotations (marcadores clinicos por nodo)                 |
+------------------------------------------------------------------------+
```

---

> **Principio clave**: SavvyFamily no duplica vinculos basicos (parent/child/sibling). Extiende la infraestructura de SavvyPeople con metadata enriquecida (fechas, estados, anotaciones clinicas) y una capa de visualizacion profesional (genograma D3.js).
