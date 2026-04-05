# Aplicaciones SaaS sobre SavvyCore

---

## Resumen

SavvyCore es la base compartida sobre la cual se construyen multiples aplicaciones SaaS verticales. Cada aplicacion extiende el core con funcionalidad especifica de un dominio de negocio, sin modificar el core en si.

---

## Modelo de extensibilidad

```
+===================================================================+
|                         SavvyCore                                 |
|  +--------+  +---------------+  +---------+  +------------------+ |
|  | Auth   |  | Organizations |  | Gateway |  | Shared Utilities | |
|  +--------+  +---------------+  +---------+  +------------------+ |
+===================================================================+
       |               |                |               |
       v               v                v               v
+==============+  +================+  +================+  +=========+
| SavvyPOS     |  | SavvyLogistics |  | SavvyInventory |  | ...     |
|              |  |                |  |                |  |         |
| - Productos  |  | - Rutas        |  | - Stock        |  |         |
| - Ventas     |  | - Envios       |  | - Almacenes    |  |         |
| - Cajas      |  | - Tracking     |  | - Movimientos  |  |         |
| - Clientes   |  | - Conductores  |  | - Alertas      |  |         |
| - Reportes   |  | - ETAs         |  | - Reportes     |  |         |
+==============+  +================+  +================+  +=========+
```

---

## Aplicaciones planeadas

### SavvyPOS

**Dominio**: Punto de venta para restaurantes, tiendas y comercios.

**Funcionalidades principales**:
- Gestion de productos y categorias
- Registro de ventas y transacciones
- Gestion de cajas (apertura, cierre, cortes)
- Gestion de clientes
- Reportes de ventas (diario, semanal, mensual)
- Impresion de tickets
- Multiples metodos de pago

**Estado**: En planificacion.

### SavvyLogistics

**Dominio**: Gestion de logistica, entregas y transporte.

**Funcionalidades principales**:
- Creacion y seguimiento de envios
- Gestion de rutas y conductores
- Tracking en tiempo real
- Calculo de ETAs
- Notificaciones al cliente
- Reportes de entregas

**Estado**: Concepto.

### SavvyInventory

**Dominio**: Control de inventario y almacenes.

**Funcionalidades principales**:
- Gestion de productos y SKUs
- Multiples almacenes
- Movimientos de entrada/salida
- Alertas de stock bajo
- Reportes de inventario
- Integracion con POS y Logistics

**Estado**: Concepto.

---

## Como se integra una app con el core

### 1. Autenticacion y autorizacion

La app usa el sistema de auth del core. No implementa su propia autenticacion.

```
Cliente App        SavvyCore Auth        App Module
    |                    |                    |
    | Login              |                    |
    |------------------->|                    |
    |                    |                    |
    | JWT con org_id     |                    |
    |<-------------------|                    |
    |                    |                    |
    | Request a la app   |                    |
    | (con JWT)          |                    |
    |---------------------------------------->|
    |                    |                    |
    |                    | Validar JWT,       |
    |                    | extraer contexto   |
    |                    |<-------------------|
    |                    |                    |
```

### 2. Multi-tenancy

Toda tabla de la app incluye `organization_id` y usa las mismas convenciones de RLS del core. En Python, se hereda de `OrgMixin` para incluir automaticamente el campo.

### 3. Routing

Las rutas de la app se montan bajo el namespace de la app en FastAPI:

```
/api/v1/pos/products          <-- SavvyPOS
/api/v1/pos/sales             <-- SavvyPOS
/api/v1/logistics/shipments   <-- SavvyLogistics
/api/v1/inventory/stock       <-- SavvyInventory
```

### 4. Base de datos

Cada app extiende el schema con sus propias tablas, siguiendo las convenciones de BD del core. Las tablas de la app van en el mismo schema pero con prefijo de app en las migraciones:

```
Migraciones del core:
  0001_create_organizations.sql
  0002_create_users.sql
  ...

Migraciones de SavvyPOS:
  pos_0001_create_products.sql
  pos_0002_create_sales.sql
  ...

Migraciones de SavvyLogistics:
  logistics_0001_create_shipments.sql
  ...
```

### 5. Estructura de carpetas

```
app/
  core/                       <-- SavvyCore (no se modifica al agregar una app)
    config.py
    database.py
    security.py
    dependencies.py
  models/                     <-- Modelos SQLAlchemy del core
  routers/                    <-- Routers del core
  schemas/                    <-- Schemas Pydantic del core
  services/                   <-- Servicios del core
  apps/
    pos/                      <-- SavvyPOS
      models/
      routers/
      schemas/
      services/
    logistics/                <-- SavvyLogistics
      models/
      routers/
      schemas/
      services/
```

---

## Reglas para aplicaciones

1. **No modificar el core**: Las apps extienden, no modifican. Si se necesita funcionalidad nueva en el core, se propone como modulo core.
2. **Respetar convenciones**: Toda app sigue las convenciones de BD, API y codigo del core.
3. **Independencia**: Las apps no dependen entre si. SavvyPOS no importa codigo de SavvyLogistics.
4. **Integracion via API o eventos**: Si dos apps necesitan comunicarse, lo hacen via API interna o event bus, nunca accediendo a las tablas de la otra.
5. **Documentar**: Cada app tiene su propia documentacion siguiendo la [plantilla](/_template/README.md).

---

## Template de documentacion

Cada aplicacion debe documentarse usando la plantilla en [apps/_template/README.md](./_template/README.md).

La documentacion de cada app debe incluir como minimo:
- Proposito y alcance
- Arquitectura especifica
- Endpoints de la API
- Esquema de base de datos (extensiones)
- Plan de escalabilidad
- Integracion con el core

---

## Referencias

- [Plantilla para nueva app](./_template/README.md)
- [Guia: Agregar una app](../guides/adding-an-app.md)
- [Arquitectura General](../architecture/overview.md)
