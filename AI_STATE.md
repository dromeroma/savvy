# AI_STATE.md — Estado del Proyecto Savvy

> Ultima actualizacion: 2026-04-13 (v0.0.44)

## Resumen

Savvy es una plataforma SaaS multi-tenant modular desarrollada por **Savvitrix Solutions**. El backend es un monolito modular en FastAPI, el frontend es Angular standalone con Tailwind CSS v4, y la base de datos es PostgreSQL vía Supabase.

**Version actual del frontend**: 0.0.44
**Git remote**: `git@github-dromeroma:dromeroma/savvy.git`
**Branch principal**: `main`

---

## Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| Backend | Python 3.12+ / FastAPI / SQLAlchemy 2.0 async / Pydantic v2 |
| Frontend | Angular 20 standalone / TypeScript 5.9 / Tailwind CSS v4 |
| Base de datos | PostgreSQL 17 via Supabase (PgBouncer, RLS habilitado) |
| Auth | JWT (access + refresh tokens con family rotation) |
| Deploy | Vercel (frontend) + Render (backend) + Supabase (DB) |
| Visualizacion | D3.js (genograma familiar) |
| Date picker | flatpickr con locale español |

---

## Arquitectura Backend

```
backend/src/
├── main.py                    # FastAPI app factory
├── gateway/router.py          # Central router: /api/v1/*
├── core/                      # Config, DB, security, middleware, exceptions
│   ├── config.py              # Pydantic Settings (SAVVY_ prefix)
│   ├── database.py            # AsyncSession factory, Base
│   ├── security.py            # JWT, password hashing
│   ├── dependencies.py        # get_db, get_org_id, get_current_user, require_role
│   ├── exceptions.py          # SavvyException hierarchy
│   ├── models/base.py         # BaseMixin (id, timestamps), OrgMixin (organization_id)
│   └── middleware/             # TenantMiddleware, LoggingMiddleware
├── modules/                   # Shared reusable modules
│   ├── auth/                  # Users, RefreshTokens, register/login/refresh (+ platform_roles in JWT)
│   ├── organization/          # Organizations, Memberships, Invitations
│   ├── platform/              # v0.0.41 — Savvy Platform super-admin panel
│   │                          # PlatformRole, UserPlatformRole, SubscriptionPlan, PlatformFeature,
│   │                          # PlanFeature, OrganizationSubscription, OrganizationFeatureOverride,
│   │                          # PlatformAuditLog, AppRoleCatalog (v0.0.42) —
│   │                          # 39 endpoints under /api/v1/platform/* (+10 for apps/members/roles)
│   ├── people/                # Person, FamilyRelationship, EmergencyContact
│   ├── groups/                # OrganizationalScope, GroupType, Group, GroupMember
│   ├── finance/               # FinanceCategory, FinanceTransaction, PaymentAccount
│   ├── accounting/            # ChartOfAccounts, FiscalPeriod, JournalEntry, AccountingEngine
│   ├── apps/                  # AppRegistry, OrganizationApp, AppUserRole
│   └── geography/             # GeoCountry, GeoState, GeoCity
└── apps/                      # Vertical business apps
    ├── church/                # SavvyChurch v2 (11 sub-modules, 16 church tables)
    ├── edu/                   # SavvyEdu (11 sub-modules)
    ├── family/                # SavvyFamily (1 module, 4 tables)
    ├── credit/                # SavvyCredit (7 sub-modules, 11 tables)
    ├── crm/                   # SavvyCRM (6 sub-modules, 9 tables)
    ├── parking/                # SavvyParking (6 sub-modules, 10 tables)
    ├── condo/                 # SavvyCondo (8 sub-modules, 11 tables)
    ├── health/                # SavvyHealth (6 sub-modules, 12 tables)
    ├── pay/                   # SavvyPay (7 sub-modules, 11 tables) — FINANCIAL BACKBONE
    └── pos/                   # SavvyPOS cloud (6 sub-modules, 11 tables) + SavvyPOS LocalFirst (external, code=pos_local)
```

### Patron de cada modulo/app

```
module_name/
├── __init__.py
├── models.py      # SQLAlchemy ORM models (BaseMixin + OrgMixin + Base)
├── schemas.py     # Pydantic v2 request/response schemas
├── service.py     # Stateless business logic (static methods)
└── router.py      # FastAPI endpoints (Depends get_db, get_org_id)
```

---

## Arquitectura Frontend

```
frontend/src/app/
├── shell/                     # Layout, auth, dashboard, settings
│   ├── auth/                  # Login, register
│   ├── layout/                # Main layout with sidebar
│   ├── dashboard/             # App launcher + catalog + coming soon
│   └── settings/              # Organization settings
├── platform/                  # NEW v0.0.41 — Super admin panel (rojo)
│   ├── layout/                # platform-layout (sidebar distinto, badge Super Admin)
│   ├── dashboard/             # KPIs globales: MRR, orgs totales, churn, etc.
│   ├── organizations/         # list + detail (tabs General/Subscription) + create
│   ├── plans/                 # catálogo de planes con edición de precios
│   ├── subscriptions/         # listado global con filtros + activar/suspender
│   ├── users/                 # todos los users + grant/revoke platform role
│   └── audit/                 # bitácora inmutable con filtros
├── core/                      # Singleton services, guards, interceptors
│   ├── services/              # AuthService (+isSuperAdmin/getPlatformRoles), ApiService (+put), AppsService
│   ├── guards/                # authGuard, appAccessGuard, superAdminGuard (NEW)
│   ├── interceptors/          # Auth interceptor (Bearer + refresh)
│   └── models/                # app.model, user.model
├── shared/                    # Reusable components and services
│   ├── components/
│   │   ├── sidebar/           # Dynamic sidebar (reactive via apps$ BehaviorSubject)
│   │   ├── ui/                # alert, confirm-dialog, modal
│   │   ├── form/              # date-picker (flatpickr), location-selector
│   │   ├── common/            # theme-toggle
│   │   └── notifications/     # Toast notifications
│   └── services/              # NotificationService, ThemeService, SidebarService
└── apps/                      # Vertical app modules (lazy-loaded)
    ├── church/                # 10 views
    ├── accounting/            # 5 views
    ├── edu/                   # 12 views
    └── family/                # 4 views + D3.js genogram
```

### Patrones clave

- **Standalone components** (no NgModules)
- **Signals** para estado local de componentes
- **RxJS BehaviorSubject** para estado compartido (apps$, sidebar)
- **Lazy loading** via `loadChildren` / `loadComponent` en rutas
- **appAccessGuard** verifica que la org tiene la app activada
- **APP_MENUS** en sidebar.component.ts define submenus por app code

---

## Apps Implementadas

### SavvyChurch v2 (code: `church`)
- **Tablas v1**: church_congregants, church_events (+ event_category, scope_id), church_attendance, church_visitors
- **Tablas v2 nuevas (12)**: church_member_lifecycle, church_transfers, church_pastoral_notes, church_doctrine_groups, church_doctrine_enrollments, church_doctrine_attendance, church_aggregate_offerings, church_aid_programs, church_aid_beneficiaries, church_aid_distributions, church_rotations, church_rotation_assignments
- **Backend**: src/apps/church/ — 11 sub-modulos (congregants, events, attendance, visitors, finance + aggregate_offerings, reports, dashboard v2 con analytics multi-scope, pastoral, doctrine, social_aid, rotations)
- **Frontend**: 12 vistas — (dashboard, congregantes, visitantes, grupos, eventos, asistencia, doctrina, rotaciones, ayuda social, finanzas, ofrendas agregadas, reportes)
- **RBAC contextual**: reutiliza `scope_leaders` (shared/groups) en vez de tabla propia
- **Arbol familiar**: reutiliza `family_relationships` + nuevo FK `church_congregants.family_head_person_id`
- **Jerarquia**: reutiliza `organizational_scopes` (recursive CTE en dashboard analytics)
- **Ofrendas agregadas**: `church_aggregate_offerings` espejada automaticamente en `finance_transactions` via `reference_type='church_aggregate_offering'`
- **Migracion**: `church_v2_hierarchical_extensions` (2026-04-12)
- **Delega a**: PeopleService, GroupService, FinanceService, AccountingEngine

### SavvyEdu (code: `edu`)
- **Tablas (24)**: edu_grading_systems, edu_grade_scales, edu_academic_period_types, edu_evaluation_templates, edu_academic_periods, edu_programs, edu_courses, edu_prerequisites, edu_curriculum_versions, edu_students, edu_guardians, edu_teachers, edu_sections, edu_enrollments, edu_waitlists, edu_rooms, edu_schedules, edu_attendance, edu_evaluations, edu_grades, edu_final_grades, edu_tuition_plans, edu_student_charges, edu_scholarships, edu_scholarship_awards, edu_document_templates, edu_issued_documents
- **Backend**: src/apps/edu/ (config, structure, students, teachers, enrollment, scheduling, attendance, grading, finance, documents)
- **Frontend**: 12 vistas (dashboard, config, programas, cursos, estudiantes, docentes, secciones, horarios, asistencia, calificaciones, finanzas, documentos)
- **GradingEngine**: Calcula notas finales ponderadas con conversion a escala del grading system
- **SchedulingService**: Deteccion de conflictos de salon y docente

### SavvyFamily (code: `family`)
- **Tablas (4)**: family_units, family_members, family_relationship_meta, family_annotations
- **Backend**: src/apps/family/ (models, schemas, service, router)
- **Frontend**: 4 vistas (dashboard, familias, detalle, genograma D3.js)
- **Genograma**: SVG con D3.js, simbologia clinica estandar (cuadrado=hombre, circulo=mujer, X=fallecido, lineas de matrimonio/divorcio, marcadores de anotacion)
- **19 categorias de anotacion**: substance_abuse, mental_health, physical_illness, violence, etc.
- **Multi-app**: source_app permite que anotaciones vengan de church, health, edu

### SavvyCredit (code: `credit`)
- **Tablas (11)**: credit_products, credit_product_fees, credit_borrowers, credit_guarantors, credit_applications, credit_loans, credit_amortization, credit_disbursements, credit_payments, credit_penalties, credit_restructurings
- **Backend**: src/apps/credit/ (products, borrowers, applications, loans, payments, restructuring, dashboard)
- **CreditEngine**: Motor de calculo financiero con 4 metodos de amortizacion (french, german, flat, bullet), conversion de tasas entre periodos, asignacion de pagos configurable (interest_first, principal_first, proportional)
- **Frontend**: 8 vistas (dashboard KPIs, productos crediticios, prestatarios, solicitudes con aprobacion, prestamos con tabla amortizacion, detalle de prestamo, pagos, registro de pagos)
- **Config-driven**: Cada producto define su propio interest_type, amortization_method, payment_frequency, late_fee, grace_period, payment_allocation
- **Loan lifecycle**: pending -> active -> current/delinquent -> paid_off/written_off/restructured
- **Delega a**: PeopleService (borrowers), FinanceService + AccountingEngine (futuro)

### SavvyAccounting (modulo compartido, code: `accounting`)
- **Tablas**: chart_of_accounts, fiscal_periods, journal_entries, journal_entry_lines
- **AccountingEngine**: Plan de cuentas jerarquico, asientos doble partida, periodos fiscales, reportes (estado de resultados, balance general)
- **Frontend**: 5 vistas (catalogo cuentas, asientos, periodos, estado resultados, balance general)

---

## Apps en Dashboard "Proximamente"



---

## Modulos Compartidos (backend)

| Modulo | Tablas clave | Consumido por |
|--------|-------------|---------------|
| auth | users, refresh_tokens | Todos |
| organization | organizations, memberships, invitations | Todos |
| people | people, family_relationships, emergency_contacts | Church, Edu, Family, Credit, CRM |
| groups | organizational_scopes, group_types, groups, group_members, scope_leaders | Church, Edu |
| finance | finance_categories, finance_transactions, finance_payment_accounts | Church, Edu, Credit |
| accounting | chart_of_accounts, fiscal_periods, journal_entries, journal_entry_lines | Finance -> todos |
| apps | app_registry, organization_apps, app_user_roles | Dashboard, sidebar, guards |
| geography | geo_countries, geo_states, geo_cities | People |

---

## Base de Datos (Supabase)

- **Proyecto**: Savvy (cdvwtgfyetonidjfwflt, us-west-2)
- **Total de tablas**: ~60+
- **RLS**: Habilitado en todas las tablas de apps
- **Multi-tenancy**: Via organization_id (OrgMixin) en todas las tablas scoped
- **IDs**: UUID (gen_random_uuid)
- **Timestamps**: created_at + updated_at con timezone

---

## UI / UX

- **Color primario**: Emerald green (#059669 = brand-500)
- **Temas**: Light + Dark (CSS custom properties via ThemeService)
- **Scrollbars**: Brand-colored (scrollbar-brand utility)
- **Select hover**: Brand-colored option hover
- **Date picker**: flatpickr con locale español (DatePickerComponent compartido)
- **Notificaciones**: Toast con sonido (Web Audio API via SoundManagerService)
- **Font**: System UI stack

---

## Documentacion

```
docs/
├── README.md                          # Indice principal
├── architecture/                      # overview, multi-tenancy, scalability, tech-stack, ecosystem-design, migration-strategy
├── modules/
│   ├── auth/README.md
│   ├── organization/README.md
│   ├── gateway/README.md
│   ├── people/README.md
│   ├── groups/README.md
│   ├── finance/README.md
│   └── accounting/README.md
├── database/                          # schema.md, conventions.md
├── api/                               # README.md, auth-endpoints.md, organization-endpoints.md
├── apps/
│   ├── README.md                      # Guia de apps + lista de apps implementadas/planeadas
│   ├── _template/README.md
│   ├── church/README.md
│   ├── edu/README.md
│   └── family/README.md
└── guides/                            # adding-a-module.md, adding-an-app.md
```

---

## Convenciones de Desarrollo

- **Version bump**: Cada commit sube la version patch del frontend (package.json)
- **Commit + push**: Siempre push inmediato despues de cada commit
- **Backend pattern**: models.py -> schemas.py -> service.py -> router.py (stateless, static methods)
- **Frontend pattern**: Standalone component con inline template, signals, inject()
- **Multi-tenancy**: Siempre filtrar por org_id en service layer
- **Person-first**: Students, teachers, congregants extienden people via person_id
- **Finance delegation**: Apps no crean sistema financiero propio, usan SavvyFinance + AccountingEngine
- **Config-driven**: No hardcodear logica institucional (grading, evaluation, attendance policies)

---

## Bugs Conocidos / Deuda Tecnica

- ChurchLayoutComponent importa RouterLink y RouterLinkActive sin usarlos (warning Angular)
- flatpickr no es ESM (warning en build, no-fatal)
- CSS selector warnings (empty sub-selector, no-fatal)
- SavvyChurch docs describe tablas church_classes y church_class_enrollments que no estan implementadas en codigo (solo en la doc original) — v2 introduce church_doctrine_* como el reemplazo funcional

---

## Historial de Versiones Recientes

| Version | Descripcion |
|---------|-------------|
| 0.0.44 | **Permission enforcement (Phase 1 — POS + Church)**: system roles in `app_role_catalog` are now seeded with default permission sets (pos owner/store_manager/cashier/inventory/viewer; church owner/pastor/treasurer/teacher/leader/member; plus the other 9 apps with sensible defaults). New `src/modules/apps/permissions.py` exposes `require_permission(app_code, *perms)` — a FastAPI dependency factory that: (1) bypasses for `super_admin` platform role, (2) bypasses for org-level `membership.role == 'owner'`, (3) bypasses for app-level role catalog entry `code == 'owner'`, (4) otherwise looks up `app_user_roles` + `app_role_catalog` (system OR org-scoped custom) and grants access if ANY of the required permissions are present. Permissions are request-cached on `request.state._perm_cache`. Retrofit applied to every SavvyPOS router (sales, inventory, catalog, registers, config) and every SavvyChurch router (11 sub-routers — dashboard, congregants, events, attendance, visitors, finance, pastoral, doctrine, social_aid, rotations, reports). Also added `social_aid.manage` and `rotations.manage` to the church permission catalog and seeded them into the matching system roles. Phases 2+ will cover the other 9 apps (accounting, edu, family, credit, crm, parking, condo, health, pay) one at a time. |
| 0.0.43 | **Platform v3 — custom roles + permissions + self-service settings**: extended `app_role_catalog` with `organization_id` (nullable = system, non-null = org-custom), `permissions` JSONB, `created_by`, `updated_at`; new `app_permission_catalog` table seeded with 55 permissions across the 11 apps (church: members.read/write, finance.read/write, events.manage, doctrine.manage, pastoral.notes, etc.; pos: sales.create/void, inventory.read/write, products.manage, cash.open_close, discounts.apply; accounting, edu, family, credit, crm, parking, condo, health, pay — all with a baseline permission set). Backend: +9 platform endpoints — `/platform/users/{id}/reset-password`, `/platform/features/{id}` PATCH/DELETE, `/platform/dashboard/timeseries`, `/platform/apps/{code}/permissions`, `/platform/organizations/{id}/custom-roles` CRUD (GET/POST/PATCH/DELETE). `assign_app_role` now accepts custom roles scoped to the same org. Catalog validation prevents unknown permissions from being saved. Frontend: settings page redesigned with 3 tabs — **Organización** (existing), **Mi cuenta** (change password with current → new + confirm), **Roles personalizados** (list + create/edit custom roles per app with permission checkboxes grouped by category). Platform: users list now has "Reset pwd" button with auto-generated 12-char password, dashboard shows 12-month time-series SVG chart (bars = new orgs, line = new users), new `/platform/features` CRUD page with grouped table + modal editor, org-detail gains "Roles personalizados" tab mirroring settings UI. Total platform routes: 39 → 48. |
| 0.0.42 | **Platform v2 — org parametrization**: new `app_role_catalog` table seeded with 50 roles across 11 apps (church: pastor/treasurer/teacher/leader/member; pos: store_manager/cashier/inventory/viewer; accounting: accountant/auditor/assistant; edu, family, credit, crm, parking, condo, health, pay). Backend: 10 new `/platform/*` endpoints for listing apps, role catalog per app, activating/deactivating apps for an org, listing org members with their per-app roles, inviting new users into an org with a starting password, removing members, and assigning/revoking app roles with catalog validation. Frontend: organization-detail now has 3 new tabs — **Apps** (toggle activation per app), **Usuarios & roles** (list + invite + remove + assign per-app roles via catalog dropdown), **Features** (per-org overrides forced ON/OFF with reason). All actions write to `platform_audit_log`. |
| 0.0.41 | **Savvy Platform super admin**: platform_roles (RBAC over orgs) + plans (starter/pro/enterprise + platform) + subscriptions + features + overrides + audit log. Nuevo modulo backend `src/modules/platform/` con 29 endpoints bajo `/api/v1/platform/*`, guard `require_super_admin` + JWT claim `platform_roles`. Nueva area frontend `src/app/platform/` con layout propio, 7 vistas (dashboard, organizations list/detail/create, plans, subscriptions, users, audit), `superAdminGuard` + redirect al login si super_admin. Rename `Iglesia XYZ` → `Savvytrix` (type=`platform`), sin apps activadas. Nueva org de pruebas `Empresa Demo` (demo@savvytrix.local) con Starter trial 14d. El super_admin NO puede entrar a organizaciones — parametriza todo desde su propio panel. |
| 0.0.40 | **SavvyChurch v2**: 12 tablas nuevas para pastoral/doctrine/social_aid/rotations + aggregate_offerings + analytics multi-scope con recursive CTE. 4 nuevas vistas frontend. |
| 0.0.39 | SavvyPOS cloud completo |
| 0.0.38 | SavvyHealth completo: 12 tablas, 7 vistas, EHR SOAP, citas, diagnosticos, prescripciones, lab |
| 0.0.35 | SavvyCondo completo: 11 tablas, 9 vistas, gobernanza digital, cuotas por coeficiente |
| 0.0.34 | SavvyParking completo: PricingEngine, sesiones entry/exit, 10 tablas, 7 vistas + docs Credit/CRM/Parking |
| 0.0.33 | SavvyCRM completo: pipelines, deals, leads, contacts, companies, activities, 9 tablas |
| 0.0.32 | SavvyCredit completo: CreditEngine, 4 metodos amortizacion, 11 tablas, 8 vistas |
| 0.0.31 | Fix sidebar reactivo (BehaviorSubject) + AI_STATE.md |
| 0.0.30 | Documentacion sincronizada: SavvyAccounting, SavvyEdu, SavvyFamily + indices |
| 0.0.29 | SavvyFamily completo: familiograma D3.js, anotaciones clinicas, genograma |
| 0.0.28 | SavvyEdu completo: 11 modulos, 24 tablas, GradingEngine, config-driven |
| 0.0.27 | Scrollbars brand-colored + select option styling |
| 0.0.26 | Replace native date inputs with DatePickerComponent (flatpickr) |
| 0.0.25 | Fix horizontal scroll income statement |
| 0.0.24 | Fix balance sheet field name mismatch |
