# Savvy — Plan de Go-Live (producción 16-jun-2026)

> Checklist ejecutable por fases. Detalle técnico en `savvy-consolidation-plan.md`.
> Leyenda: ✅ hecho · 🔜 en curso · ⬜ pendiente · ⚠️ requiere paso manual/infra.

---

## FASE 1 — Seguridad multi-tenant + hardening (8-10 jun) — ✅ COMPLETA (código)

### Hardening rápido (✅ hecho y verificado)
- ✅ **Clave de cifrado dedicada** `SAVVY_ENCRYPTION_KEY` (con compat MultiFernet:
  descifra los secretos ya cifrados con el JWT secret). [`crypto.py`, `config.py`]
- ✅ **Anti-SSRF** en la acción webhook de SavvyFlow: solo https a IP pública,
  bloquea loopback/privadas/link-local (169.254.169.254), sin redirects.
  [`core/net_safety.py`, `savvy_flow/engine.py`]
- ✅ **Límite de uploads** (10 MB) + validación de tipo en SavvyScan y ANPR.
  [`core/uploads.py`]
- ✅ `statement_cache_size=0` ya estaba en el engine (PgBouncer OK).
- ✅ Tests unitarios que blindan los 3 fixes [`tests/test_security_hardening.py`].

### RLS real — aislamiento a nivel de base de datos (✅ mecanismo completo y PROBADO)
- ✅ **Políticas `tenant_isolation` en 198 tablas** con `organization_id`
  (USING/WITH CHECK por `app.current_org_id` + bypass de plataforma por
  `app.is_platform`). [`scripts/setup_rls_policies.py`]
- ✅ **Rol no-propietario `savvy_app`** (NOLOGIN, NOBYPASSRLS) con grants DML +
  default privileges + membresía al rol de la app. [`scripts/setup_rls_role.py`]
- ✅ **Enforcement por `SET LOCAL ROLE` + GUC por transacción**, gated por
  `SAVVY_RLS_ENFORCE` (default OFF). Event listener `begin` sobre el engine:
  con OFF no hace nada; con ON, cada transacción de tenant corre como `savvy_app`
  → la RLS aísla. Plataforma marca `app.is_platform=on` (cross-org). [`database.py`,
  `tenant_context.py`, middleware, `platform/dependencies.py`]
- ✅ **PROBADO contra datos reales** [`scripts/verify_rls.py`]:
  · owner → 8 empleados (bypass) · savvy_app+San Rafael → 8 · savvy_app+Acueducto
  → **0 (aislado)** · sin org → 0 · plataforma → 8. **RLS aísla correctamente.**
- ✅ **PROBADO por el camino real de la app** (event listener + contextvars):
  enforce OFF → app intacta; enforce ON → aísla por org, plataforma cross-org.
- ✅ Test de aislamiento escrito [`tests/test_tenant_isolation.py`] (HR + POS, 2 orgs).
- ⚠️ **ACTIVACIÓN (flip):** poner `SAVVY_RLS_ENFORCE=true` en el entorno
  (Render). **Hacerlo primero en staging** + smoke de rutas. Rollback instantáneo
  (cambiar la variable a false). El mecanismo ya está validado end-to-end.

### Rate limiting (✅ hecho)
- ✅ Limiter en memoria (sin deps) [`core/rate_limit.py`] aplicado a:
  `/auth/login` (10/min), `/auth/register` (5/5min), `/ai/scan` (20/min),
  `/ai/copilot` (30/min). Migrar a Redis para multi-worker.

### Pendiente Fase 1 (solo activación/CI, no código)
- ⬜ Correr `test_tenant_isolation` + suite en el entorno con pytest (CI).
- ⬜ Flip `SAVVY_RLS_ENFORCE=true` en staging → smoke → prod.

---

## FASE 2 — Estabilidad + IA production-grade (10-11 jun) — ✅ COMPLETA (código)
- ✅ **Retries con backoff** en el cliente Claude (408/409/429/5xx + timeouts;
  hasta 4 intentos, respeta `Retry-After`). [`client.py`]
- ✅ **Prompt caching** (Anthropic): el system prompt se marca `cache_control`
  ephemeral → baja costo/latencia en llamadas repetidas. [`client.py`]
- ✅ **Kill-switch de gasto IA** diario global + per-org (config
  `AI_DAILY_USD_LIMIT_GLOBAL` 50, `AI_DAILY_USD_LIMIT_ORG` 10; 0 = off).
  Integrado en `check_quota` → todos los flujos de IA lo respetan. [`usage.py`]
- ✅ **Endpoint de cron** `POST /automations/evaluate-all` (header `X-Cron-Secret`,
  itera todas las orgs con automatizaciones de datos/agenda). [`savvy_flow/router.py`]
- ⬜ Backups de Supabase verificados con **restore real** (manual — ver abajo).

### Activación de Fase 2 (infra, no código)
- ⚠️ **Cron de agentes:** en Render, crear un *Cron Job* diario que ejecute:
  ```
  curl -X POST https://<backend>/api/v1/automations/evaluate-all \
       -H "X-Cron-Secret: $SAVVY_CRON_SECRET"
  ```
  Variables nuevas a setear en prod: `SAVVY_CRON_SECRET` (aleatorio),
  opcional `SAVVY_AI_DAILY_USD_LIMIT_GLOBAL` / `_ORG`.
- ⚠️ **Backups + restore:** Supabase hace backups automáticos; **probar un restore
  real** a un proyecto/branch de staging al menos una vez antes del go-live (un
  backup nunca restaurado no es un backup). Documentar el RTO/RPO.

---

## FASE 3 — Observabilidad (11-12 jun) — ✅ COMPLETA (código)
- ✅ **Sentry backend** (gated por `SAVVY_SENTRY_DSN`, sentry_sdk ya instalado):
  init en `main.py`, etiqueta cada error con `org_id` + `request_id`. [`observability.py`]
- ✅ **Logging estructurado JSON** (gated por `SAVVY_LOG_JSON`) + middleware
  **tenant-aware**: cada request loguea `org_id`, status, `duration_ms`, `request_id`;
  WARNING en 5xx o requests lentos (`SAVVY_SLOW_REQUEST_MS`). [`logging.py`, `observability.py`]
- ✅ **Readiness** `/health/ready` (ping a la BD) para uptime/load-balancer.
- ✅ **Dashboard de gasto de IA** en `/platform/ai`: gasto de hoy vs límite
  (barra + estado del kill-switch) + sparkline de costo por día. Endpoint
  `/platform/ai/usage/daily` (serie + budget). El panel ya tenía costo por
  org/modelo/app.
- ⬜ **Frontend Sentry** (`@sentry/angular`) — requiere `npm i`; queda como paso
  de instalación (ver abajo) para no romper el build sin la dependencia.
- ⬜ Alertas (Sentry + budget) — se configuran en el dashboard de Sentry / reglas.

### Activación de Fase 3 (infra, no código)
- ⚠️ Setear `SAVVY_SENTRY_DSN` (crear proyecto en Sentry) + `SAVVY_LOG_JSON=true`
  en prod. Sin DSN, todo sigue funcionando (no-op).
- ⚠️ Frontend Sentry: `npm i @sentry/angular` + init en `main.ts` con el DSN.

---

## FASE 4 — Tests del núcleo + CI (12-13 jun)
- ⬜ Tests de los motores de dinero: nómina, liquidación (ley 50), contabilidad
  (asientos balanceados), pricing IA, insights.
- ⬜ Tests de SavvyFlow (trigger→condición→acción) y Savvy Graph (acentos, no-fuga).
- ⬜ CI GitHub Actions: lint (ruff) + typecheck (mypy/tsc) + tests + presupuesto
  de bundle DURO + build. Bloquea merge si algo falla.
- ⬜ Regla de equipo: todo bug arreglado entra con su test de regresión.

---

## FASE 5 — Pre-producción + go-live (13-16 jun)
- ⬜ **Conectar la API key de Claude** en `/platform/ai` → validar SavvyScan,
  Copilot, ANPR, narrativa de Briefing end-to-end.
- ⬜ **Sembrar datos POS realistas** → el demo de SavvyScan factura→inventario vivo.
- ⬜ (Opcional) credenciales WhatsApp Business → activar envíos.
- ⬜ Optimizar bundle < 450 kB (auditar con source-map-explorer; flatpickr/D3 lazy).
- ⬜ Smoke E2E (Playwright) de los flujos críticos: login, scan, liquidación, ⌘K.
- ⬜ **Checklist go-live:** backups verificados, RLS en staging probada, Sentry
  activo, variables de entorno de prod (ENCRYPTION_KEY dedicada), CORS correcto,
  rate limit, plan de rollback.

---

## Bitácora
- 2026-06-08 — **Fase 1 (tanda 1) hecha:** 3 hardening (cifrado dedicado, anti-SSRF,
  límite de uploads) con tests; RLS con 198 políticas dormantes + plumbing del GUC;
  test de aislamiento escrito.
- 2026-06-08 — **Fase 1 COMPLETA (código):** RLS enforcement por `SET LOCAL ROLE` +
  GUC gated por `SAVVY_RLS_ENFORCE`, **probado contra datos reales y por el camino
  real de la app** (Acueducto ve 0 datos de San Rafael). Rol `savvy_app` creado con
  grants. Rate limiting en auth/scan/copilot. Lo único que resta es la **activación**
  (flip de la variable en staging→prod) y correr la suite en CI — no más código de
  seguridad. Siguiente: **Fase 2 — Estabilidad + IA production-grade.**
- 2026-06-08 — **Fase 2 COMPLETA (código):** retries con backoff + prompt caching en
  el cliente Claude; kill-switch de gasto IA diario (global + per-org) integrado en
  check_quota; endpoint `/automations/evaluate-all` para el cron de agentes (protegido
  por X-Cron-Secret). Resta solo infra: crear el cron en Render + setear
  SAVVY_CRON_SECRET, y **probar un restore real** de backups. Siguiente:
  **Fase 3 — Observabilidad (Sentry + dashboard ai_usage + logs).**
- 2026-06-08 — Límite global de gasto IA bajado a **$1/día**.
- 2026-06-08 — **Fase 3 COMPLETA (código):** Sentry backend gated + tags por tenant;
  logging JSON + middleware tenant-aware (org_id, slow/error); readiness `/health/ready`
  con ping a BD; dashboard de gasto de IA en `/platform/ai` (hoy vs límite + kill-switch
  + sparkline diario). Resta infra: DSN de Sentry + `LOG_JSON=true`, y `npm i @sentry/angular`
  para el front. Siguiente: **Fase 4 — Tests del núcleo + CI.**
