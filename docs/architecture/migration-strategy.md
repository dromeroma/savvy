# Estrategia de Migracion — De Church-centric a Ecosystem

## Tabla de Contenidos

1. [Contexto](#contexto)
2. [Vision General](#vision-general)
3. [Fase 1: Crear Modulos Nuevos](#fase-1-crear-modulos-nuevos)
4. [Fase 2: Migrar Datos](#fase-2-migrar-datos)
5. [Fase 3: Reapuntar Church a Modulos Compartidos](#fase-3-reapuntar-church-a-modulos-compartidos)
6. [Fase 4: Eliminar Tablas Legacy](#fase-4-eliminar-tablas-legacy)
7. [Scripts de Migracion Conceptuales](#scripts-de-migracion-conceptuales)
8. [Rollback Plan por Fase](#rollback-plan-por-fase)
9. [Timeline Estimado](#timeline-estimado)
10. [Riesgos y Mitigaciones](#riesgos-y-mitigaciones)

---

## Contexto

### Estado Actual (Church-centric)

El sistema actual fue construido con SavvyChurch como app principal. Esto resulto en que logica reutilizable quedo atrapada dentro de Church:

```
ESTADO ACTUAL (problematico):

SavvyChurch contiene:
  - church_members        --> Datos de personas (deberia estar en People)
  - church_groups         --> Grupos/ministerios (deberia estar en Groups)
  - church_incomes        --> Ingresos (deberia estar en Finance)
  - church_expenses       --> Egresos (deberia estar en Finance)
  - church_scopes         --> Estructura org (deberia estar en Groups)
  - church_classes        --> OK, es exclusivo de Church
  - church_attendance     --> OK, es exclusivo de Church
```

### Estado Objetivo (Ecosystem)

```
ESTADO OBJETIVO (modular):

Module People:    people, family_relationships, emergency_contacts
Module Groups:    organizational_scopes, scope_leaders, group_types, groups, group_members
Module Finance:   finance_categories, finance_transactions, finance_payment_accounts
Module Accounting: chart_of_accounts, journal_entries, journal_entry_lines

App Church:       church_congregants, church_classes, church_class_enrollments,
                  church_activities, church_attendance
```

---

## Vision General

La migracion se ejecuta en **4 fases incrementales**, disenadas para que el sistema permanezca funcional en todo momento:

```
+====================================================================+
|                                                                    |
|  Fase 1          Fase 2          Fase 3          Fase 4            |
|  CREAR           MIGRAR          REAPUNTAR       ELIMINAR          |
|                                                                    |
|  +--------+      +--------+      +--------+      +--------+       |
|  | Crear  |      | Copiar |      | Church |      | Borrar |       |
|  | tablas |      | datos  |      | usa    |      | tablas |       |
|  | nuevas |      | legacy |      | modulos|      | legacy |       |
|  | (empty)|      | -> new |      | nuevos |      |        |       |
|  +--------+      +--------+      +--------+      +--------+       |
|                                                                    |
|  Riesgo:         Riesgo:         Riesgo:         Riesgo:           |
|  BAJO            MEDIO           ALTO            BAJO              |
|                                                                    |
|  Church sigue    Datos en        Cambio de       Solo limpieza     |
|  funcionando     ambos lados     codigo y        de tablas vacias  |
|  sin cambios     (dual write)    endpoints                         |
|                                                                    |
+====================================================================+
```

**Principio clave**: En ningun momento el sistema deja de funcionar. Cada fase es reversible.

---

## Fase 1: Crear Modulos Nuevos

### Objetivo

Crear todas las tablas, servicios, repositorios y endpoints de los modulos compartidos **sin modificar nada de Church**.

### Alcance

```
CREAR:
  backend/app/modules/people/
    - models/people.py
    - models/family_relationships.py
    - models/emergency_contacts.py
    - repositories/people_repository.py
    - services/people_service.py
    - schemas/people_schemas.py
    - routers/people_router.py

  backend/app/modules/groups/
    - models/organizational_scopes.py
    - models/scope_leaders.py
    - models/group_types.py
    - models/groups.py
    - models/group_members.py
    - repositories/...
    - services/...
    - schemas/...
    - routers/...

  backend/app/modules/finance/
    - models/finance_categories.py
    - models/finance_transactions.py
    - models/finance_payment_accounts.py
    - repositories/...
    - services/...
    - schemas/...
    - routers/...

NO TOCAR:
  backend/app/apps/church/  (sigue funcionando exactamente igual)
```

### Migraciones de Base de Datos

```sql
-- Fase 1: Crear tablas nuevas (no afectan las existentes)

-- Migration 001: Module People
CREATE TABLE people (...);
CREATE TABLE family_relationships (...);
CREATE TABLE emergency_contacts (...);

-- Migration 002: Module Groups
CREATE TABLE organizational_scopes (...);
CREATE TABLE scope_leaders (...);
CREATE TABLE group_types (...);
CREATE TABLE groups (...);
CREATE TABLE group_members (...);

-- Migration 003: Module Finance
CREATE TABLE finance_categories (...);
CREATE TABLE finance_transactions (...);
CREATE TABLE finance_payment_accounts (...);
```

### Validacion de Fase 1

- [ ] Todas las tablas nuevas creadas en Supabase
- [ ] Endpoints de cada modulo funcionando (CRUD basico)
- [ ] Tests unitarios para cada servicio
- [ ] Church sigue funcionando sin cambios
- [ ] No hay foreign keys cruzadas entre tablas nuevas y legacy

### Duracion Estimada: 2-3 semanas

---

## Fase 2: Migrar Datos

### Objetivo

Copiar datos de las tablas legacy de Church a las tablas nuevas de los modulos, manteniendo consistencia.

### Mapeo de Datos

```
+-----------------------------------------------------------------------+
|  TABLA LEGACY             -->  TABLAS NUEVAS                          |
+-----------------------------------------------------------------------+
|                                                                       |
|  church_members           -->  people + church_congregants            |
|    first_name, last_name  -->  people.first_name, people.last_name   |
|    email, phone           -->  people.email, people.phone            |
|    document_type/number   -->  people.document_type/number           |
|    membership_date        -->  church_congregants.membership_date    |
|    baptism_date           -->  church_congregants.baptism_date       |
|    spiritual_status       -->  church_congregants.spiritual_status   |
|                                                                       |
|  church_scopes            -->  organizational_scopes                 |
|    (misma estructura, solo renombrar)                                |
|                                                                       |
|  church_groups            -->  groups + group_types                   |
|    (separar tipo de grupo de instancia de grupo)                     |
|                                                                       |
|  church_incomes           -->  finance_transactions (type: income)   |
|    amount, date           -->  finance_transactions.amount, .date    |
|    category               -->  finance_categories (crear si no existe)|
|    member_id              -->  finance_transactions.person_id        |
|                                                                       |
|  church_expenses          -->  finance_transactions (type: expense)  |
|    amount, date           -->  finance_transactions.amount, .date    |
|    category               -->  finance_categories (crear si no existe)|
|                                                                       |
+-----------------------------------------------------------------------+
```

### Estrategia de Dual-Write

Durante la Fase 2, el sistema escribe en **ambos lados** (legacy y nuevo) para mantener sincronizacion:

```python
# Temporal: Dual-write durante migracion
class MigrationAwareMemberService:
    async def create_member(self, data: dict):
        # Escribir en tabla legacy (existente)
        legacy_member = await self.legacy_repo.create(data)

        # Tambien escribir en tablas nuevas
        person = await self.people_service.create(data["person_fields"])
        congregant = await self.congregant_repo.create(
            person_id=person.id,
            **data["church_fields"]
        )

        return legacy_member  # El frontend sigue usando la respuesta legacy
```

### Script de Migracion: Members -> People + Congregants

```sql
-- Paso 1: Migrar datos de personas
INSERT INTO people (
    id,                     -- Generar nuevo UUID
    organization_id,
    scope_id,
    first_name,
    last_name,
    second_last_name,
    email,
    phone,
    mobile,
    address,
    city,
    state,
    country,
    date_of_birth,
    gender,
    document_type,
    document_number,
    marital_status,
    occupation,
    photo_url,
    status,
    created_at
)
SELECT
    gen_random_uuid(),
    cm.organization_id,
    cm.scope_id,
    cm.first_name,
    cm.last_name,
    cm.second_last_name,
    cm.email,
    cm.phone,
    cm.mobile,
    cm.address,
    cm.city,
    cm.state,
    cm.country,
    cm.date_of_birth,
    cm.gender,
    cm.document_type,
    cm.document_number,
    cm.marital_status,
    cm.occupation,
    cm.photo_url,
    cm.status,
    cm.created_at
FROM church_members cm;

-- Paso 2: Crear tabla temporal de mapeo
CREATE TEMP TABLE member_person_map AS
SELECT
    cm.id AS legacy_member_id,
    p.id AS new_person_id
FROM church_members cm
JOIN people p ON
    p.organization_id = cm.organization_id
    AND p.email = cm.email
    AND p.first_name = cm.first_name
    AND p.last_name = cm.last_name;

-- Paso 3: Crear registros de congregantes
INSERT INTO church_congregants (
    id,
    person_id,
    scope_id,
    membership_date,
    baptism_date,
    conversion_date,
    spiritual_status,
    referred_by,
    pastoral_notes,
    status,
    created_at
)
SELECT
    gen_random_uuid(),
    mpm.new_person_id,
    cm.scope_id,
    cm.membership_date,
    cm.baptism_date,
    cm.conversion_date,
    cm.spiritual_status,
    NULL,                    -- referred_by se migra despues si aplica
    cm.pastoral_notes,
    cm.status,
    cm.created_at
FROM church_members cm
JOIN member_person_map mpm ON mpm.legacy_member_id = cm.id;
```

### Script de Migracion: Incomes -> Finance Transactions

```sql
-- Paso 1: Crear categorias financieras (si no existen)
INSERT INTO finance_categories (id, organization_id, app_code, code, name, type)
SELECT DISTINCT
    gen_random_uuid(),
    ci.organization_id,
    'church',
    UPPER(ci.category),
    ci.category,
    'income'
FROM church_incomes ci
ON CONFLICT (organization_id, app_code, code) DO NOTHING;

-- Paso 2: Migrar transacciones
INSERT INTO finance_transactions (
    id,
    organization_id,
    scope_id,
    category_id,
    type,
    app_code,
    amount,
    payment_method,
    person_id,
    description,
    transaction_date,
    status,
    created_at
)
SELECT
    gen_random_uuid(),
    ci.organization_id,
    ci.scope_id,
    fc.id,                   -- category_id del catalogo nuevo
    'income',
    'church',
    ci.amount,
    COALESCE(ci.payment_method, 'cash'),
    mpm.new_person_id,       -- person_id mapeado
    ci.description,
    ci.transaction_date,
    'confirmed',
    ci.created_at
FROM church_incomes ci
JOIN finance_categories fc ON
    fc.organization_id = ci.organization_id
    AND fc.app_code = 'church'
    AND fc.code = UPPER(ci.category)
LEFT JOIN member_person_map mpm ON mpm.legacy_member_id = ci.member_id;
```

### Validacion de Fase 2

- [ ] Conteo de registros: people == church_members (sin duplicados)
- [ ] Conteo de registros: finance_transactions == church_incomes + church_expenses
- [ ] Datos demograficos intactos (nombre, email, telefono)
- [ ] Datos eclesiasticos intactos (membership_date, baptism_date)
- [ ] Montos financieros cuadran (SUM legacy == SUM nuevo)
- [ ] Dual-write funcionando sin errores
- [ ] Church sigue funcionando normalmente

### Duracion Estimada: 1-2 semanas

---

## Fase 3: Reapuntar Church a Modulos Compartidos

### Objetivo

Modificar todo el codigo de SavvyChurch para que use los servicios de los modulos compartidos en lugar de acceder directamente a las tablas legacy.

### Cambios de Codigo

```
ANTES (legacy):
  ChurchMemberService
    -> church_members_repository (accede a church_members directamente)

DESPUES (modular):
  CongregantService
    -> people_service (accede a people)
    -> congregant_repository (accede a church_congregants)
```

### Cambios por Servicio

#### MemberService -> CongregantService + PeopleService

```python
# ANTES
class ChurchMemberService:
    async def create(self, data):
        return await self.member_repo.create(data)  # Todo en church_members

    async def get(self, id):
        return await self.member_repo.get(id)  # Todo de church_members

# DESPUES
class CongregantService:
    def __init__(self, people_service, congregant_repo):
        self.people = people_service
        self.congregants = congregant_repo

    async def create(self, person_data, church_data):
        person = await self.people.find_or_create(person_data)
        congregant = await self.congregants.create(
            person_id=person.id, **church_data
        )
        return {**person.dict(), **congregant.dict()}

    async def get(self, id):
        congregant = await self.congregants.get(id)
        person = await self.people.get(congregant.person_id)
        return {**person.dict(), **congregant.dict()}
```

#### IncomeService -> FinanceService (filtrado por app_code='church')

```python
# ANTES
class ChurchIncomeService:
    async def create(self, data):
        return await self.income_repo.create(data)  # church_incomes

# DESPUES
class ChurchFinanceService:
    def __init__(self, finance_service):
        self.finance = finance_service

    async def create_tithe(self, scope_id, person_id, amount, payment_method):
        category = await self.finance.get_category(
            app_code="church", code="TITHE"
        )
        return await self.finance.create_transaction(
            scope_id=scope_id,
            category_id=category.id,
            type="income",
            app_code="church",
            amount=amount,
            payment_method=payment_method,
            person_id=person_id
        )
```

#### GroupService -> SavvyGroups (filtrado por group_type)

```python
# ANTES
class ChurchGroupService:
    async def list_ministries(self, scope_id):
        return await self.group_repo.list(scope_id=scope_id)  # church_groups

# DESPUES
class ChurchMinistryService:
    def __init__(self, group_service):
        self.groups = group_service

    async def list_ministries(self, scope_id):
        ministry_type = await self.groups.get_type_by_code("ministry")
        return await self.groups.list(
            scope_id=scope_id,
            group_type_id=ministry_type.id
        )
```

### Cambios de Endpoints

```
ANTES:                              DESPUES:
GET /church/members          -->    GET /church/congregants
POST /church/members         -->    POST /church/congregants
GET /church/members/{id}     -->    GET /church/congregants/{id}
GET /church/incomes          -->    GET /finance/transactions?app_code=church&type=income
POST /church/incomes         -->    POST /church/tithes (wrapper sobre finance)
GET /church/groups           -->    GET /groups?scope_id=X&group_type_code=ministry
```

### Cambios de Frontend

```typescript
// ANTES
const members = await api.get('/church/members');

// DESPUES
const congregants = await api.get('/church/congregants');
// La respuesta incluye datos de persona + datos eclesiasticos (JOIN interno)
```

### Validacion de Fase 3

- [ ] Todos los endpoints legacy redirigidos o reemplazados
- [ ] Frontend actualizado para usar nuevos endpoints
- [ ] Tests end-to-end pasando
- [ ] Datos consistentes entre tablas nuevas
- [ ] Dual-write desactivado (solo se escribe en tablas nuevas)
- [ ] Performance comparable o mejor que antes
- [ ] Reportes financieros cuadran con datos historicos

### Duracion Estimada: 2-3 semanas

---

## Fase 4: Eliminar Tablas Legacy

### Objetivo

Eliminar las tablas legacy que ya no se usan, dejando solo las tablas de los modulos compartidos y las tablas exclusivas de Church.

### Pre-requisitos

- [ ] Fase 3 completada y estable por al menos 1 semana
- [ ] Ningun codigo referencia tablas legacy
- [ ] Backup completo de la base de datos
- [ ] Verificacion de que no hay triggers, views o funciones que referencien tablas legacy

### Tablas a Eliminar

```sql
-- Verificar que no hay datos huerfanos antes de eliminar
SELECT COUNT(*) FROM church_members;      -- Debe coincidir con people + congregants
SELECT COUNT(*) FROM church_incomes;      -- Debe coincidir con finance_transactions
SELECT COUNT(*) FROM church_expenses;     -- Debe coincidir con finance_transactions

-- Eliminar tablas legacy
DROP TABLE IF EXISTS church_incomes CASCADE;
DROP TABLE IF EXISTS church_expenses CASCADE;
DROP TABLE IF EXISTS church_members CASCADE;
DROP TABLE IF EXISTS church_groups CASCADE;     -- Si existia separado de groups
-- NO eliminar: church_classes, church_attendance (son de Church app)
```

### Tablas que se MANTIENEN (son de SavvyChurch)

```
church_congregants        (nueva, reemplaza church_members parcialmente)
church_classes            (ya existia, se mantiene)
church_class_enrollments  (nueva)
church_activities         (ya existia o nueva)
church_attendance         (ya existia, se mantiene)
```

### Validacion de Fase 4

- [ ] Tablas legacy eliminadas
- [ ] Aplicacion funcionando correctamente post-eliminacion
- [ ] No hay errores en logs
- [ ] Tests completos pasando
- [ ] Base de datos limpia, sin tablas huerfanas

### Duracion Estimada: 1 semana

---

## Scripts de Migracion Conceptuales

### Script Maestro de Migracion

```python
# scripts/migrate_church_to_ecosystem.py

import asyncio
from datetime import datetime

class EcosystemMigration:
    """
    Orquestador de migracion de Church-centric a Ecosystem.
    Cada paso es idempotente y puede ejecutarse multiples veces.
    """

    def __init__(self, db, org_id: str):
        self.db = db
        self.org_id = org_id
        self.log = []

    async def run_phase_2(self):
        """Fase 2: Migrar datos"""
        self._log("Inicio de migracion Fase 2")

        # Paso 1: Migrar personas
        count = await self._migrate_members_to_people()
        self._log(f"Personas migradas: {count}")

        # Paso 2: Crear congregantes
        count = await self._create_congregants()
        self._log(f"Congregantes creados: {count}")

        # Paso 3: Migrar scopes (si aplica)
        count = await self._migrate_scopes()
        self._log(f"Scopes migrados: {count}")

        # Paso 4: Crear categorias financieras
        count = await self._create_finance_categories()
        self._log(f"Categorias financieras creadas: {count}")

        # Paso 5: Migrar ingresos
        count = await self._migrate_incomes()
        self._log(f"Ingresos migrados: {count}")

        # Paso 6: Migrar egresos
        count = await self._migrate_expenses()
        self._log(f"Egresos migrados: {count}")

        # Paso 7: Validaciones
        await self._validate_migration()

        self._log("Migracion Fase 2 completada")
        return self.log

    async def _migrate_members_to_people(self) -> int:
        """
        Migra church_members -> people.
        Idempotente: solo migra los que no existen en people.
        """
        query = """
            INSERT INTO people (
                id, organization_id, scope_id,
                first_name, last_name, second_last_name,
                email, phone, mobile,
                address, city, state, country,
                date_of_birth, gender,
                document_type, document_number,
                marital_status, occupation, photo_url,
                status, created_at
            )
            SELECT
                gen_random_uuid(),
                cm.organization_id, cm.scope_id,
                cm.first_name, cm.last_name, cm.second_last_name,
                cm.email, cm.phone, cm.mobile,
                cm.address, cm.city, cm.state, cm.country,
                cm.date_of_birth, cm.gender,
                cm.document_type, cm.document_number,
                cm.marital_status, cm.occupation, cm.photo_url,
                cm.status, cm.created_at
            FROM church_members cm
            WHERE cm.organization_id = :org_id
              AND NOT EXISTS (
                  SELECT 1 FROM people p
                  WHERE p.organization_id = cm.organization_id
                    AND p.email = cm.email
                    AND p.first_name = cm.first_name
              )
            RETURNING id;
        """
        result = await self.db.execute(query, {"org_id": self.org_id})
        return len(result)

    async def _create_congregants(self) -> int:
        """
        Crea church_congregants para cada persona migrada.
        """
        query = """
            INSERT INTO church_congregants (
                id, person_id, scope_id,
                membership_date, baptism_date, conversion_date,
                spiritual_status, pastoral_notes,
                status, created_at
            )
            SELECT
                gen_random_uuid(),
                p.id,
                cm.scope_id,
                cm.membership_date, cm.baptism_date, cm.conversion_date,
                cm.spiritual_status, cm.pastoral_notes,
                cm.status, cm.created_at
            FROM church_members cm
            JOIN people p ON
                p.organization_id = cm.organization_id
                AND p.email = cm.email
                AND p.first_name = cm.first_name
                AND p.last_name = cm.last_name
            WHERE cm.organization_id = :org_id
              AND NOT EXISTS (
                  SELECT 1 FROM church_congregants cc
                  WHERE cc.person_id = p.id
                    AND cc.scope_id = cm.scope_id
              )
            RETURNING id;
        """
        result = await self.db.execute(query, {"org_id": self.org_id})
        return len(result)

    async def _validate_migration(self):
        """Valida que los conteos y totales coincidan."""
        # Conteo de personas
        legacy_count = await self.db.scalar(
            "SELECT COUNT(*) FROM church_members WHERE organization_id = :org_id",
            {"org_id": self.org_id}
        )
        new_count = await self.db.scalar(
            "SELECT COUNT(*) FROM people WHERE organization_id = :org_id",
            {"org_id": self.org_id}
        )
        assert new_count >= legacy_count, \
            f"Personas: legacy={legacy_count}, nuevo={new_count}"

        # Conteo de congregantes
        congregant_count = await self.db.scalar(
            "SELECT COUNT(*) FROM church_congregants cc "
            "JOIN people p ON cc.person_id = p.id "
            "WHERE p.organization_id = :org_id",
            {"org_id": self.org_id}
        )
        assert congregant_count == legacy_count, \
            f"Congregantes: legacy={legacy_count}, nuevo={congregant_count}"

        # Totales financieros
        legacy_income_total = await self.db.scalar(
            "SELECT COALESCE(SUM(amount), 0) FROM church_incomes "
            "WHERE organization_id = :org_id",
            {"org_id": self.org_id}
        )
        new_income_total = await self.db.scalar(
            "SELECT COALESCE(SUM(amount), 0) FROM finance_transactions "
            "WHERE organization_id = :org_id AND app_code = 'church' AND type = 'income'",
            {"org_id": self.org_id}
        )
        assert legacy_income_total == new_income_total, \
            f"Ingresos: legacy={legacy_income_total}, nuevo={new_income_total}"

        self._log("Validacion completada: todos los conteos coinciden")

    def _log(self, message: str):
        entry = f"[{datetime.now().isoformat()}] {message}"
        self.log.append(entry)
        print(entry)
```

---

## Rollback Plan por Fase

### Fase 1: Rollback Simple

```
Accion:     Eliminar tablas nuevas (DROP TABLE)
Impacto:    CERO — Church nunca fue modificado
Ejecucion:  < 5 minutos
```

```sql
-- Rollback Fase 1
DROP TABLE IF EXISTS group_members CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS group_types CASCADE;
DROP TABLE IF EXISTS scope_leaders CASCADE;
DROP TABLE IF EXISTS organizational_scopes CASCADE;
DROP TABLE IF EXISTS finance_payment_accounts CASCADE;
DROP TABLE IF EXISTS finance_transactions CASCADE;
DROP TABLE IF EXISTS finance_categories CASCADE;
DROP TABLE IF EXISTS emergency_contacts CASCADE;
DROP TABLE IF EXISTS family_relationships CASCADE;
DROP TABLE IF EXISTS people CASCADE;
DROP TABLE IF EXISTS church_congregants CASCADE;
DROP TABLE IF EXISTS church_class_enrollments CASCADE;
```

### Fase 2: Rollback con Limpieza

```
Accion:     Truncar tablas nuevas (datos migrados)
Impacto:    BAJO — Church sigue usando tablas legacy
Ejecucion:  < 10 minutos
```

```sql
-- Rollback Fase 2
TRUNCATE TABLE finance_transactions CASCADE;
TRUNCATE TABLE finance_categories CASCADE;
TRUNCATE TABLE church_congregants CASCADE;
TRUNCATE TABLE people CASCADE;
-- Las tablas quedan vacias pero siguen existiendo para Fase 1
```

### Fase 3: Rollback Complejo

```
Accion:     Revertir codigo al commit anterior a Fase 3
Impacto:    MEDIO — Requiere redespliegue del backend y frontend
Ejecucion:  30-60 minutos
```

```bash
# Rollback Fase 3
git revert --no-commit HEAD~N..HEAD   # N = commits de Fase 3
git commit -m "rollback: revert phase 3 migration"

# Reactivar dual-write si estaba desactivado
# Redesplegar backend y frontend
```

**Mitigacion**: Mantener una rama `pre-phase-3` con el codigo legacy funcional.

### Fase 4: Rollback desde Backup

```
Accion:     Restaurar tablas legacy desde backup
Impacto:    ALTO — Requiere restauracion de base de datos
Ejecucion:  1-2 horas
```

```
Prevencion:
- No ejecutar Fase 4 hasta que Fase 3 sea estable por 1+ semana
- Backup completo antes de DROP
- Validar con el equipo que nadie referencia tablas legacy
```

---

## Timeline Estimado

```
+====================================================================+
| Semana |  Actividad                                     | Fase     |
+========+================================================+==========+
|   1    |  Crear tablas People + servicios + tests        | Fase 1   |
|   2    |  Crear tablas Groups + Finance + servicios      | Fase 1   |
|   3    |  Tests integracion, endpoints, documentacion    | Fase 1   |
+--------+------------------------------------------------+----------+
|   4    |  Scripts de migracion + ejecucion en staging    | Fase 2   |
|   5    |  Validacion de datos + dual-write               | Fase 2   |
+--------+------------------------------------------------+----------+
|   6    |  Refactorizar servicios Church                  | Fase 3   |
|   7    |  Refactorizar endpoints + frontend              | Fase 3   |
|   8    |  QA completo, tests E2E, fix de bugs            | Fase 3   |
+--------+------------------------------------------------+----------+
|   9    |  Estabilizacion + monitoreo                     | Buffer   |
+--------+------------------------------------------------+----------+
|  10    |  Eliminar tablas legacy + limpieza              | Fase 4   |
+--------+------------------------------------------------+----------+

Total estimado: 8-10 semanas
```

### Pre-requisitos por Fase

| Fase | Pre-requisito                                              |
|------|------------------------------------------------------------|
| 1    | Diseno de tablas aprobado, branch de desarrollo creado     |
| 2    | Fase 1 completa, ambiente de staging disponible            |
| 3    | Fase 2 validada, tests de regresion listos                 |
| 4    | Fase 3 estable por 1+ semana, backup verificado            |

---

## Riesgos y Mitigaciones

### Riesgo 1: Perdida de datos durante migracion

| Aspecto      | Detalle                                                    |
|--------------|------------------------------------------------------------|
| Probabilidad | Media                                                      |
| Impacto      | Critico                                                    |
| Mitigacion   | Backup antes de cada fase. Scripts idempotentes. Validacion de conteos post-migracion. Ambiente de staging para pruebas previas. |
| Rollback     | Restaurar desde backup                                     |

### Riesgo 2: Inconsistencia de datos durante dual-write

| Aspecto      | Detalle                                                    |
|--------------|------------------------------------------------------------|
| Probabilidad | Media                                                      |
| Impacto      | Alto                                                       |
| Mitigacion   | Transacciones atomicas (legacy + nuevo en una sola transaccion). Job de reconciliacion que compare conteos periodicamente. Alertas si los conteos divergen. |
| Rollback     | Desactivar dual-write, volver a solo legacy                |

### Riesgo 3: Performance degradada con JOINs entre modulos

| Aspecto      | Detalle                                                    |
|--------------|------------------------------------------------------------|
| Probabilidad | Baja                                                       |
| Impacto      | Medio                                                      |
| Mitigacion   | Indices apropiados en todas las foreign keys. Queries optimizados (evitar N+1). Views materializadas para reportes pesados. Benchmark antes y despues de Fase 3. |
| Rollback     | Optimizar queries, agregar cache                           |

### Riesgo 4: Frontend roto por cambio de endpoints

| Aspecto      | Detalle                                                    |
|--------------|------------------------------------------------------------|
| Probabilidad | Alta                                                       |
| Impacto      | Alto                                                       |
| Mitigacion   | Endpoints legacy con redirect temporal (HTTP 307). Versionado de API (/v1/ vs /v2/). Feature flags para migrar frontend gradualmente. QA exhaustivo del frontend antes de desactivar endpoints legacy. |
| Rollback     | Reactivar endpoints legacy                                 |

### Riesgo 5: Tiempo de migracion excede el estimado

| Aspecto      | Detalle                                                    |
|--------------|------------------------------------------------------------|
| Probabilidad | Alta                                                       |
| Impacto      | Medio                                                      |
| Mitigacion   | Buffer de 2 semanas incluido en el timeline. Cada fase es independiente y desplegable. Scope rigido: no agregar features durante migracion. Fases 1 y 2 no afectan al usuario final. |
| Rollback     | Pausar migracion, Church sigue funcionando                 |

### Riesgo 6: Migracion de datos financieros con errores de redondeo

| Aspecto      | Detalle                                                    |
|--------------|------------------------------------------------------------|
| Probabilidad | Baja                                                       |
| Impacto      | Critico                                                    |
| Mitigacion   | Usar DECIMAL(15,2) en ambos lados. Validar SUM(legacy) == SUM(nuevo) al centavo. Comparar reporte financiero legacy vs nuevo lado a lado. No migrar datos financieros parcialmente. |
| Rollback     | Recalcular desde datos legacy                              |

---

### Checklist Final de Migracion

```
PRE-MIGRACION:
[ ] Backup completo de produccion
[ ] Ambiente de staging con copia de datos reales
[ ] Scripts de migracion probados en staging
[ ] Plan de comunicacion a usuarios (si hay downtime)
[ ] Equipo disponible para soporte post-migracion

POST-MIGRACION (por fase):
[ ] Conteos de registros validados
[ ] Totales financieros cuadrados
[ ] Tests automatizados pasando
[ ] Frontend funcionando correctamente
[ ] Logs sin errores criticos
[ ] Performance aceptable
[ ] Rollback plan verificado
```

---

> **Principio rector**: La migracion es un maraton, no un sprint. Cada fase debe ser estable antes de avanzar a la siguiente. Es preferible tardar mas y hacerlo bien que apresurarse y perder datos.
