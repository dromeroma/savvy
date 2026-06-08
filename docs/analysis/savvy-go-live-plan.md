# Savvy — Plan de Go-Live (producción 16-jun-2026)

> Checklist ejecutable por fases. Detalle técnico en `savvy-consolidation-plan.md`.
> Leyenda: ✅ hecho · 🔜 en curso · ⬜ pendiente · ⚠️ requiere paso manual/infra.

---

## FASE 1 — Seguridad multi-tenant + hardening (8-10 jun)

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

### RLS real — aislamiento a nivel de base de datos
- ✅ **Políticas `tenant_isolation` creadas en 198 tablas** con `organization_id`
  (USING/WITH CHECK por `app.current_org_id` + bypass de plataforma por
  `app.is_platform`). **DORMANTES**: el rol propietario las bypassa, la app
  sigue intacta. [`scripts/setup_rls_policies.py`]
- ✅ Plumbing del GUC listo: contextvar por request + helper `apply_tenant_guc`.
  [`core/tenant_context.py`, middleware tenant]
- ✅ Verificado: la app sigue leyendo normal tras aplicar políticas.
- ⬜ **Test de aislamiento multi-tenant** [`tests/test_tenant_isolation.py`] —
  escrito (HR + POS, 2 orgs, detecta fugas). **Falta correrlo en CI/staging**
  (pytest no está en este entorno; el proyecto sí lo corre).
- ⚠️ **CUT-OVER de RLS (paso deliberado, NO en esta tanda):**
  1. Crear rol `savvy_app` con LOGIN, **sin** `BYPASSRLS`, sin ser owner;
     `GRANT` de DML sobre las tablas + USAGE en el schema.
  2. Wirear `apply_tenant_guc` al inicio de cada transacción (event listener
     `begin` sobre `engine.sync_engine`, leyendo el contextvar).
  3. Cambiar `SAVVY_DATABASE_URL` al rol `savvy_app`.
  4. Correr `test_tenant_isolation` **en verde** + smoke de los 797 endpoints.
  5. **Hacerlo primero en una DB de staging** (branch de Supabase), no en prod.
  *Razón de no hacerlo ya: un fallo en el GUC tumba toda la app; sin suite de
  tests verde es temerario contra la única BD productiva.*

### Pendiente Fase 1
- ⬜ Rate limiting (slowapi) en auth/scan/copilot.
- ⬜ Correr `test_tenant_isolation` y arreglar las fugas que encuentre.
- ⬜ Cut-over de RLS en staging.

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
  test de aislamiento escrito. Falta: correr tests en CI, rate limit y el cut-over
  de RLS en staging. Siguiente: terminar Fase 1 (rate limit + cut-over) o Fase 2.
