# Savvy — Checklist de Go-Live (16-jun-2026)

> Runbook de lanzamiento. Marca cada casilla antes de abrir a clientes reales.
> Todo el **código** de las Fases 1-5 está hecho; esto es la **activación**.

---

## 1. Variables de entorno (producción / Render)

Setear en el backend (todas con prefijo `SAVVY_`):

- [ ] `SAVVY_APP_ENV=prod`
- [ ] `SAVVY_DATABASE_URL` — pooler de Supabase (puerto 6543)
- [ ] `SAVVY_JWT_SECRET_KEY` — aleatorio 256-bit (NO el de ejemplo)
- [ ] `SAVVY_ENCRYPTION_KEY` — **dedicado**, `python -c "import secrets;print(secrets.token_urlsafe(32))"`
- [ ] `SAVVY_CORS_ORIGINS` — solo el dominio real del frontend
- [ ] `SAVVY_CRON_SECRET` — aleatorio (para el cron de agentes)
- [ ] `SAVVY_AI_DAILY_USD_LIMIT_GLOBAL=1.0` (o el tope deseado)
- [ ] `SAVVY_SENTRY_DSN` — del proyecto Sentry
- [ ] `SAVVY_LOG_JSON=true`
- [ ] `SAVVY_RLS_ENFORCE` — **dejar en `false` hasta el paso 3**

## 2. Base de datos (ya aplicado, verificar)

- [x] DDL de todos los módulos aplicado a Supabase (HR, Memorial, AI, Flow, …)
- [x] Políticas RLS `tenant_isolation` en 198 tablas (`setup_rls_policies.py`)
- [x] Rol `savvy_app` creado con grants (`setup_rls_role.py`)
- [x] `verify_rls.py` → "RLS AÍSLA CORRECTAMENTE"
- [ ] **Backups:** confirmar que Supabase hace backups automáticos y **probar un
      restore real** a un proyecto/branch de staging. Anotar RTO/RPO.

## 3. Activar RLS (el paso de seguridad clave)

- [ ] En **staging**: `SAVVY_RLS_ENFORCE=true` → smoke de rutas (login, listar
      empleados/contratos, crear algo, dashboard, ⌘K). Verificar que un usuario
      de una org no ve datos de otra.
- [ ] Si todo OK en staging → `SAVVY_RLS_ENFORCE=true` en **prod**.
- [ ] Rollback listo: volver a `false` reactiva el bypass al instante.

## 4. IA (encender)

- [ ] Pegar la **API key de Claude** en `/platform/ai` → "Probar conexión".
- [ ] Verificar SavvyScan (subir una factura real), Copilot (una pregunta),
      ANPR (foto de placa), narrativa del Briefing.
- [ ] Confirmar que `/platform/ai` muestra el gasto del día y el kill-switch.
- [ ] (Opcional) WhatsApp: token + phone_id en `/platform/ai` → "Probar envío".

## 5. Automatizaciones (cron de agentes)

- [ ] Crear *Cron Job* en Render (diario):
      `curl -X POST https://<backend>/api/v1/automations/evaluate-all -H "X-Cron-Secret: $SAVVY_CRON_SECRET"`
- [ ] Verificar que genera notificaciones en la bandeja de SavvyFlow.

## 6. Observabilidad

- [ ] Sentry recibe eventos (forzar un error de prueba) y etiqueta `org_id`.
- [ ] Logs JSON visibles en el agregador (Render logs / Loki / Better Stack).
- [ ] `/health/ready` responde 200 con la BD arriba (configurar el health check
      del servicio para que apunte aquí).
- [ ] Uptime monitor (Better Stack / UptimeRobot) sobre `/health/ready`.

## 7. Frontend

- [ ] `npm i @sentry/angular` + init en `main.ts` con el DSN.
- [ ] Build de producción pasa (presupuesto inicial < 750kB enforced).
- [ ] `environment.prod.ts` apunta al backend de prod.
- [ ] Deploy en Vercel (dominio app.savvytrix.com).

## 8. Tests / CI

- [x] Tests de motores de dinero verdes (verificados).
- [ ] CI de GitHub Actions en verde (revisar el primer run; limpiar nits de lint).
- [ ] Smoke E2E (Playwright): `npx playwright test` con `PLAYWRIGHT_BASE_URL` y
      `E2E_EMAIL`/`E2E_PASSWORD` apuntando a staging.

## 9. Datos demo (para mostrar)

- [x] Funeraria San Rafael: HR + Memorial con cartera y riesgo reales.
- [x] **POS demo sembrado** (`seed_pos_demo.py`): 14 productos, 60 ventas →
      Insights vivos (7 reorden, 4 estancados, 4 promos).

## 10. Seguridad final

- [ ] CORS restringido al dominio real (no `*`).
- [ ] Rate limiting verificado (login/scan/copilot devuelven 429 al exceder).
- [ ] Webhooks de SavvyFlow rechazan URLs internas (probar `169.254.169.254`).
- [ ] Uploads rechazan archivos > 10 MB y tipos no permitidos.
- [ ] Plan de rollback documentado (revertir deploy + `SAVVY_RLS_ENFORCE=false`).

---

## Orden recomendado el día del lanzamiento
1. Backups verificados (restore real) → 2. Variables de entorno → 3. Deploy
backend + frontend → 4. Smoke en staging con RLS ON → 5. Activar RLS en prod →
6. Conectar API key + probar IA → 7. Cron + Sentry + uptime → 8. Smoke final →
9. Abrir a clientes.

> Si algo falla: `SAVVY_RLS_ENFORCE=false` y revertir el deploy. La app vuelve al
> estado estable conocido en segundos.
