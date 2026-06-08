# Savvy — Resumen completo para revisión externa

> Documento autocontenido para que otra IA lo lea "en frío" y proponga mejoras.
> Fecha: 2026-06-08 · Versión frontend: 0.1.5.
> Al final hay una lista de **preguntas concretas** para el revisor.

---

## 1. Qué es Savvy

**Savvy** (internamente *SavvyCore*) es una **plataforma SaaS multi-tenant
modular** de la empresa colombiana **Savvitrix Solutions**. No es un producto
único: es un **ecosistema de 13 aplicaciones verticales** que comparten una sola
infraestructura, base de datos, autenticación, RBAC, dominio común (personas,
organizaciones, contabilidad) y un panel de super-admin de plataforma.

Una organización (tenant) activa las apps que necesita. Mercado objetivo: pymes
de LATAM (Colombia primero).

**Escala actual del código:** 233 tablas en PostgreSQL, ~797 rutas REST,
13 apps verticales + 8 módulos compartidos + 2 módulos de IA.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 async · Pydantic v2 · asyncpg |
| Frontend | Angular 20 (standalone components, signals) · TypeScript 5.9 · Tailwind CSS v4 |
| Base de datos | PostgreSQL 17 vía **Supabase** (PgBouncer/transaction pooling, RLS) |
| Auth | JWT (access + refresh con rotación de familia); claims de roles de plataforma |
| Deploy | Vercel (frontend, app.savvytrix.com) · Render (backend) · Supabase (DB) |
| IA | Claude (Anthropic) vía API REST con httpx; pgvector disponible en Supabase |
| PDF | Jinja2 + xhtml2pdf · Voz: Web Speech API del navegador |

**Patrón de módulo backend:** `models.py` → `schemas.py` → `service.py` →
`router.py`. DDL aplicado con scripts idempotentes (`setup_*.py`), no migraciones
Alembic. Mixins `BaseMixin` (id, timestamps) y `OrgMixin` (organization_id).

**Multi-tenant:** cada tabla de negocio lleva `organization_id`; aislamiento por
RLS + dependencia `get_org_id`. Multi-país vía `country_code`/settings JSONB.

---

## 3. Las 13 apps verticales (tablas entre paréntesis)

| App | Qué hace |
|-----|----------|
| **SavvyEdu** (27) | Gestión educativa: estudiantes, matrículas, notas, etc. |
| **SavvyMemorial** (24) | Funeraria: servicios exequiales, planes, contratos, afiliados, facturación, cartera, CRM de leads, inventario, logística, vehículos, portal del cliente |
| **SavvyHR** (22) | Talento humano: empleados, contratos, asistencia, turnos, vacaciones, incapacidades, nómina (motor de fórmulas), liquidaciones (con PDF), evaluaciones 360°, capacitaciones, portal del empleado |
| **SavvyChurch** (19) | Gestión de iglesias: miembros, grupos, ciclo de vida, etc. |
| **SavvyWater** (15) | Acueductos comunales: suscriptores, lecturas, facturación, pagos, PQRs, portal cliente |
| **SavvyHealth** (12) | Salud / consultorios |
| **SavvyCredit** (11) | Créditos y cobranzas |
| **SavvyCondo** (11) | Administración de propiedad horizontal |
| **SavvyPay** (11) | Pagos / pasarela |
| **SavvyPOS** (11) | Punto de venta: catálogo, inventario, ventas, cajas, sucursales |
| **SavvyParking** (10) | Parqueaderos: sesiones, tarifas, vehículos, servicios (lavado) |
| **SavvyCRM** (9) | CRM general |
| **SavvyFamily** (5) | Genograma familiar (visualización D3.js) |

**Madurez dispar:** Memorial y HR son los más completos y con datos demo ricos
(Funeraria San Rafael: 8 empleados, ~?? contratos exequiales con cartera real).
POS está construido pero **sin datos** todavía. Otros varían.

---

## 4. Módulos compartidos

- **auth** — usuarios, login/refresh, roles de plataforma en el JWT
- **organization** — organizaciones, membresías, invitaciones
- **platform** — panel super-admin (Savvitrix): planes, suscripciones, features,
  overrides por org, catálogo de roles/permisos por app, auditoría
- **people** — Person, relaciones familiares, contactos de emergencia (identidad
  cross-app)
- **groups** — ámbitos organizacionales, tipos de grupo, miembros
- **finance** — categorías, transacciones, cuentas de pago
- **accounting** — plan de cuentas, períodos fiscales, asientos, motor contable
- **apps** — registro de apps, apps por organización, roles por usuario por app
- **geography** — países, estados, ciudades

---

## 5. SavvyAI — la capa de IA ("AI Operating System")

Trabajo reciente y grande: convertir Savvy de "ERP de formularios" a un
ecosistema inteligente. Principio rector: **Zero-Form** (el formulario es el
último recurso). Construido en 5 fases. Módulos `modules/savvy_ai/` (6 tablas) y
`modules/savvy_flow/` (4 tablas).

**Decisión arquitectónica clave:** UNA capa horizontal compartida por las 13
apps, no IA pegada por app. La API key de Claude se configura desde el panel del
super-admin (**cifrada con Fernet**, clave derivada del JWT secret), nunca en `.env`.

**Se mide TODO desde el día uno** (tabla `ai_usage`): por organización, usuario,
módulo (app_code), acción, prompt y modelo, con tokens + costo USD. Es la base
del modelo de negocio (vender IA como add-on premium medido).

### Capacidades

| Capacidad | Qué hace | Estado |
|-----------|----------|--------|
| **SavvyScan** | Sube factura/imagen → Claude Vision extrae datos estructurados → tarjeta "Confirmable Action" → al confirmar actualiza inventario POS | 🧪 requiere API key |
| **Savvy Command (⌘K)** | Barra global: navegación, búsqueda universal, chat, dictado por voz, drag de archivo | ✅ navegación/voz/búsqueda funcionan |
| **Savvy Graph / Búsqueda universal** | Encuentra una persona en TODOS los módulos (HR + Memorial + Water + leads) por nombre/documento, insensible a acentos (`unaccent`); agrupa por documento → persona unificada | ✅ funciona sin IA |
| **SavvyCopilot** | Chat con Tool Use (loop agentic) sobre 5 herramientas de solo lectura (ventas, stock bajo, cartera, headcount, búsqueda) | 🧪 requiere API key |
| **Savvy Briefing** | Resumen proactivo del día (métricas cross-app); narrativa IA o fallback con plantilla | ✅ funciona (plantilla sin key) |
| **SavvyInsights** | Predictivo determinista: reorden de inventario (velocidad de venta → días de stock), productos estancados, recomendaciones de promo (estancado + best-seller), riesgo de cartera Memorial (tiers + acción sugerida) | ✅ funciona sin IA |
| **SavvyFlow** | Automatizaciones no-code (trigger → condición → acción): editor pipeline visual, plantillas de 1 clic, bandeja de notificaciones, acciones notify/webhook/whatsapp/email | ✅ funciona sin IA |
| **SavvyVoice** | Dictado por voz (Web Speech API del navegador, en el dispositivo) | ✅ funciona sin nada |
| **Parking ANPR** | Foto de vehículo → Claude Vision lee la placa → sugiere entrada/salida; si está sucio sugiere lavado | 🧪 requiere API key |
| **WhatsApp** | Envío vía Meta Graph API; conectado a la acción de SavvyFlow | 🧪 requiere credenciales Meta |

**Disciplinas:** human-in-the-loop (la IA propone, el usuario confirma antes de
escribir en BD), audit log de toda acción IA, aislamiento por tenant, cuota
mensual de tokens por organización.

### Estado de la IA
- **Funciona hoy sin credenciales:** búsqueda universal, briefing (plantilla),
  insights predictivos, SavvyFlow, voz, navegación ⌘K.
- **Se enciende con la API key de Claude:** SavvyScan, Copilot, ANPR, narrativa IA.
- **Se enciende con WhatsApp Business (Meta):** envío de WhatsApp.
- **Pendiente:** la API key real **aún no se ha conectado** (decisión: al final).

---

## 6. Modelo de negocio

- SaaS multi-tenant por suscripción; cada org activa apps de su plan.
- Panel de plataforma con planes/features/overrides por organización.
- **IA como tier premium medido** (estilo Notion AI / Stripe): la medición de uso
  por org ya está construida para soportar la facturación.

---

## 7. Estado, decisiones y limitaciones conocidas (honesto)

**Cosas a tener en cuenta para evaluar mejoras:**

1. **Sin migraciones formales (Alembic):** el esquema se gestiona con scripts DDL
   idempotentes aplicados a mano contra Supabase. Funciona pero no hay historial
   versionado del esquema ni rollback estructurado.
2. **Sin suite de tests automatizada** visible (ni backend ni frontend).
3. **Una sola base de datos** para todos los tenants (aislamiento por RLS +
   `organization_id`). No hay sharding ni DB-por-tenant.
4. **Pooler de Supabase (PgBouncer transaction mode):** sin prepared statements;
   ya generó incidencias (statement_cache_size). Conexión históricamente frágil
   (el proyecto se "perdió"/pausó un par de veces).
5. **Datos demo dispares:** Memorial/HR ricos; POS vacío (los insights de POS no
   muestran nada hasta que haya ventas).
6. **Madurez de apps muy variable** — algunas son CRUD básico, otras (Memorial,
   HR) son profundas.
7. **IA depende de credenciales externas** aún no conectadas (Claude API key,
   WhatsApp Business). Todo el cableado existe; falta encender.
8. **Agentes en background** sin cron real: `/automations/evaluate` existe pero
   nadie lo invoca automáticamente (requiere Render cron / scheduler).
9. **Frontend monolítico de bundle** — el initial bundle excede el presupuesto
   (~577 kB vs 500 kB objetivo). Lazy-loading por ruta sí existe.
10. **Versionado:** frontend en 0.1.x; cada commit bumpea versión y se hace push.
11. **PDF con xhtml2pdf** — limitado en CSS moderno; suficiente para documentos
    simples (desprendibles, liquidaciones).
12. **Sin observabilidad/APM** mencionada (logs básicos, sin tracing/metrics).
13. **Seguridad de secretos:** la API key de IA se cifra con Fernet usando una
    clave **derivada del JWT secret** — si rota el JWT secret, los secretos
    cifrados quedan ilegibles. Trade-off consciente para no agregar config.

---

## 8. Lo que se hizo bien (para contexto, no para inflar)

- Capa de IA **horizontal y medida desde el inicio** (no bolt-on).
- **Human-in-the-loop** como patrón UX consistente (componente Confirmable Action).
- **Savvy Graph** (búsqueda cross-módulo) aprovecha la BD compartida — algo que un
  competidor de apps sueltas no puede replicar.
- Reutilización: los ~797 endpoints existentes son las "herramientas" del Copilot
  (Tool Use), sin reescribir lógica.
- Dashboards rediseñados con un sistema "bento" propio (componentes SVG/CSS sin
  dependencias externas: sparkline, kpi-card, hero, donut, bar, chart-card).

---

## 9. Preguntas concretas para el revisor (otra IA)

1. **Arquitectura de datos:** ¿una sola DB con RLS es sostenible al crecer, o
   conviene ya pensar en particionamiento / esquema-por-tenant? ¿Riesgos de RLS
   mal configurado?
2. **Esquema sin Alembic:** ¿vale la pena migrar a migraciones versionadas ahora,
   o el costo supera el beneficio dado el ritmo actual?
3. **Estrategia de IA:** ¿la decisión de un solo proveedor (Claude) + pgvector +
   medición total es correcta, o hay un riesgo de lock-in que valga abstraer más?
4. **Costos de IA:** ¿el esquema de medición (org/usuario/módulo/acción/prompt) es
   suficiente para facturar de forma justa? ¿Qué falta para un pricing real?
5. **SavvyScan / human-in-the-loop:** ¿el flujo factura→inventario es robusto
   ante facturas reales (variabilidad, errores de OCR)? ¿Qué salvaguardas faltan?
6. **Savvy Graph:** hoy es búsqueda LIKE + unaccent. ¿Cuándo justifica pgvector
   (búsqueda semántica) o un grafo real (FalkorDB)? ¿Vale la deduplicación de
   identidad cross-app como producto en sí?
7. **SavvyFlow:** el motor es trigger→condición→acción con evaluación on-demand.
   ¿Qué le falta para competir con Zapier/n8n a nivel pyme sin volverse complejo?
8. **Seguridad:** cifrado de secretos derivado del JWT secret, multi-tenant en una
   DB, IA que escribe en BD tras confirmación. ¿Vectores de riesgo principales?
9. **Testing/observabilidad:** ¿cuál es el mínimo viable de tests + monitoreo que
   recomendarías dado el tamaño (233 tablas, 797 rutas) y un equipo pequeño?
10. **Priorización de producto:** con 13 apps de madurez dispar + una capa de IA
    nueva, ¿conviene profundizar pocas apps "estrella" o seguir ampliando? ¿Cuál
    sería tu hoja de ruta de 3 movimientos?
11. **Diferenciación:** ¿el "AI OS" (Zero-Form, ⌘K, Graph, Briefing, Flow) es un
    diferencial real y defendible para una pyme LATAM, o features bonitas sin
    foso? ¿Qué lo volvería imprescindible?
12. **Quick wins:** ¿qué 3 mejoras de bajo esfuerzo y alto impacto ves de
    inmediato?

---

## 10. Repositorio / referencias internas

- Estrategia de IA: `docs/analysis/savvy-ai-strategy.md`
- Tracker vivo de la IA (qué está hecho y qué falta): `docs/analysis/savvy-ai-roadmap.md`
- Diseño de la Fase 0: `docs/analysis/savvy-ai-phase0-design.md`
- Análisis previo del ecosistema: `docs/analysis/savvy-ecosystem-analysis.md`
