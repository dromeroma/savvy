# Arquitectura del Ecosistema Savvy — Diseno Modular

## Tabla de Contenidos

1. [Vision](#vision)
2. [Las 3 Capas](#las-3-capas)
3. [Regla de Ubicacion](#regla-de-ubicacion)
4. [Mapa de Dominios](#mapa-de-dominios)
5. [Comunicacion entre Capas](#comunicacion-entre-capas)
6. [Scopes Organizacionales y Liderazgo Multinivel](#scopes-organizacionales-y-liderazgo-multinivel)
7. [Estrategia de Migracion (Resumen)](#estrategia-de-migracion-resumen)
8. [Lista de Tablas por Modulo](#lista-de-tablas-por-modulo)
9. [Diagrama de Relaciones entre Modulos y Apps](#diagrama-de-relaciones-entre-modulos-y-apps)
10. [Principios de Diseno](#principios-de-diseno)

---

## Vision

Savvy es una **plataforma multi-app tipo Google Workspace** para organizaciones. Cada organizacion puede activar las apps que necesite:

- Una iglesia activa: SavvyChurch + SavvyPeople + SavvyGroups + SavvyFinance + SavvyAccounting
- Un comercio activa: SavvyPOS + SavvyPeople + SavvyFinance + SavvyAccounting
- Una ONG activa: SavvyPeople + SavvyGroups + SavvyFinance + SavvyAccounting
- Una empresa activa: SavvyHR + SavvyPeople + SavvyGroups + SavvyFinance + SavvyAccounting + SavvyCRM

Las apps comparten una base comun de modulos, evitando duplicacion y permitiendo una vision unificada de personas, finanzas y estructura organizacional.

```
+====================================================================+
|                                                                    |
|               SAVVY — Plataforma Multi-App SaaS                   |
|                                                                    |
|   "Tu organizacion, todas las herramientas, una sola plataforma"  |
|                                                                    |
+====================================================================+
|                                                                    |
|   APPS:     [Church] [POS] [HR] [CRM] [Education] [Clinic] ...   |
|                 |       |     |    |        |          |           |
|   MODULES:  [People] [Groups] [Finance] [Accounting] [Inventory]  |
|                 |       |         |           |            |        |
|   CORE:     [Auth] [Organizations] [Gateway] [Notifications]      |
|                                                                    |
+====================================================================+
```

---

## Las 3 Capas

### Capa 1: Core (Nucleo)

El core provee servicios fundamentales que **toda app necesita** sin excepcion:

| Servicio        | Responsabilidad                                          |
|-----------------|----------------------------------------------------------|
| Auth            | Autenticacion (Supabase Auth), usuarios, sesiones        |
| Organizations   | Multi-tenancy, registro de organizaciones, apps activas  |
| Gateway         | API Gateway, rate limiting, logging                      |
| Notifications   | Emails, push notifications, SMS (futuro)                 |

**Caracteristica**: Ningun codigo de negocio. Solo infraestructura.

### Capa 2: Modules (Modulos Compartidos)

Los modulos encapsulan **dominios de negocio reutilizables** que multiples apps necesitan:

| Modulo       | Responsabilidad                                        |
|-------------|--------------------------------------------------------|
| People      | Gestion universal de personas                          |
| Groups      | Estructura organizacional y agrupacion                 |
| Finance     | Motor de transacciones (ingresos/egresos)              |
| Accounting  | Motor contable (plan de cuentas, asientos, reportes)   |
| Inventory   | Gestion de productos e inventario (futuro)             |

**Caracteristica**: Logica de negocio generica. NO saben que app los consume.

### Capa 3: Apps (Aplicaciones)

Las apps contienen **logica de negocio especifica** de un dominio vertical:

| App          | Dominio                                                |
|-------------|--------------------------------------------------------|
| Church      | Gestion de iglesias (congregantes, clases, cultos)     |
| POS         | Punto de venta (ordenes, inventario, clientes)         |
| HR          | Recursos humanos (empleados, nomina, vacaciones)       |
| CRM         | Relacion con clientes (leads, pipeline, seguimiento)   |
| Education   | Gestion educativa (estudiantes, cursos, notas)         |

**Caracteristica**: Logica especifica del dominio. Consumen modulos compartidos.

---

## Regla de Ubicacion

Para decidir donde va cada pieza de funcionalidad, se aplican estas preguntas en orden:

```
+---------------------------------------------------------------+
|                                                               |
|  Pregunta 1: Es infraestructura sin logica de negocio?       |
|     SI ---> CORE                                              |
|     NO ---> Siguiente pregunta                                |
|                                                               |
|  Pregunta 2: Lo necesitan 2 o mas apps?                      |
|     SI ---> MODULE                                            |
|     NO ---> Siguiente pregunta                                |
|                                                               |
|  Pregunta 3: Es especifico de un solo dominio vertical?      |
|     SI ---> APP                                               |
|     NO ---> Reconsiderar si deberia ser MODULE                |
|                                                               |
+---------------------------------------------------------------+
```

### Ejemplos Practicos

| Funcionalidad              | Pregunta | Ubicacion      | Razon                                         |
|----------------------------|----------|----------------|-----------------------------------------------|
| Login/Logout               | 1: SI    | Core (Auth)    | Infraestructura pura                          |
| Datos de una persona       | 2: SI    | Module (People)| Church, POS, HR la necesitan                  |
| Ministerios de iglesia     | 2: SI    | Module (Groups)| Groups es generico, Church lo usa como ministry|
| Diezmo                     | 2: SI    | Module (Finance)| Es una transaccion financiera categorizada    |
| Clase biblica              | 3: SI    | App (Church)   | Solo tiene sentido en contexto eclesiastico   |
| Orden de venta             | 3: SI    | App (POS)      | Solo tiene sentido en contexto comercial      |
| Congregante                | 3: SI    | App (Church)   | Datos eclesiasticos sobre una persona         |

### Anti-patron: Duplicacion

```
INCORRECTO:
  SavvyChurch tiene: church_members (nombre, email, telefono, ...)
  SavvyPOS tiene:    pos_customers  (nombre, email, telefono, ...)
  --> Duplicacion de datos de persona

CORRECTO:
  SavvyPeople tiene: people (nombre, email, telefono, ...)
  SavvyChurch tiene: church_congregants (person_id FK, datos eclesiasticos)
  SavvyPOS tiene:    pos_customers (person_id FK, datos comerciales)
  --> Una sola fuente de verdad
```

---

## Mapa de Dominios

```
+====================================================================+
|                        ECOSISTEMA SAVVY                            |
+====================================================================+
|                                                                    |
|  CORE                                                              |
|  +----------+  +----------------+  +---------+  +---------------+  |
|  |   Auth   |  | Organizations  |  | Gateway |  | Notifications |  |
|  | -users   |  | -organizations |  | -routes |  | -templates    |  |
|  | -sessions|  | -org_apps      |  | -logs   |  | -queue        |  |
|  | -roles   |  | -subscriptions |  | -rate   |  | -history      |  |
|  +----------+  +----------------+  +---------+  +---------------+  |
|                                                                    |
+====================================================================+
|                                                                    |
|  MODULES                                                           |
|  +-----------------+  +-------------------+  +------------------+  |
|  |   People        |  |   Groups          |  |   Finance        |  |
|  | -people         |  | -org_scopes       |  | -fin_categories  |  |
|  | -family_rels    |  | -scope_leaders    |  | -fin_transactions|  |
|  | -emergency_cont |  | -group_types      |  | -fin_pay_accounts|  |
|  |                 |  | -groups           |  |                  |  |
|  |                 |  | -group_members    |  |                  |  |
|  +-----------------+  +-------------------+  +------------------+  |
|                                                                    |
|  +--------------------+  +------------------+                      |
|  |   Accounting       |  |   Inventory      |                      |
|  | -chart_of_accounts |  | -products        |  (futuro)            |
|  | -journal_entries   |  | -stock_movements |                      |
|  | -journal_lines     |  | -warehouses      |                      |
|  | -fiscal_periods    |  | -categories      |                      |
|  +--------------------+  +------------------+                      |
|                                                                    |
+====================================================================+
|                                                                    |
|  APPS                                                              |
|  +-----------------+  +---------------+  +------------------+      |
|  |   Church        |  |   POS         |  |   HR             |      |
|  | -congregants    |  | -orders       |  | -employees       |      |
|  | -classes        |  | -order_items  |  | -contracts       |      |
|  | -enrollments    |  | -customers    |  | -payroll         |      |
|  | -activities     |  | -suppliers    |  | -vacations       |      |
|  | -attendance     |  | -pos_config   |  | -attendance      |      |
|  +-----------------+  +---------------+  +------------------+      |
|                                                                    |
|  +-----------------+  +---------------+                            |
|  |   CRM           |  |   Education   |                            |
|  | -leads          |  | -students     |                            |
|  | -opportunities  |  | -courses      |                            |
|  | -pipelines      |  | -grades       |                            |
|  | -tasks          |  | -schedules    |                            |
|  +-----------------+  +---------------+                            |
|                                                                    |
+====================================================================+
```

---

## Comunicacion entre Capas

### Fase Actual: Monolito Modular

En la fase actual, Savvy es un **monolito modular**: todas las capas viven en el mismo backend y se comunican mediante **imports directos de Python**:

```
backend/
  app/
    core/
      auth/
      organizations/
    modules/
      people/
        services/
        repositories/
        schemas/
      groups/
        services/
        repositories/
        schemas/
      finance/
        services/
        repositories/
        schemas/
      accounting/
        services/
        repositories/
        schemas/
    apps/
      church/
        services/       # Importan desde modules.people, modules.groups, etc.
        repositories/
        schemas/
        routers/
      pos/
        services/
        repositories/
        schemas/
        routers/
```

### Reglas de Dependencia

```
+-------------------------------------------------------------------+
|                                                                   |
|  PERMITIDO:                                                       |
|  App -> Module    (Church importa PeopleService)                  |
|  App -> Core      (Church importa Auth)                           |
|  Module -> Core   (People importa Organizations)                  |
|  Module -> Module (Finance importa Accounting)                    |
|                                                                   |
|  PROHIBIDO:                                                       |
|  Module -> App    (People NO puede importar Church)               |
|  Core -> Module   (Auth NO puede importar People)                 |
|  Core -> App      (Auth NO puede importar Church)                 |
|  App -> App       (Church NO puede importar POS)                  |
|                                                                   |
+-------------------------------------------------------------------+
```

### Futuro: Microservicios / HTTP / Eventos

Cuando la escala lo requiera, la migracion a microservicios sera natural porque las dependencias ya estan bien definidas:

```
Fase futura:
  - Cada modulo se convierte en un servicio independiente con su propia API
  - Las apps se comunican con modulos via HTTP o mensajeria (RabbitMQ, Redis Streams)
  - Los eventos permiten desacoplamiento asincrono:
    * Finance emite: "transaction.created"
    * Accounting escucha y crea el journal_entry
```

---

## Scopes Organizacionales y Liderazgo Multinivel

### Jerarquia de Scopes

Los scopes definen la **estructura organizacional** a traves de la cual fluyen los permisos y la visibilidad de datos:

```
ORGANIZACION (multi-tenancy boundary)
    |
    +-- Country: Colombia
    |     |
    |     +-- Zone: Zona Norte
    |     |     |
    |     |     +-- District: Distrito Barranquilla
    |     |     |     |
    |     |     |     +-- Church: Iglesia Central      <-- Unidad operativa
    |     |     |     +-- Church: Iglesia Sur
    |     |     |
    |     |     +-- District: Distrito Cartagena
    |     |           |
    |     |           +-- Church: Iglesia Principal
    |     |
    |     +-- Zone: Zona Sur
    |           |
    |           +-- ...
    |
    +-- Country: Panama
          |
          +-- Zone: Zona Capital
                |
                +-- ...
```

### Liderazgo Multinivel

Cada nivel del scope tiene lideres con roles especificos:

```
Country: Colombia
  Leader: Obispo General Martinez (role: bishop)

  Zone: Zona Norte
    Leader: Supervisor Rodriguez (role: supervisor)

    District: Distrito Barranquilla
      Leader: Pastor Distrital Gomez (role: district_pastor)

      Church: Iglesia Central
        Leaders:
          - Pastor Lopez (role: pastor, started_at: 2022-01-15)
          - Pastora Diaz (role: co_pastor, started_at: 2023-06-01)
          - Hno. Ramirez (role: treasurer, started_at: 2024-01-01)
```

### Visibilidad de Datos

La regla de visibilidad es **descendente e inclusiva**:

| Rol               | Nivel       | Ve datos de...                              |
|--------------------|-------------|---------------------------------------------|
| Obispo            | Country     | Todas las iglesias del pais                 |
| Supervisor        | Zone        | Todas las iglesias de su zona               |
| Pastor Distrital  | District    | Todas las iglesias de su distrito           |
| Pastor            | Church      | Solo su iglesia                             |

---

## Estrategia de Migracion (Resumen)

La migracion desde el estado actual (church-centric) al ecosistema modular se ejecuta en 4 fases. Ver documento completo en [migration-strategy.md](./migration-strategy.md).

```
+--------+     +---------+     +----------+     +---------+
| Fase 1 | --> | Fase 2  | --> | Fase 3   | --> | Fase 4  |
| Crear  |     | Migrar  |     | Reapuntar|     | Eliminar|
| modulos|     | datos   |     | Church   |     | legacy  |
+--------+     +---------+     +----------+     +---------+
```

| Fase | Accion                                    | Riesgo  | Duracion Estimada |
|------|-------------------------------------------|---------|-------------------|
| 1    | Crear modulos nuevos sin tocar Church     | Bajo    | 2-3 semanas       |
| 2    | Migrar datos a tablas nuevas              | Medio   | 1-2 semanas       |
| 3    | Reapuntar Church a modulos compartidos    | Alto    | 2-3 semanas       |
| 4    | Eliminar tablas legacy                    | Bajo    | 1 semana          |

---

## Lista de Tablas por Modulo

### Core

| Tabla              | Modulo        | Descripcion                          |
|--------------------|---------------|--------------------------------------|
| `auth.users`       | Auth          | Usuarios de Supabase Auth            |
| `user_profiles`    | Auth          | Perfil extendido del usuario         |
| `organizations`    | Organizations | Organizaciones (tenants)             |
| `org_members`      | Organizations | Miembros de una organizacion         |
| `org_apps`         | Organizations | Apps activas por organizacion        |
| `apps_registry`    | Organizations | Catalogo de apps disponibles         |

### Module: People

| Tabla                  | Descripcion                          |
|------------------------|--------------------------------------|
| `people`               | Registro central de personas         |
| `family_relationships` | Relaciones familiares bidireccionales|
| `emergency_contacts`   | Contactos de emergencia              |

### Module: Groups

| Tabla                    | Descripcion                          |
|--------------------------|--------------------------------------|
| `organizational_scopes`  | Jerarquia organizacional             |
| `scope_leaders`          | Lideres por scope con periodo        |
| `group_types`            | Plantillas de tipos de grupo         |
| `groups`                 | Instancias de grupos                 |
| `group_members`          | Miembros de grupos                   |

### Module: Finance

| Tabla                       | Descripcion                          |
|-----------------------------|--------------------------------------|
| `finance_categories`        | Categorias por app (TITHE, SALE)     |
| `finance_transactions`      | Transacciones financieras            |
| `finance_payment_accounts`  | Mapeo metodo pago -> cuenta contable |

### Module: Accounting

| Tabla                  | Descripcion                          |
|------------------------|--------------------------------------|
| `chart_of_accounts`    | Plan de cuentas contables            |
| `journal_entries`      | Asientos contables (encabezado)      |
| `journal_entry_lines`  | Lineas del asiento (debito/credito)  |
| `fiscal_periods`       | Periodos fiscales                    |

### App: Church

| Tabla                       | Descripcion                          |
|-----------------------------|--------------------------------------|
| `church_congregants`        | Datos eclesiasticos de congregantes  |
| `church_classes`            | Clases biblicas                      |
| `church_class_enrollments`  | Matriculas a clases                  |
| `church_activities`         | Cultos, eventos, actividades         |
| `church_attendance`         | Registro de asistencia               |

---

## Diagrama de Relaciones entre Modulos y Apps

```
+====================================================================+
|                                                                    |
|  CORE                                                              |
|  +-------+    +----------------+                                   |
|  | Auth  |--->| Organizations  |                                   |
|  +---+---+    +-------+--------+                                   |
|      |                |                                            |
|      |    (user_id)   | (organization_id)                          |
|      |                |                                            |
+======|================|===========================================+
|      v                v                                            |
|  MODULES                                                           |
|                                                                    |
|  +--------+     +---------+     +---------+     +------------+    |
|  | People |<--->| Groups  |     | Finance |---->| Accounting |    |
|  +---+----+     +----+----+     +----+----+     +------------+    |
|      |               |              |                              |
|      |  person_id    | scope_id     | category_id                  |
|      |  (FK en todo) | group_id     | transaction_id               |
|      |               |              |                              |
+======|===============|==============|=============================+
|      v               v              v                              |
|  APPS                                                              |
|                                                                    |
|  +-------------------+    +----------------+                       |
|  | SavvyChurch       |    | SavvyPOS       |                      |
|  |                   |    |                |                       |
|  | congregants       |    | orders         |                       |
|  |   -> person_id    |    |   -> person_id |                       |
|  | activities        |    | customers      |                       |
|  |   -> scope_id     |    |   -> scope_id  |                       |
|  | (finance: church) |    | (finance: pos) |                       |
|  | (groups: ministry)|    | (groups: team) |                       |
|  +-------------------+    +----------------+                       |
|                                                                    |
+====================================================================+

Leyenda:
  ---->  Dependencia directa (import)
  <--->  Dependencia bidireccional (People <-> Groups via scope_id en people)
  (FK)   Foreign key entre tablas
```

---

## Principios de Diseno

### 1. Reutilizacion

Cada pieza de funcionalidad se construye **una sola vez** y se reutiliza por todas las apps que la necesiten. No se duplica codigo ni datos.

```
CORRECTO:  10 apps usan 1 PeopleService
INCORRECTO: 10 apps tienen 10 tablas de personas diferentes
```

### 2. Bajo Acoplamiento

Cada capa solo conoce la capa inmediatamente inferior. Las apps no se conocen entre si. Los modulos no conocen las apps.

```
CORRECTO:  Church importa PeopleService (modulo generico)
INCORRECTO: PeopleService importa ChurchCongregantService (app especifica)
```

### 3. Alta Cohesion

Cada modulo y app agrupa toda la logica relacionada con su dominio. No hay "servicios dios" que hagan de todo.

```
CORRECTO:  PeopleService solo gestiona personas
INCORRECTO: PeopleService tambien gestiona ministerios y diezmos
```

### 4. Extensibilidad

Agregar una nueva app no requiere modificar ningún modulo existente. La nueva app simplemente consume los modulos que necesita.

```
Agregar SavvyCRM:
1. Crear carpeta apps/crm/
2. Crear tabla crm_leads (person_id FK -> people)
3. Usar PeopleService, FinanceService, GroupService
4. Cero cambios en People, Finance o Groups
```

### 5. Separacion de Datos y Logica

Los datos compartidos (personas, transacciones) viven en modulos. La logica especifica (que significa ser congregante, que es un diezmo) vive en las apps.

```
DATOS:   people.first_name = "Juan"          (Module: People)
LOGICA:  congregant.spiritual_status = "leader"  (App: Church)
DATOS:   transaction.amount = 500000          (Module: Finance)
LOGICA:  Es un diezmo porque category = TITHE (App: Church define la categoria)
```

### 6. Multi-tenancy First

Toda tabla tiene `organization_id`. Todo query filtra por organizacion. No hay datos cruzados entre organizaciones.

```sql
-- TODA consulta incluye el filtro de organizacion
SELECT * FROM people
WHERE organization_id = :org_id
  AND status = 'active';
```

### 7. Scope-based Access Control

Los permisos se basan en el scope organizacional del usuario. Un pastor solo ve su iglesia. Un supervisor ve toda su zona.

```python
# Middleware de filtrado por scope
async def filter_by_scope(user_scope_id: UUID):
    accessible_scopes = await get_descendant_scopes(user_scope_id)
    return Query.filter(scope_id__in=accessible_scopes)
```

---

> **Principio rector**: Savvy no es una app de iglesias que tambien hace POS. Savvy es una **plataforma de modulos reutilizables** sobre la cual se construyen apps verticales. Cada app es ciudadano de primera clase, y cada modulo es infraestructura compartida.
