# SavvyCondo — Administracion de Propiedades Horizontales

## Proposito

SavvyCondo es la app de **gestion de condominios y propiedad horizontal** del ecosistema Savvy. Cubre administracion financiera, gobernanza digital, mantenimiento y comunicacion comunitaria.

## Entidades (11 tablas)

| Tabla | Descripcion |
|-------|-------------|
| `condo_properties` | Edificios/conjuntos con config de cuotas, mora, gracia |
| `condo_units` | Unidades con coeficiente de copropiedad |
| `condo_residents` | Propietarios/arrendatarios (extends People) |
| `condo_visitors` | Control de visitantes con entry/exit |
| `condo_fees` | Cuotas de administracion generadas por coeficiente |
| `condo_common_areas` | Areas comunes reservables (piscina, salon, bbq, etc.) |
| `condo_reservations` | Reservas de areas comunes |
| `condo_maintenance` | Solicitudes de mantenimiento/PQR con prioridad |
| `condo_assemblies` | Asambleas con quorum y propuestas |
| `condo_votes` | Votos digitales ponderados por coeficiente |
| `condo_announcements` | Comunicados con categoria y prioridad |

## Fee Generation

Las cuotas se generan automaticamente por periodo usando el coeficiente de copropiedad:
```
cuota_unidad = admin_fee_base * unit.coefficient
```

## Governance (diferenciador)

- Asambleas ordinarias/extraordinarias con quorum configurable
- Propuestas en JSONB
- Votacion digital ponderada por coeficiente de copropiedad
- Cada unidad vota 1 vez por propuesta (UniqueConstraint)

## Frontend (9 vistas)

Dashboard KPIs, propiedades, residentes/visitantes (tabs), cuotas con generacion masiva y pago, areas comunes, mantenimiento/PQR, asambleas con votacion, comunicados.

## Endpoints API

Base: `/api/v1/condo/`

Properties: GET/POST `/properties`, GET/POST `/units`
Residents: GET/POST `/residents`, GET/POST/POST-exit `/visitors`
Fees: GET `/fees`, POST `/fees/generate`, POST `/fees/{id}/pay`
Areas: GET/POST `/areas`, GET/POST `/areas/reservations`
Maintenance: GET/POST `/maintenance`, PATCH `/maintenance/{id}`
Governance: GET/POST `/governance/assemblies`, POST `/governance/votes`, GET `/governance/assemblies/{id}/votes`
Communication: GET/POST `/announcements`
Dashboard: GET `/dashboard/kpis`
