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
| 1 | WOW — Savvy Command + SavvyScan | ⬜ Pendiente | 0% |
| 2 | Copilot + Briefing + Búsqueda + Graph | ⬜ Pendiente | 0% |
| 3 | Predictivo + Workflows visuales | ⬜ Pendiente | 0% |
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
- ⬜ Endpoint `/ai/scan` (subir archivo → `ai_extractions`)
- ⬜ Prompt + schema de **factura de compra** (proveedor, ítems, cantidades, costos, fechas, impuestos)
- ⬜ Mapeo extracción → entidades POS (producto, proveedor, movimiento de inventario)
- ⬜ Flujo "Confirmable Action": revisar ítems antes de escribir stock
- ⬜ Al confirmar: crea/actualiza productos, ajusta stock, registra compra y movimiento financiero

### Savvy Command (barra ⌘K)
- ⬜ Componente global de command bar (atajo ⌘K / Ctrl+K)
- ⬜ Drag & drop de archivo dentro de la barra
- ⬜ Router de intención: texto/archivo → módulo + acción
- ⬜ Render del resultado como Confirmable Action

### Criterios de aceptación Fase 1
- ⬜ Subir foto/PDF de una factura real → inventario actualizado tras confirmar
- ⬜ Tiempo de captura de una compra baja de minutos a segundos
- ⬜ El usuario nunca escribió un formulario manual completo

---

## FASE 2 — Copilot + Briefing + Búsqueda Universal + Graph

- ⬜ SavvyCopilot: Tool Use sobre endpoints existentes (solo lectura primero)
- ⬜ Acciones con confirmación (escritura vía Confirmable Action)
- ⬜ Búsqueda universal cross-módulo ("todo de Carlos")
- ⬜ Savvy Graph básico: entidad persona unificada cross-app (pgvector + joins)
- ⬜ Savvy Briefing: resumen diario por rol (in-app)

---

## FASE 3 — Predictivo + Workflows visuales

- ⬜ SavvyInsights sobre dashboards bento (anomalías + narrativa)
- ⬜ Inventario predictivo (reorden, demanda)
- ⬜ Riesgo financiero / mora temprana
- ⬜ Motor de recomendaciones (promos, productos, precios)
- ⬜ SavvyFlow: workflows no-code (estilo Zapier/n8n)

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
