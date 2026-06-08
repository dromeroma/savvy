# Savvy AI OS — Roadmap & Tracker Vivo

> Este documento es el **tablero de progreso oficial** de la iniciativa de IA.
> Se actualiza al cerrar cada fase: ✅ hecho · 🔜 en curso · ⬜ pendiente.
> Estrategia completa en [`savvy-ai-strategy.md`](./savvy-ai-strategy.md).
> Última actualización: 2026-06-08.

## Leyenda
- ✅ Completado y verificado
- 🔜 En curso
- ⬜ Pendiente
- 🧪 Hecho pero sin probar en datos reales

---

## Estado global

| Fase | Nombre | Estado | Avance |
|------|--------|--------|--------|
| 0 | Cimiento (`savvy_ai`) | 🧪 Construida y desplegada (sin API key real) | ~90% |
| 1 | WOW — Savvy Command + SavvyScan | 🧪 Construida (sin API key real) | ~85% |
| 2 | Copilot + Briefing + Búsqueda + Graph | 🧪 Construida (búsqueda + briefing YA funcionan) | ~85% |
| 3 | Predictivo + Recomendaciones (+ Workflows dif.) | ✅ Predictivo OK · 🔜 SavvyFlow diferido a 3b | ~70% |
| 4 | Voz + WhatsApp + Vision + Agentes | ⬜ Pendiente | 0% |

---

## FASE 0 — Cimiento (`savvy_ai`)

> Objetivo: la capa invisible que hace posible TODO lo demás. Sin esto, cada
> feature de IA sería un parche con su propio cliente, sin control de costo,
> sin auditoría, sin aislamiento. **Es el módulo más importante y el menos visible.**

### Backend — módulo `backend/src/modules/savvy_ai/`
- ✅ `client.py` — cliente Claude (httpx, sin SDK extra) con tiering + interfaz `LLMProvider`; lee API key CIFRADA de BD
- ✅ `crypto.py` — cifrado Fernet de la API key (clave derivada del JWT secret)
- ✅ `pricing.py` — tarifas por modelo + cálculo de costo USD
- ✅ `models.py` — 6 tablas ORM
- ✅ `schemas.py` — Pydantic: provider, settings, jobs, ConfirmableAction, reportes de uso
- ✅ `service.py` — ProviderService, ScanService, UsageAnalyticsService
- ✅ `vision.py` — extracción documento/imagen → JSON (Claude Vision + tool-use forzado)
- ✅ `usage.py` — medición de tokens/costo + cuota por org (mide TODO)
- ✅ `router.py` — `/api/v1/ai/*` (org) + `/api/v1/platform/ai/*` (super admin)
- ✅ `prompts/registry.py` — prompts versionados (factura de compra v1)

### Base de datos (DDL idempotente) — aplicado a Supabase
- ✅ `ai_provider_config` — PLATAFORMA: API key cifrada + modelos + tarifas (singleton)
- ✅ `ai_org_settings` — cuota mensual, tiers permitidos, features por org
- ✅ `ai_jobs` — cola async
- ✅ `ai_extractions` — resultado de SavvyScan reutilizable
- ✅ `ai_usage` — MEDICIÓN: org · usuario · módulo · acción · prompt · modelo · costo (5 índices)
- ✅ `ai_audit_log` — propuesto/confirmado/editado/descartado

### Frontend
- ✅ `shared/components/ai/confirmable-action.component.ts` — tarjeta [Confirmar][Editar][Descartar] con confianza por campo
- ✅ `core/services/ai.service.ts` — cliente de `/api/v1/ai/*`
- ✅ `platform/ai/platform-ai.component.ts` — panel super admin: API key + uso global (bento)
- ⬜ `ai-field.component.ts` standalone — (integrado dentro de confirmable-action; opcional separarlo)

### Seguridad / plataforma
- ✅ API key configurable SOLO desde super admin, cifrada en reposo
- ✅ Endpoints de plataforma protegidos con `require_super_admin`
- ✅ Aislamiento por tenant (todas las tablas `ai_*` con organization_id)
- ⬜ Permisos granulares `ai.use`/`ai.admin` en el catálogo de la org (pendiente — hoy basta con pertenecer a la org)

### Criterios de aceptación Fase 0
- ✅ Crear un job de extracción y consultar su estado (endpoints listos)
- ✅ Cada llamada al LLM se registra en `ai_usage` con costo (lógica en usage.py)
- ✅ Cada propuesta/confirmación queda en `ai_audit_log`
- ✅ Org sin cuota recibe error claro (check_quota)
- ✅ El componente Confirmable Action renderiza una extracción
- 🧪 **Falta probar end-to-end con API key real** (no la tenemos aún — se agrega desde `/platform/ai`)

---

## FASE 1 — WOW (Savvy Command + SavvyScan)

> Objetivo: el demo que vende toda la visión. Un flujo perfecto:
> **factura de compra → inventario en POS.**

### SavvyScan (extracción)
- ✅ Endpoint `/ai/scan` (subir archivo → `ai_extractions`) — listo desde Fase 0
- ✅ Prompt + schema de **factura de compra** (proveedor, ítems, cantidades, costos, fechas, impuestos) — `extraction.purchase_invoice` v1
- ✅ Mapeo extracción → entidades POS: `apps/pos/ai_apply.py` (busca/crea producto por SKU o nombre, ajusta costo, sugiere precio con margen 30%)
- ✅ Flujo "Confirmable Action": revisar/editar ítems antes de escribir stock
- ✅ Al confirmar: crea/actualiza productos + registra movimiento de compra (stock +) en la sede principal; idempotente (no re-aplica)
- ✅ Dispatch genérico `_apply_to_target_app` (extensible a otras apps/documentos)
- ⬜ Movimiento financiero/contable de la compra (queda para integrar con `finance`/`accounting`)

### Savvy Command (barra ⌘K)
- ✅ Componente global `savvy-command` montado en el shell (atajo ⌘K / Ctrl+K)
- ✅ Navegación instantánea con teclado (↑↓ + ↵) sobre destinos curados
- ✅ Drag & drop de archivo → enruta a SavvyScan
- ✅ Trigger visible en el header ("✨ Buscar o ejecutar… ⌘K")
- ⬜ Router de intención por lenguaje natural (texto → acción) → **Fase 2** (Copilot/Tool Use)

### Frontend
- ✅ Página `/pos/scan` (dropzone + estado + Confirmable Action + resumen de resultado)
- ✅ Entrada en sidebar POS "Escanear factura ✨"
- ✅ Resumen post-confirmación: "Inventario actualizado: N creados, M actualizados…"

### Criterios de aceptación Fase 1
- 🧪 Subir foto/PDF de una factura real → inventario actualizado tras confirmar (**requiere API key**)
- ✅ El flujo no requiere llenar un formulario manual completo
- ✅ Barra ⌘K disponible en toda la plataforma

---

## FASE 2 — Copilot + Briefing + Búsqueda Universal + Graph

### Savvy Graph / Búsqueda universal (✅ funciona HOY, sin API key)
- ✅ `graph.py`: búsqueda cross-módulo (HR + Memorial afiliados + Memorial leads + Water)
- ✅ Insensible a acentos (extensión `unaccent` habilitada en Supabase + normalización en Python)
- ✅ Busca por nombre, documento, email, código
- ✅ `resolve_person`: agrupa apariciones por documento → persona unificada (el moat)
- ✅ Endpoint `GET /ai/search?q=` · probado en vivo (Cárdenas/Romero/Salazar cross-módulo)
- ✅ Integrado en la barra ⌘K (sección "Personas y registros")

### SavvyCopilot (🧪 listo, requiere API key)
- ✅ `copilot.py`: loop agentic con Tool Use (hasta 5 iteraciones)
- ✅ Registro de herramientas (solo lectura): universal_search, pos_sales_summary,
  pos_low_stock, memorial_receivables, hr_headcount
- ✅ Cada llamada se mide en `ai_usage` (app_code=copilot)
- ✅ Endpoint `POST /ai/copilot` + modo chat en la barra ⌘K
- ⬜ Acciones de escritura con Confirmable Action (Fase 3+)

### Savvy Briefing (✅ funciona HOY con plantilla; narrativa IA con API key)
- ✅ `briefing.py`: agrega métricas cross-app (POS ventas/stock, Memorial cartera, HR headcount)
- ✅ Narrativa IA (Haiku) si hay API key; fallback con plantilla si no → **funciona sin IA**
- ✅ Endpoint `GET /ai/briefing` · probado (San Rafael: cartera vencida $6.37M, 8 activos)
- ✅ Tarjeta "Resumen del día" en el dashboard principal (badge ✨ por IA / automático)

### Pendiente Fase 2
- ⬜ pgvector / embeddings para búsqueda semántica (hoy es LIKE; suficiente por ahora)
- ⬜ Lenguaje natural en ⌘K depende del Copilot → requiere API key para responder

---

## FASE 3 — Predictivo + Recomendaciones

> `insights.py` — análisis determinista (funciona SIN API key). Probado en vivo.

### Predictivo + recomendaciones (✅ funciona hoy)
- ✅ Inventario predictivo POS: velocidad de venta (ventana 30d) → días de stock →
  **sugerencia de reorden** con cantidad y costo estimado, priorizada por urgencia
- ✅ Productos **estancados** (con stock, sin ventas) + capital inmovilizado
- ✅ **Motor de recomendaciones de promo**: empareja estancado + best-seller de la misma categoría
- ✅ **Riesgo de cartera Memorial**: contratos con facturas vencidas, tiers alto/medio/bajo,
  acción sugerida ("Llamar hoy", "Recordatorio", "Monitorear"). Probado: 42 en riesgo, $6.37M vencido, 15 alto
- ✅ `insights_summary`: tarjetas de titulares para el dashboard
- ✅ Endpoints: `/ai/insights/summary`, `/ai/insights/pos`, `/ai/insights/memorial`

### Frontend (✅)
- ✅ `/pos/insights` "Sugerencias IA": reorden + estancados + promos (bento)
- ✅ `/memorial/risk` "Riesgo de cartera": HERO vencido + tiers + tabla priorizada con acción
- ✅ Entradas en sidebar POS y Memorial

### Pendiente / diferido
- 🔜 **SavvyFlow (workflows visuales no-code)** → movido a una **sub-fase 3b** propia.
  Es un constructor de automatizaciones (trigger→acción) grande y autónomo; se hará
  como módulo dedicado para no diluir el resto. Los "eventos inteligentes" que pedía
  la visión ya están parcialmente cubiertos por Insights (alertas de stock/mora).
- ⬜ Narrativa IA sobre los insights (explicación en lenguaje natural) → con API key
- ⬜ Predicción de vencimiento de productos perecederos → cuando POS registre fechas de caducidad

---

## FASE 4 — Voz + WhatsApp + Vision + Agentes

- ⬜ SavvyVoice (Whisper) alimentando Command/Scan
- ⬜ Integración WhatsApp (consultas, notificaciones, Briefing)
- ⬜ SavvyVision: ANPR de placas en Parking (entra/sale/incidentes)
- ⬜ Agentes en background (recordatorios de cobro, restock, alertas)

---

## Bitácora de cambios
- 2026-06-08 — Documento creado. Estrategia fusionada y Fase 0 diseñada.
- 2026-06-08 — **Fase 0 construida y desplegada** (v0.1.0). Módulo `savvy_ai` completo,
  6 tablas aplicadas a Supabase, panel super admin `/platform/ai` con API key cifrada
  + uso global, componente Confirmable Action. Falta únicamente la API key real
  (se agrega desde el panel) para probar end-to-end. Siguiente: **Fase 1 — factura→inventario en POS**.
- 2026-06-08 — **Fase 1 construida** (v0.1.1). SavvyScan factura→inventario en POS
  (`apps/pos/ai_apply.py` + dispatch en confirm), página `/pos/scan` con dropzone +
  Confirmable Action, y **Savvy Command (⌘K)** global en el shell. Todo el flujo listo;
  solo falta la API key real para la prueba end-to-end (se agrega al final de todas las fases).
  Siguiente: **Fase 2 — Copilot + Briefing + Búsqueda Universal + Graph**.
- 2026-06-08 — **Fase 2 construida** (v0.1.2). Savvy Graph/búsqueda universal cross-módulo
  (`graph.py`, insensible a acentos, probada en vivo) integrada en ⌘K; SavvyCopilot
  (`copilot.py`, loop agentic + 5 herramientas de solo lectura) con modo chat en ⌘K;
  Savvy Briefing (`briefing.py`, métricas cross-app + narrativa) como tarjeta en el dashboard.
  **Búsqueda universal y briefing ya funcionan sin API key**; el copilot conversacional
  se enciende cuando se agregue la key. Siguiente: **Fase 3 — Predictivo + Workflows visuales**.
- 2026-06-08 — **Fase 3 construida** (v0.1.3, parte predictiva). `insights.py` con
  inventario predictivo POS (reorden/estancados/promos) y riesgo de cartera Memorial,
  todo determinista (funciona sin API key). Probado: 42 clientes en riesgo, $6.37M vencido.
  Páginas `/pos/insights` y `/memorial/risk`. **SavvyFlow (workflows visuales) diferido a
  sub-fase 3b** por ser un constructor autónomo grande. Siguiente: **Fase 4 — Voz + WhatsApp
  + Vision (Parking) + Agentes**, o **3b SavvyFlow** si se prioriza automatización.
