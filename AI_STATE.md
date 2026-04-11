# AI_STATE.md — Estado del Proyecto Savvy

> Ultima actualizacion: 2026-04-11

## Resumen

Savvy es una plataforma SaaS multi-tenant modular desarrollada por **Savvitrix Solutions**. El backend es un monolito modular en FastAPI, el frontend es Angular standalone con Tailwind CSS v4, y la base de datos es PostgreSQL vía Supabase.

**Version actual del frontend**: 0.0.30
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
│   ├── auth/                  # Users, RefreshTokens, register/login/refresh
│   ├── organization/          # Organizations, Memberships, Invitations
│   ├── people/                # Person, FamilyRelationship, EmergencyContact
│   ├── groups/                # OrganizationalScope, GroupType, Group, GroupMember
│   ├── finance/               # FinanceCategory, FinanceTransaction, PaymentAccount
│   ├── accounting/            # ChartOfAccounts, FiscalPeriod, JournalEntry, AccountingEngine
│   ├── apps/                  # AppRegistry, OrganizationApp, AppUserRole
│   └── geography/             # GeoCountry, GeoState, GeoCity
└── apps/                      # Vertical business apps
    ├── church/                # SavvyChurch (7 sub-modules)
    ├── edu/                   # SavvyEdu (11 sub-modules)
    └── family/                # SavvyFamily (1 module, 4 tables)
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
├── core/                      # Singleton services, guards, interceptors
│   ├── services/              # AuthService, ApiService, AppsService, SoundManager
│   ├── guards/                # authGuard, appAccessGuard
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

### SavvyChurch (code: `church`)
- **Tablas**: church_congregants, church_events, church_attendance, church_visitors
- **Backend**: src/apps/church/ (congregants, events, attendance, visitors, finance, reports, dashboard)
- **Frontend**: 10 vistas (dashboard, congregantes, visitantes, grupos, eventos, asistencia, finanzas, reportes)
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

### SavvyAccounting (modulo compartido, code: `accounting`)
- **Tablas**: chart_of_accounts, fiscal_periods, journal_entries, journal_entry_lines
- **AccountingEngine**: Plan de cuentas jerarquico, asientos doble partida, periodos fiscales, reportes (estado de resultados, balance general)
- **Frontend**: 5 vistas (catalogo cuentas, asientos, periodos, estado resultados, balance general)

---

## Apps en Dashboard "Proximamente"

SavvyHealth, SavvyCondo, SavvyParking, SavvyCRM, SavvyCredit

---

## Modulos Compartidos (backend)

| Modulo | Tablas clave | Consumido por |
|--------|-------------|---------------|
| auth | users, refresh_tokens | Todos |
| organization | organizations, memberships, invitations | Todos |
| people | people, family_relationships, emergency_contacts | Church, Edu, Family |
| groups | organizational_scopes, group_types, groups, group_members, scope_leaders | Church, Edu |
| finance | finance_categories, finance_transactions, finance_payment_accounts | Church, Edu |
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
- SavvyChurch docs describe tablas church_classes y church_class_enrollments que no estan implementadas en codigo (solo en la doc original)

---

## Historial de Versiones Recientes

| Version | Descripcion |
|---------|-------------|
| 0.0.30 | Documentacion sincronizada: SavvyAccounting, SavvyEdu, SavvyFamily + indices |
| 0.0.29 | SavvyFamily completo: familiograma D3.js, anotaciones clinicas, genograma |
| 0.0.28 | SavvyEdu completo: 11 modulos, 24 tablas, GradingEngine, config-driven |
| 0.0.27 | Scrollbars brand-colored + select option styling |
| 0.0.26 | Replace native date inputs with DatePickerComponent (flatpickr) |
| 0.0.25 | Fix horizontal scroll income statement |
| 0.0.24 | Fix balance sheet field name mismatch |
