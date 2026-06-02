# Análisis técnico y arquitectónico del ecosistema **Savvy**

> Documento de referencia para compartir con otra IA / agente.
> Versión del análisis: 1.0 — Fecha de corte: junio 2026 (sobre `main`, v0.0.89).
> Fuente: lectura directa del repositorio + `AI_STATE.md` + `docs/architecture/*`.

---

## 1 · Visión general del proyecto

### 1.1 Qué es Savvy

**Savvy** (también referida internamente como *SavvyCore*) es una **plataforma SaaS multi-tenant modular** desarrollada por la empresa colombiana **Savvitrix Solutions**. No es un único producto: es un **ecosistema de aplicaciones verticales** que comparten infraestructura, base de datos, autenticación, RBAC, dominio común (personas, organizaciones, contabilidad) y panel de superadmin de plataforma.

Cada vertical es comercializable de forma independiente bajo una marca propia (*SavvyChurch*, *SavvyMemorial*, *SavvyWater*, *SavvyPOS*, etc.), pero todas viven dentro del mismo monolito modular y comparten un kernel transversal.

### 1.2 Objetivo principal

Construir una **plataforma única** sobre la cual cualquier vertical de negocio (iglesias, funerarias, acueductos comunales, conjuntos residenciales, clínicas, instituciones educativas, comercios) pueda operarse end-to-end (operación + facturación + cartera + cobros + reportes + cliente final) **sin tener que rehacer la infraestructura de cero cada vez**.

El usuario final (la empresa cliente) activa solo las apps que necesita, paga una suscripción mensual y obtiene tanto el back-office para sus empleados como el portal público para sus afiliados/clientes.

### 1.3 Tipo de plataforma / ecosistema

| Característica | Valor |
|---|---|
| Modelo de negocio | **B2B SaaS multi-tenant** con suscripciones (`starter / pro / enterprise / platform`) |
| Tipo de despliegue | **Cloud-hosted**, monolito modular en una sola región (us-west-2) |
| Aislamiento entre clientes | Lógico — base compartida, columna `organization_id` + RLS de PostgreSQL |
| Arquitectura interna | Monolito modular Python (FastAPI) + SPA Angular |
| Modelo de extensión | Apps verticales bajo `backend/src/apps/<code>/` y `frontend/src/app/apps/<code>/`, registradas en `app_registry` |
| Modelo de cobro | Por organización (plan + activación granular de apps) |
| Multilingüe | UI en español; arquitectura preparada para i18n |

### 1.4 Problemas que busca resolver

1. **Fragmentación del software vertical de PYME**: hoy una iglesia, una funeraria o un acueducto comunal usan 5-7 herramientas distintas (Excel + WhatsApp + un POS local + una cartera improvisada + Word para documentos). Savvy unifica todo en una sola plataforma.
2. **Falta de un dominio común reutilizable**: personas, contabilidad, facturación y cobranza se reescriben en cada producto vertical. Savvy las ofrece como **módulos compartidos** (`people`, `finance`, `accounting`, `apps`).
3. **Cero portal del afiliado/cliente** en estas verticales: Savvy expone portales públicos (ej: `/memorial-portal`, `/water-portal`) con login propio para que el cliente final vea su contrato, cuotas y pagos sin intervención del operador.
4. **RBAC propio por app inalcanzable para PYME**: Savvy entrega catálogo de roles y permisos por app (`app_role_catalog`, `app_permission_catalog`), con roles personalizables por organización.
5. **Visibilidad financiera consolidada**: el dashboard ejecutivo cross-app agrega ingresos, cartera y alertas de las 12 apps activadas en una organización.

---

## 2 · Arquitectura general

### 2.1 Stack tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Backend runtime | Python | 3.12+ |
| Framework HTTP | FastAPI | ≥ 0.115 |
| ORM | SQLAlchemy 2.0 async + asyncpg | — |
| Validación | Pydantic | v2 |
| Auth | JWT (HS256) con access + refresh tokens y family rotation | — |
| Password hashing | passlib + bcrypt 4.x | — |
| PDF | xhtml2pdf + Jinja2 (facturas, reportes) | — |
| Frontend framework | Angular standalone (no NgModules) | 20.x |
| Frontend lenguaje | TypeScript | 5.9 |
| Frontend estado | Signals + RxJS BehaviorSubject | — |
| CSS | Tailwind CSS | v4 |
| Visualización | D3.js (genograma familiar SavvyFamily) | 7.x |
| Date picker | flatpickr + input HTML5 nativo | — |
| Base de datos | PostgreSQL via Supabase (PgBouncer, RLS habilitado) | 17 |
| Hosting backend | Render (Docker, 1 worker, pool 5+5) | — |
| Hosting frontend | Vercel (`app.savvytrix.com`) | — |
| Hosting DB | Supabase (proyecto `cdvwtgfyetonidjfwflt`, región us-west-2) | — |

### 2.2 Estructura física del repositorio

```
Savvy/
├── backend/
│   ├── src/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── gateway/router.py          # Router central /api/v1/*
│   │   ├── core/                      # config, DB, security, middleware, exceptions
│   │   ├── modules/                   # módulos compartidos transversales
│   │   └── apps/                      # apps verticales
│   ├── scripts/                       # setup_*.py + seed_*.py (idempotentes)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/app/
│   │   ├── shell/                     # layout, auth, dashboard, settings
│   │   ├── platform/                  # super-admin panel
│   │   ├── memorial-portal/           # portal público del afiliado (SavvyMemorial)
│   │   ├── core/                      # services, guards, interceptors
│   │   ├── shared/                    # componentes y servicios reutilizables
│   │   └── apps/                      # vistas por app vertical
│   ├── vercel.json
│   └── package.json
└── docs/                              # arquitectura, módulos, apps, guías, análisis
```

### 2.3 Patrón de cada módulo o app (uniforme)

Cada feature (módulo compartido o sub-módulo de app) sigue el patrón:

```
<feature>/
├── __init__.py
├── models.py      # ORM SQLAlchemy: BaseMixin + OrgMixin + Base
├── schemas.py     # Pydantic v2 request/response
├── service.py     # Lógica de negocio stateless (static methods)
└── router.py      # FastAPI endpoints (Depends get_db, get_org_id)
```

### 2.4 API gateway interno

El archivo `backend/src/gateway/router.py` agrupa todos los routers bajo `/api/v1/`:

```python
api_router = APIRouter(prefix="/api/v1")

# Núcleo
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(dashboard_router)
api_router.include_router(organization_router)
api_router.include_router(platform_router)

# Compartidos
api_router.include_router(apps_router)
api_router.include_router(accounting_router)
api_router.include_router(people_router)
api_router.include_router(groups_router)
api_router.include_router(finance_router)
api_router.include_router(geography_router)

# Verticales (apps)
api_router.include_router(church_router)
api_router.include_router(edu_router)
api_router.include_router(family_router)
api_router.include_router(credit_router)
api_router.include_router(crm_router)
api_router.include_router(parking_router)
api_router.include_router(condo_router)
api_router.include_router(health_router)
api_router.include_router(pay_router)
api_router.include_router(pos_router)
api_router.include_router(water_router)
api_router.include_router(memorial_router)
api_router.include_router(memorial_portal_router)  # público, sin auth admin
```

### 2.5 Bases de datos

- **Supabase PostgreSQL 17** — proyecto `cdvwtgfyetonidjfwflt`, ~150 tablas.
- **Connection pool**: PgBouncer (pooler en puerto 6543) + SQLAlchemy pool (5+5).
- **RLS (Row Level Security)** habilitado en todas las tablas con `organization_id`.
- **UUIDs** vía `gen_random_uuid()` como PK universal.
- **Timestamps**: `created_at` + `updated_at` con `timezone`.
- **No usa Alembic** para versionado: DDL aplicado vía scripts idempotentes `setup_<phase>.py` directos contra Supabase.

### 2.6 Autenticación y RBAC

Modelo de **tres capas** de autorización:

```
┌──────────────────────────────────────────────────────────────┐
│ CAPA 1 — Platform role (Savvitrix Solutions)                 │
│ users.platform_roles ∋ 'super_admin'                         │
│ Acceso a /api/v1/platform/* — gestiona TODAS las orgs        │
└──────────────────────────────────────────────────────────────┘
            │
┌──────────────────────────────────────────────────────────────┐
│ CAPA 2 — Membership (rol en la organización)                 │
│ memberships.role ∈ {owner, admin, member, customer}          │
│ owner → bypass de permisos de app                            │
└──────────────────────────────────────────────────────────────┘
            │
┌──────────────────────────────────────────────────────────────┐
│ CAPA 3 — App role (per-app)                                  │
│ app_user_roles[user, org, app] → app_role_catalog            │
│ Cada rol contiene una lista de permission codes              │
│ require_permission(app_code, *perms) verifica acceso         │
└──────────────────────────────────────────────────────────────┘
```

- **JWT**: contiene `sub` (user_id), `org_id`, `role` (membership), `platform_roles` (lista).
- **Refresh tokens**: rotación con detección de reutilización (`refresh_tokens.family_id`).
- **Portales públicos** (memorial-portal): JWT propio con `scope: 'memorial_portal'` + `contract_id`. No comparte sesión con el back-office.

### 2.7 Infraestructura y despliegue

```
┌───────────────┐         ┌────────────────────┐        ┌───────────────────┐
│  Vercel       │         │  Render            │        │  Supabase         │
│  (frontend)   │ ──HTTPS─▶  (backend)         │ ──TLS─▶│  (PostgreSQL 17)  │
│  Angular SPA  │         │  FastAPI Docker    │        │  + PgBouncer      │
│  app.savvy    │         │  savvy-8otl        │        │  + RLS            │
│  trix.com     │         │  .onrender.com     │        │                   │
└───────────────┘         └────────────────────┘        └───────────────────┘
```

- **Vercel**: build automático desde `main` con `vercel.json` → frontend en `app.savvytrix.com`.
- **Render**: Docker image desde `main`, single worker (memoria limitada a starter tier), variables de entorno con prefijo `SAVVY_`.
- **CORS**: backend permite el dominio del frontend.
- **CI/CD**: `git push main` → ambos deploys disparados.

### 2.8 IA / automatizaciones existentes

Actualmente **no hay IA en runtime** (no se invocan modelos LLM desde el backend). Lo que existe es:

- **`AI_STATE.md`** — documento vivo del estado del proyecto pensado para que LLMs externos (Claude, GPT) puedan navegar la base sin perder contexto.
- **Auditoría inmutable** (`memorial_audit_log`, `platform_audit_log`) como base de datos lista para alimentar a un agente.
- **Generación de PDFs** vía Jinja2 + xhtml2pdf (facturas, comprobantes, contratos).
- **Compartir por WhatsApp** vía `wa.me/?text=...` (sin API, link puro).

No hay agentes, cron jobs ni workers async hoy. Toda la lógica es síncrona disparada por requests HTTP.

---

## 3 · Módulos del sistema

### 3.1 Módulos compartidos (`backend/src/modules/`)

#### 3.1.1 `auth`

| Campo | Valor |
|---|---|
| Función | Autenticación + emisión de JWT + registro |
| Tablas | `users`, `refresh_tokens` |
| Dependencias | Ninguna (es la base) |
| Consumido por | Todos los módulos |
| Datos que maneja | email, password_hash (bcrypt), platform_roles (lista de strings) |

Endpoints: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`.

#### 3.1.2 `organization`

| Campo | Valor |
|---|---|
| Función | Multi-tenancy — orgs + memberships + invitaciones |
| Tablas | `organizations`, `memberships`, `invitations`, `business_type_catalog` |
| Dependencias | `auth` |
| Consumido por | Todos los módulos |
| Datos | `slug`, `name`, `type` (business/platform), `business_type` (iglesia, funeraria, etc.) |

#### 3.1.3 `platform`

| Campo | Valor |
|---|---|
| Función | Super-admin panel para Savvitrix (multi-org) |
| Tablas | `platform_roles`, `user_platform_roles`, `subscription_plans`, `platform_features`, `plan_features`, `organization_subscriptions`, `organization_feature_overrides`, `platform_audit_log`, `app_role_catalog`, `app_permission_catalog` |
| Endpoints | 48 endpoints bajo `/api/v1/platform/*` |
| Función crítica | Activar apps por org, gestionar planes, ver MRR, reset passwords, roles custom |

#### 3.1.4 `apps`

| Campo | Valor |
|---|---|
| Función | Registry central de las apps verticales + RBAC per-app |
| Tablas | `app_registry`, `organization_apps`, `app_user_roles` |
| Función crítica | `require_permission(app_code, *perms)` — dependency factory que: (1) bypass super_admin, (2) bypass owner de org, (3) lookup en `app_role_catalog`, (4) verifica que CUALQUIERA de los permisos requeridos esté presente. Resultado cacheado en `request.state._perm_cache`. |

#### 3.1.5 `people`

| Campo | Valor |
|---|---|
| Función | Persona como entidad reutilizable cross-app |
| Tablas | `people`, `family_relationships`, `emergency_contacts` |
| Patrón | Cada app vertical que necesita personas (estudiantes, congregantes, prestatarios, pacientes) referencia `people.id` y agrega atributos en su propia tabla. |
| Consumido por | Church, Edu, Family, Credit, CRM, Health |

#### 3.1.6 `groups`

| Campo | Valor |
|---|---|
| Función | Jerarquía organizacional reutilizable (scopes) |
| Tablas | `organizational_scopes`, `group_types`, `groups`, `group_members`, `scope_leaders` |
| Consumido por | Church (jerarquía pastoral, RBAC contextual), Edu |
| Patrón | Recursive CTE para analytics multi-scope |

#### 3.1.7 `finance`

| Campo | Valor |
|---|---|
| Función | Backbone financiero del ecosistema |
| Tablas | `finance_categories`, `finance_transactions`, `finance_payment_accounts` |
| Función | Toda app que registra ingresos/egresos (Church offerings, Edu tuition, Credit payments) escribe aquí en lugar de tener su propia tabla. |
| Consumido por | Church, Edu, Credit |

#### 3.1.8 `accounting`

| Campo | Valor |
|---|---|
| Función | Contabilidad doble partida |
| Tablas | `chart_of_accounts`, `fiscal_periods`, `journal_entries`, `journal_entry_lines` |
| Motor | `AccountingEngine` — asientos automáticos desde transacciones de `finance` |
| Reportes | Estado de resultados, Balance general |

#### 3.1.9 `geography`

| Campo | Valor |
|---|---|
| Función | Catálogo geográfico |
| Tablas | `geo_countries`, `geo_states`, `geo_cities` |
| Consumido por | `people` (direcciones), `health`, `parking` |

#### 3.1.10 `dashboard`

| Campo | Valor |
|---|---|
| Función | Dashboard ejecutivo cross-app |
| Endpoint | `GET /api/v1/dashboard/summary` |
| Funcionalidad | Extractores de KPIs por app activa + agregador cross-app (suma ingresos, cartera, alertas) usando claves convencionales (`.income_month`, `.receivables`, `.alert`) |
| Apps cubiertas | 12: church, memorial, water, pos, parking, health, pay, condo, credit, edu, family, crm |

### 3.2 Apps verticales (`backend/src/apps/`)

#### 3.2.1 SavvyChurch (`church`)

| Campo | Valor |
|---|---|
| Función | Gestión integral de iglesias |
| Sub-módulos | 11 — congregants, events, attendance, visitors, finance, pastoral, doctrine, social_aid, rotations, reports, dashboard |
| Tablas | 16 (church_congregants, church_events, church_attendance, church_visitors, church_member_lifecycle, church_transfers, church_pastoral_notes, church_doctrine_groups, church_doctrine_enrollments, church_doctrine_attendance, church_aggregate_offerings, church_aid_programs, church_aid_beneficiaries, church_aid_distributions, church_rotations, church_rotation_assignments) |
| Frontend | 12 vistas |
| Delega a | `PeopleService`, `GroupService`, `FinanceService`, `AccountingEngine` |
| Datos clave | Congregantes (extiende `people`), ofrendas (espejadas en `finance_transactions`), notas pastorales (privadas con scope) |

#### 3.2.2 SavvyEdu (`edu`)

| Campo | Valor |
|---|---|
| Función | Gestión académica completa |
| Sub-módulos | 11 — config, structure, students, teachers, enrollment, scheduling, attendance, grading, finance, documents |
| Tablas | 26 (períodos, programas, cursos, secciones, matrículas, horarios, asistencia, evaluaciones, notas finales, cobros de matrícula, becas, documentos emitidos) |
| Motor | `GradingEngine` (ponderación + conversión a escala configurable), `SchedulingService` (detección de conflictos sala+docente) |
| Config-driven | Todo (grading_systems, evaluation_templates, period_types) parametrizable por org |

#### 3.2.3 SavvyFamily (`family`)

| Campo | Valor |
|---|---|
| Función | Genograma familiar + anotaciones clínicas cross-app |
| Tablas | 4 (family_units, family_members, family_relationship_meta, family_annotations) |
| Visualización | SVG con D3.js — simbología clínica estándar |
| Anotaciones | 19 categorías (substance_abuse, mental_health, violence, …) con `source_app` para que vengan de Church, Health o Edu |

#### 3.2.4 SavvyCredit (`credit`)

| Campo | Valor |
|---|---|
| Función | Gestión de cartera crediticia |
| Sub-módulos | 7 (products, borrowers, applications, loans, payments, restructuring, dashboard) |
| Tablas | 11 |
| Motor | `CreditEngine` — 4 métodos de amortización (francés, alemán, flat, bullet), conversión de tasas, asignación configurable (interest_first / principal_first / proportional) |
| Ciclo de vida | pending → active → current/delinquent → paid_off / written_off / restructured |

#### 3.2.5 SavvyCRM (`crm`)

| Campo | Valor |
|---|---|
| Función | Pipeline comercial genérico |
| Sub-módulos | 6 (pipelines, deals, leads, contacts, companies, activities) |
| Tablas | 9 |
| Casos de uso | Leads → deals → won/lost; actividades (call, meeting, email) sobre cualquier entidad |

#### 3.2.6 SavvyParking (`parking`)

| Campo | Valor |
|---|---|
| Función | Gestión de parqueaderos urbanos |
| Sub-módulos | 6 (infrastructure, pricing, vehicles, sessions, services) |
| Tablas | 10 |
| Motor | `PricingEngine` — tarifas por tiempo, zona, tipo de vehículo, suscripción mensual |

#### 3.2.7 SavvyCondo (`condo`)

| Campo | Valor |
|---|---|
| Función | Conjuntos residenciales |
| Sub-módulos | 8 (properties, residents, fees, communication, areas, governance, maintenance) |
| Tablas | 11 |
| Funcionalidad | Cuotas por coeficiente, asambleas digitales con votaciones, reservas de áreas comunes |

#### 3.2.8 SavvyHealth (`health`)

| Campo | Valor |
|---|---|
| Función | Software clínico ligero (EHR + agenda + facturación) |
| Sub-módulos | 6 (patients, providers, services, appointments, clinical) |
| Tablas | 12 |
| Funcionalidad | EHR con notas SOAP, citas, diagnósticos, prescripciones, laboratorio |

#### 3.2.9 SavvyPay (`pay`)

| Campo | Valor |
|---|---|
| Función | **Backbone financiero** del ecosistema (no comercializada solo, soporta a otras) |
| Sub-módulos | 7 (transactions, wallets, ledger, subscriptions, fees, payouts) |
| Tablas | 11 |
| Estados | pending → authorized → captured → settled; cancelled / failed / refunded |
| Trazabilidad | `source_app`, `source_ref_type`, `source_ref_id` para vincular cualquier transacción de pago con su origen en otra app |

#### 3.2.10 SavvyPOS (`pos`)

| Campo | Valor |
|---|---|
| Función | Punto de venta cloud |
| Sub-módulos | 6 (catalog, inventory, registers, sales, config) |
| Tablas | 11 |
| Versión externa | `pos_local` (LocalFirst, código aparte registrado en `app_registry`) |

#### 3.2.11 SavvyWater (`water`)

| Campo | Valor |
|---|---|
| Función | Acueductos comunales — facturación por lectura |
| Sub-módulos | subscribers, meters, tariffs, routes, consumptions, invoices, payments, cartera, treasury, pqrs, portal, dashboard |
| Patrón | Replica el patrón Memorial: app + portal público para el suscriptor |
| Mora | Mora compuesta idempotente `base × rate × meses_vencidos` |

#### 3.2.12 SavvyMemorial (`memorial`) — vertical más reciente y completa

| Campo | Valor |
|---|---|
| Función | Gestión funeraria integral end-to-end |
| Sub-módulos | 13 (services, plans, contracts, invoices, payments, cartera, logistics, transfers, inventory, hr, crm, portal, reports, audit) |
| Tablas | ~25 |
| Fases construidas | 7 fases secuenciales (servicios → planes/contratos → facturas/pagos → logística/traslados → inventario/RRHH → CRM/portal → reportes/auditoría) |
| Portal del cliente | `/memorial-portal` — login público sin password (org_slug + email/doc), JWT scope `memorial_portal` válido 24h, embebe `contract_id` |
| Mora | Compuesta idempotente sobre cuotas de plan exequial |
| Demo seedeado | 100 contratos, 640 cuotas, 538 pagos en `Funeraria San Rafael` (org `memorial-demo`) |

---

## 4 · Relaciones del ecosistema

### 4.1 Diagrama lógico de dependencias

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PLATAFORMA                                 │
│  Savvitrix → super_admin → platform_module → ALL orgs               │
└────────────────────────────┬────────────────────────────────────────┘
                             │ activa apps via OrganizationApp
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ORGANIZATION (tenant)                         │
│  organizations + memberships + invitations                          │
└───────────┬────────────────────────┬────────────────────────────────┘
            │                        │
            │ membership.role        │ app_user_roles (per-app)
            │ (owner/admin/...)      │
            ▼                        ▼
   ┌──────────────────┐    ┌─────────────────────┐
   │   USERS / AUTH   │    │   APP_ROLE_CATALOG  │
   │  users + tokens  │◀──▶│  + PERMISSION CAT.  │
   └──────────────────┘    └─────────────────────┘
            │
            │ extiende como persona
            ▼
   ┌──────────────────┐
   │      PEOPLE      │◀───────────┬───────────┬───────────┬─────────┐
   │ (cross-app base) │            │           │           │         │
   └──────────────────┘            │           │           │         │
                                  ▲           ▲           ▲         ▲
                          ┌───────┴────┐ ┌────┴────┐ ┌────┴─┐  ┌────┴──┐
                          │ congregant │ │ student │ │ patient │ borrower │
                          │  (church)  │ │  (edu)  │ │ (health)│ (credit) │
                          └────────────┘ └─────────┘ └─────────┘  └───────┘

┌─────────────────────────────────────────────────────────────────────┐
│              MOTOR FINANCIERO COMPARTIDO                            │
│   FINANCE_TRANSACTIONS ◀── escribe ── Church, Edu, Credit, …        │
│           │                                                         │
│           ▼                                                         │
│   ACCOUNTING (chart_of_accounts → journal_entries)                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              MOTOR DE PAGOS — SavvyPay                              │
│  pay_transactions con source_app/source_ref_type/source_ref_id      │
│   ▲                                                                 │
│   │ posible referencia desde:                                       │
│   │   pos_sales, memorial_payments, water_payments, condo_fees, …   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Tipos de relaciones existentes

| Tipo de relación | Implementación | Ejemplo |
|---|---|---|
| **Composición fuerte** | FK con `ON DELETE CASCADE` | `memorial_services → memorial_service_events` |
| **Composición débil** | FK con `ON DELETE SET NULL` | `memorial_services.cemetery_id → memorial_locations` |
| **Extensión de persona** | UNIQUE(`org_id`, `person_id`) | `edu_students`, `church_congregants`, `health_patients` |
| **Reflejo entre apps** | escribir a tabla compartida con `reference_type` + `reference_id` | `church_aggregate_offerings → finance_transactions` |
| **Permiso contextual** | `app_user_roles` + `app_role_catalog.permissions` JSONB | `pos.sales.create`, `church.doctrine.manage` |
| **Activación de app por org** | `organization_apps.status` IN (`active`, `trial`, `suspended`) | Memorial activado en `memorial-demo` |
| **Auditoría inmutable** | `*_audit_log` tablas insert-only | `memorial_audit_log`, `platform_audit_log` |
| **Trazabilidad de pagos** | `source_app + source_ref_type + source_ref_id` | un pago en `pay_transactions` apunta a la factura origen |

### 4.3 Eventos y automatizaciones

Hoy el sistema **no tiene un bus de eventos formal** (ni Redis pub/sub, ni un message broker, ni domain events). Las "automatizaciones" están en código síncrono:

1. **Generación batch de cuotas exequiales** (`InvoicesService.batch_generate_dues`) — cron manual.
2. **Recálculo de cartera con mora compuesta** (idempotente — se puede correr N veces sin duplicar).
3. **Asiento contable automático** al registrar un pago (delegación finance → accounting).
4. **Avance de `next_payment_date`** en contratos exequiales al generar cuota.

Todo esto es **driven por endpoints HTTP**, no por eventos. Sería un punto de evolución obvio.

---

## 5 · Flujo de información

### 5.1 Flujo de un usuario administrador

```
1. Usuario abre app.savvytrix.com/auth/login
                ↓
2. Frontend Angular envía POST /api/v1/auth/login
                ↓
3. Backend valida bcrypt, emite access_token (JWT) + refresh_token
   • JWT payload: { sub, org_id, role, platform_roles, exp, type:"access" }
                ↓
4. Frontend guarda tokens en sessionStorage, redirige a /dashboard
                ↓
5. Dashboard llama GET /api/v1/dashboard/summary
   • Backend itera por apps activas, llama extractor por app
   • Agrega: ingresos_mes (suma), cartera (suma), alertas (conteo)
                ↓
6. Usuario navega a un módulo (ej: /memorial/contracts)
   • Angular Router → appAccessGuard verifica activación
   • Componente carga lista vía GET /api/v1/memorial/contracts
                ↓
7. Usuario crea contrato → POST /api/v1/memorial/contracts
   • Backend: ContractsService.create_contract()
   • Inserta MemorialExequialContract
   • Inserta MemorialExequialBeneficiary(s)
   • Calcula fee_amount según plan + frequency
   • Calcula next_payment_date
                ↓
8. Periódicamente, admin dispara batch:
   POST /api/v1/memorial/invoices/batch-generate-dues
   • Para cada contrato activo con next_payment_date <= hoy:
     - Crea MemorialInvoice (cuota)
     - Avanza next_payment_date al siguiente período
                ↓
9. Cliente paga → admin registra POST /api/v1/memorial/payments
   • PaymentsService aplica FIFO contra facturas pendientes
   • Crea MemorialPaymentInvoice (allocations)
   • Actualiza MemorialInvoice.balance/paid_amount/status
```

### 5.2 Flujo del cliente final (portal Memorial)

```
1. Titular abre app.savvytrix.com/memorial-portal
                ↓
2. Ingresa org_slug + (email o documento)
   POST /api/v1/memorial-portal/auth
   • Backend busca org por slug, contrato por (email | document)
   • Emite JWT scope:memorial_portal con contract_id + org_id, TTL 24h
                ↓
3. Frontend guarda token en sessionStorage como memorial_portal_token
   • Auth interceptor IGNORA URLs /memorial-portal/* (no inyecta admin JWT)
                ↓
4. Portal home consulta:
   GET /memorial-portal/me        → contrato + plan + beneficiarios
   GET /memorial-portal/invoices  → todas las cuotas
   GET /memorial-portal/payments  → historial de pagos
   GET /memorial-portal/services  → servicios funerarios prestados
                ↓
5. Usuario descarga PDF de factura:
   GET /memorial-portal/invoices/{id}/pdf
   • Backend valida que la factura pertenece al contract_id del JWT
   • Reutiliza render_invoice_pdf (xhtml2pdf + Jinja2)
```

### 5.3 Datos que se generan en cada flujo

| Acción | Datos generados |
|---|---|
| Crear contrato | 1 row en `memorial_exequial_contracts` + N en `memorial_exequial_beneficiaries` |
| Generar cuota mensual | 1 row en `memorial_invoices` (status=`pending`, balance=fee) |
| Registrar pago | 1 row en `memorial_payments` + 1-N en `memorial_payment_invoices` (allocations) + UPDATE en facturas |
| Cerrar servicio funerario | UPDATE `memorial_services.status='finalizado'` + N rows en `memorial_service_events` |
| Recalcular cartera | UPDATE en facturas vencidas (suma de mora compuesta a `late_interest`) |

---

## 6 · Escalabilidad

### 6.1 Lo que ya escala bien

- **Multi-tenancy por columna `organization_id`** + RLS: añadir un cliente es un INSERT en `organizations`, no aprovisionar infraestructura. Onboarding instantáneo.
- **Apps activables granularmente**: una org no paga ni carga código de apps que no usa (lazy loading frontend + filtrado por `organization_apps.status`).
- **Patrón uniforme por módulo** (`models / schemas / service / router`): cualquier dev nuevo entiende cualquier app en minutos.
- **Catálogos parametrizables** (`grading_systems`, `evaluation_templates`, `period_types`, `app_role_catalog`, etc.): cada org configura su propia lógica sin tocar código.
- **Trazabilidad explícita** (`source_app + source_ref_type + source_ref_id` en pagos, `reference_type + reference_id` en transacciones): permite reconstruir el origen de cualquier movimiento.
- **PostgreSQL 17 + RLS**: cuando los volúmenes crezcan, RLS bloquea fugas a nivel BD aunque haya bugs en el código.

### 6.2 Cuellos de botella técnicos previsibles

| Problema | Causa | Mitigación futura |
|---|---|---|
| **Latencia desde frontend** | Render us-west-2, clientes en Colombia → ~200ms por request | CDN + replicas o migración a São Paulo |
| **Single worker en Render** | Memoria limitada del tier starter (~512MB) | Subir tier; o partir por sub-dominio por app |
| **Paginación cliente** | Algunos endpoints traen 500+ rows y paginan en frontend | Endpoint con `limit/offset/total` real cuando supere 5k rows |
| **Falta de cache** | Toda lectura va a DB | Redis para catálogos estáticos (geo, business_type_catalog, app_registry) |
| **Generación batch síncrona** | `batch_generate_dues` corre en el request del admin | Worker async (Celery, RQ, o tasks de Supabase Functions) |
| **No hay search full-text** | LIKE `%query%` sobre nombres | pg_trgm o Elastic cuando crezca |
| **No hay event bus** | Apps no se enteran de cambios entre sí en tiempo real | Domain events + outbox pattern |
| **Migraciones manuales** | DDL aplicado vía scripts ad-hoc | Alembic + versionado por release |

### 6.3 Ventajas arquitectónicas actuales

1. **Monolito modular ≠ Monolito acoplado**: cada app vive en su carpeta, con su router, sin importar código de otras apps directamente. Refactor a microservicios es viable cuando aparezca la justificación.
2. **People-first**: hay una sola identidad de persona reutilizada por 6 apps, no 6 tablas duplicadas. Cuando llegue el momento de "vista 360 del cliente cross-app", está casi gratis.
3. **Finance-first**: hay un solo motor financiero. Cuando llegue auditoría externa o reporte fiscal consolidado, el dato ya está estructurado.
4. **RBAC granular declarativo**: `require_permission(app_code, *perms)` es composable y testable.
5. **Frontend lazy-loaded** por feature: el bundle inicial es < 540kB; cada app se carga solo si el usuario navega.

---

## 7 · Inteligencia artificial y automatización

### 7.1 Estado actual

**Cero IA en runtime**. El proyecto se ha construido con asistencia de IA (Claude, GPT) pero el producto no hace inferencia.

Existe sí una **disposición arquitectónica favorable** para incorporar agentes:

- `AI_STATE.md` mantiene el estado del proyecto digerible para LLMs.
- Logs de auditoría inmutables (`memorial_audit_log`, `platform_audit_log`) son input ideal de un agente analítico.
- Multi-app comparte `people` → un agente puede correlacionar comportamiento cross-app.

### 7.2 Oportunidades de IA / agentes (alta a mediana prioridad)

| Área | Caso de uso | Datos disponibles |
|---|---|---|
| **Cartera y cobranza** | Agente de cobranza que prioriza llamadas + propone mensajes WhatsApp por moroso | `memorial_invoices`, `water_invoices`, `condo_fees`, historial de pagos |
| **Insight financiero ejecutivo** | "Resumen del mes" generado por LLM sobre datos del dashboard | `dashboard.summary` ya tiene los KPIs |
| **Lead scoring CRM** | Modelo simple que predice probabilidad de cierre por lead | `crm_deals` + `crm_activities` + historial de won/lost |
| **Predicción de cancelación de contratos exequiales** | Detectar contratos en riesgo antes de que entren en mora | `memorial_invoices.status`, antigüedad, último pago |
| **Clasificación automática de PQRS** | LLM clasifica reclamos del portal water | `water_pqrs.body` |
| **Asistente del operador** | Chat dentro del back-office que ejecuta acciones via tool-calling | Todos los endpoints REST existentes |
| **Validación de notas pastorales/clínicas** | Detección de PII sensible antes de guardar | `church_pastoral_notes`, `health_clinical_*` |
| **Detección de duplicados de personas** | Match difuso entre `people` cross-app | `people` table (nombres, documentos) |
| **Generación de descripciones de servicios funerarios** | Texto del programa de honras fúnebres | `memorial_services`, `memorial_service_family` |

### 7.3 Contexto / memoria persistente útil para un agente

Si Savvy decide adoptar un agente con memoria persistente (vector store + memory store), lo que vale la pena guardar de forma estructurada es:

1. **Perfil de cada organización**: tamaño, apps activas, historia de uso, métricas clave.
2. **Historial de cobranza por afiliado**: cuántas mora, días promedio de atraso, respuesta a recordatorios.
3. **Patrones de uso por usuario**: qué módulos abre, qué reportes mira, qué horarios.
4. **Documentos generados** (facturas, contratos, certificados): full text indexado para consulta retroactiva.
5. **Decisiones de plataforma** (cambios de plan, suspensiones, activaciones de apps): bitácora para que el agente comercial entienda al cliente.
6. **Glosario por vertical**: cada vertical tiene su jerga (cuota exequial, ofrenda, matrícula, sesión de parqueo). Útil para que un LLM no se confunda al rephraseear.

### 7.4 Tipo de memoria recomendada

| Tipo | Implementación | Para qué |
|---|---|---|
| **Vector DB** (pgvector en Supabase) | Embeddings de notas pastorales, descripciones de servicios, PQRS | Búsqueda semántica |
| **Knowledge graph** | Nodos = personas/orgs/contratos/servicios; Edges = relaciones | Razonamiento sobre dependencias |
| **Memoria conversacional** | Tabla `agent_conversations` con turn_id | Continuidad entre sesiones |
| **Audit log estructurado** | Ya existe en `*_audit_log` | Reconstrucción de "qué pasó" |

---

## 8 · Relaciones y conocimiento estructurado

### 8.1 Por qué Savvy es naturalmente un grafo

Casi todas las entidades de Savvy se conectan en patrones que **no son árboles ni jerarquías estrictas** — son **grafos heterogéneos**. Ejemplo concreto:

```
Persona "María Pérez" (id=P-001)
   ├── es congregante en SavvyChurch     [church_congregants.person_id = P-001]
   ├── es estudiante en SavvyEdu         [edu_students.person_id = P-001]
   ├── es titular de contrato exequial   [memorial_exequial_contracts.titular_document_number = ...]
   ├── es beneficiaria de plan exequial  [memorial_exequial_beneficiaries.contract_id = ...]
   ├── es paciente en SavvyHealth        [health_patients.person_id = P-001]
   ├── pertenece a la familia "Pérez Castaño" [family_members]
   │     └── es cónyuge de "Jorge Castaño" [family_relationships]
   │           └── cuyo servicio funerario está vinculado al contrato exequial de María
   └── es prestataria en SavvyCredit     [credit_borrowers.person_id = P-001]
         └── tiene un préstamo activo con N pagos
```

Esto es **lo natural** del producto: la misma persona aparece en 6 apps distintas con relaciones cruzadas (familia → contrato → servicio → factura → pago).

### 8.2 Entidades-nodo principales

| Entidad | Tipo de nodo | Propiedades clave |
|---|---|---|
| `User` | identidad | email, platform_roles |
| `Organization` | tenant | slug, business_type, plan |
| `Person` | persona física | first_name, last_name, document |
| `App` | módulo activable | code, is_external |
| `Role` (per-app) | permiso agregado | code, permissions[] |
| `Plan` (subscription) | producto comercial | code, monthly_fee |
| `Contract` (memorial / credit) | acuerdo | code, start_date, status |
| `Invoice` | cobro | code, total, balance |
| `Payment` | recibo | code, amount, method |
| `Service` (memorial / health) | prestación | code, date, status |
| `Lead`, `Deal` | oportunidad comercial | source, status |
| `Employee` | recurso operativo | code, position, shift |
| `Vehicle`, `Room`, `Oven`, `Location` | activo físico | code, status |
| `Group`, `Scope` | jerarquía | parent_id |

### 8.3 Aristas / relaciones importantes

| Relación | Origen → Destino | Cardinalidad | Carga semántica |
|---|---|---|---|
| `is_titular_of` | Person → Contract | 1:N | dueño legal |
| `is_beneficiary_of` | Person → Contract | N:M | cubierto por plan |
| `paid` | Person → Invoice (via Payment) | N:M con monto | flujo financiero |
| `allocated_to` | Payment → Invoice | N:M con amount | FIFO o explícito |
| `belongs_to_family` | Person → FamilyUnit | N:1 | relación parental |
| `related_to` | Person → Person | N:M con tipo | spouse, parent, sibling |
| `member_of` | User → Organization | N:M con rol | tenancy |
| `has_app_role` | User → App (per Org) | N:M con role_code | RBAC |
| `originated_in` | Payment → SourceApp | N:1 con ref_id | trazabilidad |
| `triggered_event` | Action → AuditLog | 1:N | inmutabilidad |
| `provided_service` | Organization → Service | 1:N | prestación |
| `cover_for_service` | Contract → Service | 1:N | cuando el servicio se presta bajo cobertura |
| `attended_event` | Person → Event | N:M | asistencia |
| `enrolled_in` | Student → Course | N:M | matrícula |

### 8.4 Casos donde un knowledge graph / GraphRAG paga inmediato

1. **Vista 360 de la persona cross-app**: hoy requiere 6 queries SQL distintas + lógica en Python para correlacionar. En grafo es UNA traversal de profundidad 2.
2. **Análisis de fraude o duplicados**: detectar que la misma persona aparece con 2 documentos distintos en orgs diferentes — match difuso + grafo.
3. **Trazabilidad financiera**: "¿De dónde salió este pago?" cruza Payment → Invoice → Contract → Plan → Organization → SubscriptionPlan.
4. **Recomendación de planes**: "para un cliente con perfil X, ¿qué plan exequial conviene?" — basado en grafo de otros titulares similares + sus servicios prestados.
5. **Detección de patrones de cancelación**: ¿quién canceló qué app y cuándo, y qué tenían en común?
6. **Búsqueda contextual con RAG**: para que un LLM responda "muéstrame todas las facturas del beneficiario X del contrato Y de la funeraria Z" sin tener que escribir SQL.
7. **Razonamiento sobre permisos**: "¿Por qué este usuario puede ver este recurso?" recorre el grafo Auth → Membership → AppRole → Permission.

### 8.5 Trazabilidad y análisis de código

A nivel **código** (no de datos), Savvy también es un grafo:

- Cada `service.py` llama a `*Service` de otros módulos (delegación explícita): Church → People + Finance + Accounting.
- Los `app_role_catalog` referencian `app_permission_catalog`.
- Los routers usan `require_permission` que mira `app_user_roles → app_role_catalog`.

Un grafo del código permitiría preguntas como:
- "Si cambio el contrato de `PeopleService.create()`, ¿qué apps se ven afectadas?"
- "¿Qué endpoints requieren el permiso `church.finance.write`?"
- "¿Qué tablas se borran en cascada si elimino una organización?"

---

## 9 · Resultado final

### 9.1 Resumen ejecutivo

**Savvy es una plataforma SaaS multi-tenant modular** desarrollada por Savvitrix Solutions que unifica 12 verticales de negocio (iglesias, funerarias, acueductos, parqueaderos, clínicas, educación, comercio, etc.) sobre una **base común** de personas, organizaciones, finanzas, contabilidad y RBAC.

Arquitectónicamente es un **monolito modular** (FastAPI + SQLAlchemy async + PostgreSQL/Supabase) con frontend Angular standalone, deployado en **Render + Vercel + Supabase**. Cada vertical se activa por organización vía un `app_registry` y se cobra por suscripción.

Lo distintivo de Savvy frente a un ERP genérico es la **profundidad vertical** de cada app (ej: SavvyMemorial implementa el ciclo completo de una funeraria — contratos exequiales, cobranza, logística de salas y carrozas, traslados, inventario de cofres, RRHH, CRM, portal del afiliado, reportes y auditoría) **manteniendo el dominio común desacoplado** para que no haya duplicación.

### 9.2 Resumen técnico

| Dimensión | Valor |
|---|---|
| Líneas de código aproximadas | ~50.000 LoC (backend + frontend) |
| Tablas en producción | ~150 |
| Endpoints REST | ~400 |
| Apps verticales | 12 |
| Sub-módulos | 80+ |
| Vistas frontend | 100+ |
| Permisos definidos | 55+ |
| Roles del sistema | 50 |
| Organizaciones soportadas | ilimitadas (multi-tenant) |
| Patrón arquitectónico | Monolito modular API-first |
| Modelo de datos | Relacional con UUIDs + columna `organization_id` en todas las tablas scoped |
| Multi-tenancy | Schema compartido + RLS + filtrado obligatorio por org_id en service layer |
| Autenticación | JWT (access + refresh con family rotation) + 3 capas RBAC |
| Despliegue | Render (backend) + Vercel (frontend) + Supabase (DB) |
| Versión actual | 0.0.89 (frontend); backend sigue el ritmo |

### 9.3 Lista de entidades importantes del ecosistema

**Identidad / acceso:**
- `User`, `RefreshToken`, `PlatformRole`, `UserPlatformRole`

**Tenancy / comercial:**
- `Organization`, `Membership`, `Invitation`, `SubscriptionPlan`, `OrganizationSubscription`, `PlatformFeature`, `OrganizationFeatureOverride`

**RBAC granular:**
- `AppRegistry`, `OrganizationApp`, `AppUserRole`, `AppRoleCatalog`, `AppPermissionCatalog`

**Dominio compartido:**
- `Person`, `FamilyRelationship`, `EmergencyContact`
- `OrganizationalScope`, `GroupType`, `Group`, `GroupMember`, `ScopeLeader`
- `FinanceCategory`, `FinanceTransaction`, `FinancePaymentAccount`
- `ChartOfAccount`, `FiscalPeriod`, `JournalEntry`, `JournalEntryLine`
- `GeoCountry`, `GeoState`, `GeoCity`

**Memorial (el más completo y representativo):**
- `MemorialService`, `MemorialServiceFamily`, `MemorialServiceEvent`
- `MemorialExequialPlan`, `MemorialExequialContract`, `MemorialExequialBeneficiary`
- `MemorialInvoice`, `MemorialPayment`, `MemorialPaymentInvoice`
- `MemorialVehicle`, `MemorialDriver`, `MemorialRoom`, `MemorialOven`, `MemorialLocation`
- `MemorialTransfer`
- `MemorialInventoryItem`, `MemorialInventoryMovement`
- `MemorialPosition`, `MemorialEmployee`, `MemorialAttendance`
- `MemorialLead`, `MemorialLeadCommunication`
- `MemorialAuditLog`

**Otras apps verticales:** cada una mantiene su set de entidades análogo (ver sección 3.2).

### 9.4 Relaciones importantes entre componentes

```
User ──[has_platform_role]──▶ PlatformRole
User ──[is_member_of]──▶ Organization (with role)
User ──[has_app_role_in]──▶ App (scoped to org)
Organization ──[has_active]──▶ App
Organization ──[subscribed_to]──▶ SubscriptionPlan
Person ──[is_extended_as]──▶ Congregant | Student | Patient | Borrower | Employee
Person ──[is_related_to]──▶ Person (typed: spouse, parent, sibling, …)
Person ──[is_titular_of]──▶ ExequialContract
ExequialContract ──[covers]──▶ Beneficiary (Person)
ExequialContract ──[generates]──▶ Invoice (recurring)
Invoice ──[paid_by]──▶ Payment (N:M via PaymentInvoice with amount)
Payment ──[originated_in]──▶ App (via source_app + source_ref_id)
Service ──[uses]──▶ Vehicle | Room | Oven | Location | InventoryItem
Service ──[performed_by]──▶ Employee
Service ──[covered_by]──▶ ExequialContract (optional)
Lead ──[converts_to]──▶ ExequialContract | Service
LeadCommunication ──[belongs_to]──▶ Lead
AuditEntry ──[recorded]──▶ AnyAction (resource_type + resource_id)
```

### 9.5 Por qué Savvy podría beneficiarse de una base de datos de grafos como FalkorDB

#### 9.5.1 Diagnóstico

PostgreSQL hace bien lo que Savvy hace hoy: **lecturas/escrituras transaccionales sobre tablas con FKs claras**. Pero hay una clase de consultas que está creciendo y que **PostgreSQL paga caro**:

- "Dame TODO lo que tocó esta persona en TODAS las apps en los últimos 12 meses." → 6+ JOIN cross-table, lento y frágil.
- "Si la persona X está en mora en SavvyWater, ¿también lo está en SavvyMemorial?" → cross-org / cross-app, sin clave directa.
- "¿Qué patrón común tienen las orgs que se dieron de baja?" → traversal exploratoria, no predicado fijo.
- "¿Por qué este usuario tiene acceso a este recurso?" → camino User → Membership → AppRole → Permission, hoy resuelto a punta de queries imperativas.

#### 9.5.2 Por qué FalkorDB específicamente

| Razón | Cómo aplica a Savvy |
|---|---|
| **Cypher nativo y rápido** | Las consultas anteriores se escriben en 3-5 líneas Cypher; PostgreSQL las pide en 30+ líneas SQL con CTEs recursivos. |
| **Modelo property graph** | Encaja 1:1 con cómo modelamos hoy (nodos = entidades, aristas = FKs con propiedades). |
| **Performance en traversals profundos** | El caso "Persona en 6 apps" es un traversal de profundidad 2-3 — sweet spot de grafos. |
| **Sub-segundo en analytics ad-hoc** | El analista pregunta "¿cuántos clientes nuevos vinieron por referido y compraron en 90 días?" sin esperar al data engineer. |
| **Integración con LLMs (GraphRAG)** | Falkor publica APIs pensadas para alimentar agentes; Savvy puede ofrecer un asistente conversacional que razone sobre todo el ecosistema. |
| **Co-residente con Redis** | FalkorDB corre sobre Redis Stack → bajo costo operativo añadirlo al stack actual. |
| **Sincronización vía CDC** | Supabase emite cambios; un consumer puede mantener el grafo sincronizado sin reescribir el dato canónico. |

#### 9.5.3 Casos concretos de uso que justifican el grafo

1. **Vista 360 del cliente cross-app** — hoy imposible sin engineering; en Cypher es `MATCH (p:Person {document_number: $d})-[*1..2]-(x) RETURN x`.
2. **Recomendaciones de upsell** — "clientes parecidos a este compraron también..." resuelve con similarity over graph embeddings.
3. **Detección de fraude / duplicados** — mismo `document_number` en orgs distintas; mismo email con leves variaciones.
4. **Razonamiento de permisos explicable** — para un usuario, el grafo retorna el camino exacto que le da acceso (auditable).
5. **GraphRAG sobre el dominio** — un LLM con tool-calling que **traversa el grafo** en lugar de hacer SQL embedding-search puro.
6. **Análisis de churn / supervivencia** — qué organizaciones / qué planes generan más permanencia, traversando organizationsubscriptions ↔ apps ↔ activity.
7. **Pipeline comercial inteligente** — leads → deals → conversiones con scoring basado en grafo de clientes pasados.

#### 9.5.4 Cómo encajaría arquitectónicamente

```
                ┌─────────────────────────────┐
                │  PostgreSQL (Supabase)      │
                │  • OLTP, sistema de récord  │
                │  • RLS, multi-tenancy       │
                └────────────┬────────────────┘
                             │ CDC / triggers
                             ▼
                ┌─────────────────────────────┐
                │  FalkorDB (Redis Stack)     │
                │  • Property graph derived   │
                │  • Solo lectura analítica   │
                └────────────┬────────────────┘
                             │ Cypher API
                             ▼
                ┌─────────────────────────────┐
                │  Agente IA / Dashboard      │
                │  • GraphRAG                 │
                │  • Reportes ad-hoc          │
                │  • Vista 360                │
                └─────────────────────────────┘
```

**PostgreSQL sigue siendo la fuente de verdad**. FalkorDB es una **proyección de lectura** especializada en relaciones, alimentada por eventos de cambio. Esto evita el clásico "elegir entre los dos" — se complementan.

#### 9.5.5 Riesgos / cuándo NO sería buena idea

- Si los volúmenes siguen pequeños (< 1M filas totales), el costo operativo de mantener un segundo motor de datos no compensa.
- Si el equipo no tiene experiencia con Cypher, hay curva.
- Si las consultas siguen siendo CRUD planas, el ROI es bajo.

Savvy ya **rebasa esos umbrales** en al menos tres dimensiones: tiene un dominio cross-app rico, tiene aspiraciones de IA conversacional, y tiene una superficie creciente de relaciones implícitas (persona en 6 apps, pagos con `source_app`, RBAC en 3 capas).

---

## Anexo A · Convenciones de desarrollo

- **Version bump**: cada commit sube `frontend/package.json` patch version.
- **Commit + push**: `git push` inmediatamente después de cada commit.
- **Backend pattern**: `models.py → schemas.py → service.py → router.py` (services son stateless con `staticmethod`).
- **Frontend pattern**: standalone components con `inject()`, signals para estado local, lazy-loaded routes.
- **Multi-tenancy obligatoria**: filtrado por `org_id` en service layer; nunca confiar solo en RLS.
- **Person-first**: estudiantes, congregantes, prestatarios extienden `people` vía `person_id`.
- **Finance delegation**: ninguna app crea sistema financiero propio — todas escriben a `finance_transactions` o `pay_transactions`.
- **Config-driven**: nada de hardcodear políticas institucionales (grading scales, attendance policies, payment frequencies).

---

## Anexo B · Glosario

| Término | Significado |
|---|---|
| **Org** | Organization — el tenant (una empresa cliente de Savvy). |
| **App** | Vertical activable (church, memorial, water, …). |
| **Module** | Compartido reutilizable (auth, people, finance, …). |
| **OrgMixin** | SQLAlchemy mixin que agrega `organization_id` + index a una tabla. |
| **BaseMixin** | Mixin con `id` UUID + `created_at` + `updated_at`. |
| **Platform** | El nivel Savvitrix Solutions (sobre todas las orgs). |
| **Super admin** | Usuario con `platform_roles ∋ 'super_admin'` — sin org propia. |
| **Owner** | `membership.role='owner'` — dueño de UNA org, bypass RBAC per-app. |
| **Source_app** | Columna trazabilidad: qué app originó un pago/transacción. |
| **Scope** | Unidad de jerarquía organizacional (ej: parroquia → diócesis). |
| **Mora compuesta idempotente** | Algoritmo de cartera: `base × rate × meses_vencidos`. Se puede correr N veces sin duplicar. |

---

*Fin del análisis. Documento mantenido en `docs/analysis/savvy-ecosystem-analysis.md` — actualizar al cambiar arquitectura mayor.*
