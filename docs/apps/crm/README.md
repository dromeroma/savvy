# SavvyCRM — CRM con Pipelines Configurables

## Proposito

SavvyCRM es el **CRM pipeline-driven** del ecosistema Savvy. Motor de ventas con contactos, leads, deals y actividades.

## Entidades (9 tablas)

| Tabla | Descripcion |
|-------|-------------|
| `crm_contacts` | Contactos CRM (extends People) con source, lifecycle, score, custom fields |
| `crm_companies` | Empresas/organizaciones clientes |
| `crm_contact_companies` | Vinculo M2M contacto-empresa con rol |
| `crm_leads` | Prospectos con fuente, score, estado, conversion |
| `crm_pipelines` | Pipelines configurables con stages, probabilidad, colores |
| `crm_pipeline_stages` | Etapas con is_won/is_lost, rules JSONB |
| `crm_deals` | Oportunidades con valor, probabilidad auto, stage tracking |
| `crm_deal_stage_history` | Audit trail de movimientos entre etapas |
| `crm_activities` | Calls, meetings, emails, tasks, notes con completion |

## Pipeline Design

Cada org configura sus pipelines. Los stages tienen:
- `sort_order` para visualizacion Kanban
- `probability` (0-100%) auto-asignada al deal
- `is_won` / `is_lost` flags para terminal stages
- `rules` JSONB para extensibilidad

## Deal Lifecycle

open -> (move between stages) -> won (is_won stage) / lost (is_lost stage)

Stage history trackeado automaticamente en `crm_deal_stage_history`.

## Frontend (8 vistas)

Dashboard 8 KPIs, contactos, empresas, leads con calificacion, pipelines con stage builder, deals con vista Kanban, actividades con completion.
