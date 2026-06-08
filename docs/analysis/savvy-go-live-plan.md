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

## FASE 2 — Estabilidad + IA production-grade (10-11 jun)
- ⬜ Retries con backoff en el cliente Claude (429/500/timeout).
- ⬜ Circuit breaker / kill-switch de gasto IA diario global.
- ⬜ Prompt caching (Anthropic) en system prompts largos.
- ⬜ Cron de `/automations/evaluate` (Render cron) → agentes en background.
- ⬜ Backups de Supabase verificados con **restore real** (no solo configurados).

---

## FASE 3 — Observabilidad (11-12 jun)
- ⬜ Sentry (backend + frontend) — error tracking. (~1-2 h, 60% del valor)
- ⬜ Dashboard de `ai_usage` (costo por org/día/modelo) en el panel de plataforma.
- ⬜ Logs estructurados JSON + métricas básicas por tenant (p95, error rate).
- ⬜ Alertas: gasto IA, error rate por tenant, runs de SavvyFlow fallidos.

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
