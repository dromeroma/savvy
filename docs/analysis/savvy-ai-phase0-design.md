# Fase 0 — Diseño detallado del módulo `savvy_ai`

> El cimiento. Capa compartida que consumen las 13 apps. Diseñado para encajar
> con los patrones existentes (BaseMixin/OrgMixin, setup DDL idempotente,
> gateway router, catálogo de permisos).
> Estado: **diseño para validar** — sin construir todavía.

---

## 1. Estructura del módulo

```
backend/src/modules/savvy_ai/
├── __init__.py
├── client.py        # LLMProvider (interfaz) + ClaudeProvider; tiering Haiku/Sonnet/Opus
├── models.py        # ORM: AiJob, AiUsage, AiAuditLog, AiExtraction, AiOrgSettings
├── schemas.py       # Pydantic: ScanRequest, ExtractionResult, ConfirmableAction, JobStatus...
├── service.py       # Orquestación: crear/ejecutar job, medir uso, audit, cuota
├── vision.py        # documento/imagen -> JSON estructurado (Claude Vision + structured output)
├── usage.py         # conteo de tokens, costo, verificación de cuota por org
├── router.py        # /api/v1/ai/*
└── prompts/
    ├── __init__.py
    └── registry.py  # plantillas versionadas (extraction.invoice.v1, etc.)
```

Registro en `gateway/router.py`:
```python
from src.modules.savvy_ai.router import router as ai_router
api_router.include_router(ai_router)
```

---

## 2. Modelo de datos (5 tablas, todas con OrgMixin → RLS por tenant)

### 2.1 `ai_org_settings` — configuración + cuota por organización (1:1)
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid PK | |
| organization_id | uuid FK | único |
| ai_enabled | bool | feature on/off |
| monthly_token_quota | bigint | 0 = ilimitado |
| tokens_used_this_period | bigint | reset mensual |
| period_resets_at | date | |
| allowed_models | jsonb | `["haiku","sonnet","opus"]` |
| features | jsonb | `{scan:true, copilot:false, ...}` granular |

### 2.2 `ai_jobs` — cola async de trabajos de IA
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid PK | |
| organization_id | uuid FK | |
| job_type | varchar | `scan`, `copilot`, `insight`, `briefing` |
| status | varchar | `queued`, `running`, `succeeded`, `failed`, `cancelled` |
| source_kind | varchar | `file`, `text`, `image`, `voice` |
| source_ref | text | URL/ruta del archivo o hash del texto |
| model_used | varchar | `claude-haiku-4-5` … |
| input_summary | text | qué se pidió (para audit) |
| output | jsonb | resultado estructurado |
| error | text | si falló |
| created_by | uuid FK users | |
| created_at / updated_at / completed_at | timestamptz | |

### 2.3 `ai_extractions` — resultado de SavvyScan (reutilizable)
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid PK | |
| organization_id | uuid FK | |
| job_id | uuid FK ai_jobs | |
| document_type | varchar | `purchase_invoice`, `id_card`, `contract`, `meter`… |
| extracted_data | jsonb | datos estructurados |
| confidence | numeric(5,2) | 0–100 global |
| field_confidence | jsonb | confianza por campo |
| target_app | varchar | `pos`, `memorial`… |
| status | varchar | `pending_review`, `confirmed`, `discarded` |
| confirmed_entity_id | uuid | a qué registro se aplicó |
| confirmed_by | uuid FK users | |
| created_at / updated_at | timestamptz | |

### 2.4 `ai_usage` — medición (base de la facturación)
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid PK | |
| organization_id | uuid FK | |
| job_id | uuid FK | nullable |
| model | varchar | |
| input_tokens / output_tokens | int | |
| cached_tokens | int | prompt caching |
| cost_usd | numeric(12,6) | calculado por tarifa del modelo |
| feature | varchar | `scan`, `copilot`… |
| created_at | timestamptz | |

### 2.5 `ai_audit_log` — trazabilidad de toda acción IA
| Columna | Tipo | Notas |
|---|---|---|
| id | uuid PK | |
| organization_id | uuid FK | |
| job_id | uuid FK | nullable |
| action | varchar | `proposed`, `confirmed`, `edited`, `discarded` |
| actor_user_id | uuid FK | |
| summary | text | "Propuso registrar 12 productos desde factura X" |
| payload | jsonb | snapshot de lo propuesto/confirmado |
| created_at | timestamptz | |

DDL idempotente en `backend/scripts/setup_savvy_ai.py` (mismo patrón que
`setup_hr_phase*.py`).

---

## 3. API — `/api/v1/ai/*`

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/ai/scan` | Sube archivo/imagen → crea job → devuelve `extraction` (pending_review) |
| GET | `/ai/jobs/{id}` | Estado de un job async |
| GET | `/ai/extractions/{id}` | Resultado de extracción |
| POST | `/ai/extractions/{id}/confirm` | Confirma (con edición opcional) → ejecuta la acción real en la app destino |
| POST | `/ai/extractions/{id}/discard` | Descarta |
| GET | `/ai/usage` | Uso/cuota de la org (para UI de plan) |
| GET | `/ai/settings` · PATCH | Config de IA de la org (admin) |

**Contrato de `ConfirmableAction`** (lo que el frontend renderiza):
```jsonc
{
  "extraction_id": "uuid",
  "title": "Registrar compra a Distribuidora XYZ",
  "target_app": "pos",
  "summary": "12 productos · $1.240.000 · IVA $235.600",
  "confidence": 94.5,
  "fields": [
    { "key": "supplier_name", "label": "Proveedor", "value": "Distribuidora XYZ", "confidence": 98, "editable": true },
    { "key": "total", "label": "Total", "value": "1240000", "confidence": 99, "editable": true }
  ],
  "line_items": [ /* ítems editables con su confianza */ ],
  "actions": ["confirm", "edit", "discard"]
}
```

---

## 4. Cliente LLM con tiering

`LLMProvider` (interfaz abstracta) → `ClaudeProvider` (impl). Permite cambiar de
proveedor sin tocar el resto. Selección de modelo por tarea:

| Tarea | Modelo | Razón |
|---|---|---|
| Clasificar tipo de documento | Haiku 4.5 | barato, alto volumen |
| Validar/autocompletar campos | Haiku 4.5 | barato |
| Extracción de factura/cédula | Sonnet 4.6 | precisión visión + structured output |
| Copilot conversacional | Sonnet 4.6 | balance |
| Insights / agentes multi-paso | Opus 4.8 | razonamiento |

Todas las llamadas pasan por `usage.py` → registran tokens/costo y verifican
cuota **antes** de ejecutar (si no hay cuota → 402/403 claro, no se gasta).

---

## 5. Frontend — primitivas reutilizables

```
frontend/src/app/shared/components/ai/
├── confirmable-action.component.ts   # tarjeta [Confirmar][Editar][Descartar] (reusa bento)
├── ai-field.component.ts             # campo editable con barra de confianza
└── confidence-badge.component.ts     # chip de % de confianza (verde/amber/rojo)
core/services/ai.service.ts           # cliente de /api/v1/ai/*
```

La `confirmable-action` reusa `chart-card`/tonos de la librería bento para
mantener coherencia visual. Confianza < 70% → campo resaltado para revisión.

---

## 6. Seguridad / plataforma

- Permisos nuevos en el catálogo: `ai.use` (usar IA), `ai.admin` (config/cuota).
- Feature `ai` registrada por organización (on/off + cuota) en `ai_org_settings`.
- RLS sobre todas las tablas `ai_*` (igual que el resto del esquema multi-tenant).
- Audit obligatorio: ninguna acción IA escribe en BD de la app sin pasar por
  `ai_audit_log` + confirmación humana.

---

## 7. Criterios de aceptación (Fase 0 = "lista")

1. Crear un job de extracción y consultar su estado.
2. Cada llamada al LLM registrada en `ai_usage` con costo en USD.
3. Cada propuesta/confirmación/descartado en `ai_audit_log`.
4. Org sin cuota → error claro, sin gasto.
5. Componente `confirmable-action` renderiza una extracción de ejemplo (mock).

> Nota: la Fase 0 **no** entrega una feature visible de cara al usuario final —
> entrega el cimiento. La primera magia visible llega en la Fase 1
> (factura → inventario). Es tentador saltarse la Fase 0; no hacerlo es lo que
> separa una plataforma sólida de un montón de parches.

---

## 8. Orden de construcción sugerido (cuando aprobemos)

1. DDL `setup_savvy_ai.py` + modelos ORM.
2. `client.py` + `usage.py` (cliente Claude + medición).
3. `vision.py` + prompt de factura + `/ai/scan` + `/ai/jobs`.
4. `confirm`/`discard` + `ai_audit_log`.
5. Frontend: `ai.service.ts` + `confirmable-action` con extracción mock.
6. Permisos + `ai_org_settings` + cuota.
7. Verificación de criterios de aceptación end-to-end.
