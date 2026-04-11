# SavvyParking — Automatizacion de Parqueaderos

## Proposito

SavvyParking es la app de **gestion y automatizacion de parqueaderos** del ecosistema Savvy. Soporta desde un parqueadero pequeno hasta una red de estacionamientos inteligentes.

## Entidades (10 tablas)

| Tabla | Descripcion |
|-------|-------------|
| `parking_locations` | Sedes/parqueaderos con capacidad, ocupacion, horarios |
| `parking_zones` | Zonas dentro de una sede (nivel, sector, tipo) |
| `parking_spots` | Espacios individuales con tipo, sensor, cargador |
| `parking_pricing_rules` | Reglas de precio config-driven (por minuto, hora, plana, diaria) |
| `parking_subscriptions` | Planes mensuales/anuales con acceso a zona |
| `parking_vehicles` | Vehiculos con placa, tipo, propietario, suscripcion |
| `parking_sessions` | Sesiones entry/exit con duracion, costo, metodo pago |
| `parking_reservations` | Pre-reservas de espacios con slot de tiempo |
| `parking_services` | Servicios adicionales (lavado, valet, detailing) |
| `parking_service_orders` | Ordenes de servicio vinculadas a sesion |

## PricingEngine

Calcula costo automaticamente segun regla aplicable:
- **per_minute**: tarifa x minutos (despues de gracia)
- **per_hour**: tarifa x horas (fraccion proporcional)
- **flat_rate**: tarifa fija por visita
- **daily**: tarifa x dias
- **grace_minutes**: minutos gratis antes de cobrar
- **min_charge**: cobro minimo
- **max_daily**: tope diario maximo

## Session Lifecycle

```
Entry (placa, tipo, sede, metodo)
  -> Session active (spot occupied, occupancy++)
  -> Exit (calcula costo, aplica pricing rule)
  -> Session completed (spot available, occupancy--)
```

## Metodos de acceso

| Metodo | Descripcion |
|--------|-------------|
| `manual` | Operador registra placa manualmente |
| `lpr` | License Plate Recognition (camara) |
| `qr` | Codigo QR escaneado |
| `rfid` | Tarjeta/tag RFID |

## Frontend (7 vistas)

Dashboard con KPIs en tiempo real (ocupacion, revenue, disponibilidad), infraestructura (sedes con barra de ocupacion), vehiculos, sesiones (entrada/salida en vivo), tarifas config, servicios.

## Endpoints API

Base: `/api/v1/parking/`

### Infrastructure
GET/POST `/locations`, GET/POST `/zones`, GET/POST `/spots`

### Sessions
POST `/sessions/entry`, POST `/sessions/{id}/exit`, GET `/sessions/active`, GET `/sessions/completed`

### Pricing
GET/POST `/pricing/rules`, GET/POST `/pricing/subscriptions`

### Services
GET/POST `/services/types`, GET/POST `/services/orders`, POST `/services/orders/{id}/complete`

### Dashboard
GET `/dashboard/kpis`
