# Guia: Crear una nueva aplicacion SaaS sobre SavvyCore

---

## Resumen

Esta guia describe el proceso completo para crear una nueva aplicacion SaaS (como SavvyPOS, SavvyLogistics, etc.) que se ejecuta sobre la base de SavvyCore.

---

## Prerequisitos

Antes de empezar:

- [ ] SavvyCore esta funcionando localmente (auth, organizations, gateway).
- [ ] Tienes claro el dominio de negocio de la app.
- [ ] Has definido el MVP (funcionalidades minimas viables).
- [ ] Has revisado la [arquitectura general](../architecture/overview.md).
- [ ] Has revisado las [convenciones de BD](../database/conventions.md) y [API](../api/README.md).

---

## Paso 1: Planificacion

### 1.1 Definir el alcance

Responder estas preguntas:

1. **Que problema resuelve?** {Una frase clara}
2. **Quienes son los usuarios?** {Tipos de usuario}
3. **Que funcionalidades tiene el MVP?** {Lista priorizada}
4. **Que datos maneja?** {Entidades principales}
5. **Que integraciones necesita?** {APIs externas, otros modulos}

### 1.2 Elegir el prefijo de la app

El prefijo se usa en rutas API y nombres de migracion:

| App | Prefijo | Ruta base |
|-----|---------|-----------|
| SavvyPOS | `pos` | `/api/v1/pos/` |
| SavvyLogistics | `logistics` | `/api/v1/logistics/` |
| SavvyInventory | `inventory` | `/api/v1/inventory/` |
| {Tu app} | `{prefijo}` | `/api/v1/{prefijo}/` |

**Reglas del prefijo**:
- Minusculas, sin guiones ni guiones bajos.
- Corto (max 15 caracteres).
- Descriptivo del dominio.
- Unico entre todas las apps.

---

## Paso 2: Crear la estructura de carpetas

```
app/apps/{prefijo}/
  models/                <-- Modelos SQLAlchemy
  routers/               <-- Routers FastAPI
  schemas/               <-- Schemas Pydantic
  services/              <-- Logica de negocio

migrations/
  {prefijo}_0001_create_{primera_tabla}.sql
```

### Crear los archivos base

**Router principal** -- Rutas de la app:

```python
# app/apps/{prefijo}/routers/{recurso}.py
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, get_org_id

router = APIRouter(prefix="/api/v1/{prefijo}", tags=["{prefijo}"])

# Las dependencies del core se aplican automaticamente
@router.get("/products")
async def list_products(
    org_id: uuid.UUID = Depends(get_org_id),
    user = Depends(get_current_user),
):
    ...
```

---

## Paso 3: Disenar la base de datos

### 3.1 Identificar las entidades

Listar todas las tablas que la app necesita. Para cada una:

- Nombre (plural, snake_case)
- Columnas con tipos
- Relaciones con otras tablas
- Indices necesarios

### 3.2 Crear las migraciones

Nombrar las migraciones con el prefijo de la app:

```
migrations/{prefijo}_0001_create_products.sql
migrations/{prefijo}_0002_create_categories.sql
migrations/{prefijo}_0003_create_sales.sql
```

### 3.3 Seguir las convenciones obligatorias

Toda tabla de la app DEBE incluir:

```sql
CREATE TABLE {nombre_tabla} (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id),
    -- ... campos de la app ...
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indice en organization_id
CREATE INDEX idx_{tabla}_organization_id ON {tabla}(organization_id);

-- RLS
ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_isolation ON {tabla}
    USING (organization_id = current_setting('app.current_org')::UUID);

CREATE POLICY org_insert ON {tabla}
    FOR INSERT
    WITH CHECK (organization_id = current_setting('app.current_org')::UUID);

-- Trigger updated_at
CREATE TRIGGER trg_{tabla}_updated_at
    BEFORE UPDATE ON {tabla}
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.4 Crear los modelos SQLAlchemy

```python
# app/apps/{prefijo}/models/product.py
import uuid
from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, OrgMixin, TimestampMixin

class Product(Base, OrgMixin, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # organization_id viene de OrgMixin
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # created_at, updated_at vienen de TimestampMixin
```

### 3.5 Relaciones con tablas del core

Las tablas de la app pueden referenciar tablas del core:

```python
# Referencia a organizations (via OrgMixin)
# organization_id ya viene incluido

# Referencia a users (creador, asignado, etc.)
created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
```

**Nunca** crear FK desde tablas del core hacia tablas de la app. La dependencia es unidireccional: app --> core.

---

## Paso 4: Implementar la logica

### 4.1 Patron por recurso

Para cada recurso/entidad de la app, crear:

```
app/apps/{prefijo}/
  models/
    {recurso}.py              <-- Modelo SQLAlchemy
  routers/
    {recurso}.py              <-- Router FastAPI
  schemas/
    {recurso}.py              <-- Schemas Pydantic
  services/
    {recurso}_service.py      <-- Logica de negocio
```

### 4.2 Usar los servicios del core

La app puede importar dependencies y utilidades del core:

```python
# Usar las dependencies del core para auth y organizacion
from app.core.dependencies import get_current_user, get_org_id, require_role

# Ejemplo de endpoint protegido
@router.post("/sales", status_code=201)
async def create_sale(
    data: CreateSaleRequest,
    org_id: uuid.UUID = Depends(get_org_id),
    user = Depends(require_role("member")),
    db: AsyncSession = Depends(get_db),
):
    ...
```

### 4.3 No modificar el core

Si necesitas funcionalidad nueva en el core:

1. Proponer un nuevo modulo core (ver [guia de agregar modulo](./adding-a-module.md)).
2. Discutir con el equipo si realmente es transversal.
3. Si se aprueba, implementarlo como modulo core separado.
4. **Nunca** agregar codigo especifico de una app dentro de `app/core/` o `app/models/` del core.

---

## Paso 5: Registrar la app en FastAPI

### 5.1 Agregar los routers

```python
# app/main.py
from app.routers import auth, organizations
from app.apps.pos.routers import products as pos_products, sales as pos_sales

app = FastAPI()

# Routers del core
app.include_router(auth.router)
app.include_router(organizations.router)

# Routers de apps
app.include_router(pos_products.router)
app.include_router(pos_sales.router)
```

### 5.2 Configurar rate limiting especifico (si aplica)

```python
# Si la app tiene endpoints con limites especiales
rate_limit_config = {
    "/api/v1/pos/sales": {"limit": 200, "window": "1m"}
}
```

---

## Paso 6: Configurar feature flags por organizacion

Cada organizacion puede habilitar/deshabilitar apps via el campo `settings.features`:

```json
{
  "features": {
    "pos": true,
    "logistics": false,
    "inventory": true
  }
}
```

Crear una dependency que verifique si la org tiene la app habilitada:

```python
# app/apps/{prefijo}/dependencies.py
from fastapi import Depends, HTTPException

async def require_feature_enabled(
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    org = await get_organization(db, org_id)
    if not org.settings.get("features", {}).get("{prefijo}", False):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FEATURE_NOT_ENABLED",
                "message": "Esta funcionalidad no esta habilitada para tu organizacion"
            }
        )
```

---

## Paso 7: Escribir tests

### Tests minimos requeridos

1. **Unitarios**: Logica de negocio en services.
2. **Integracion**: Cada endpoint responde correctamente.
3. **Multi-tenant**: Datos aislados entre organizaciones.
4. **Permisos**: RBAC funciona correctamente.
5. **Feature flag**: App deshabilitada retorna 403.

### Estructura de tests

```
tests/apps/{prefijo}/
  test_{recurso}_service.py
  test_{recurso}_routes.py
  test_multi_tenant.py
```

### Test multi-tenant ejemplo

```python
class TestOrgIsolation:
    async def test_org_a_cannot_see_org_b_data(self, client, org_a_headers, org_b_headers):
        # 1. Crear producto con Org A
        response = await client.post(
            "/api/v1/pos/products",
            json={"name": "Producto A", "price": 10.00},
            headers=org_a_headers,
        )
        product_id = response.json()["data"]["id"]

        # 2. Listar productos con Org B
        response = await client.get(
            "/api/v1/pos/products",
            headers=org_b_headers,
        )
        products = response.json()["data"]

        # 3. Verificar que el producto de A no aparece
        assert len(products) == 0
        assert not any(p["id"] == product_id for p in products)
```

---

## Paso 8: Documentar la app

### 8.1 Crear la documentacion

Copiar la plantilla y completarla:

```
docs/apps/{prefijo}/
  README.md              <-- Copiar de docs/apps/_template/README.md
```

Ver la [plantilla de documentacion](../apps/_template/README.md) para el formato completo.

### 8.2 Actualizar la documentacion del core

- **docs/README.md**: Agregar la app al indice.
- **docs/apps/README.md**: Agregar la app a la lista de apps planeadas/existentes.
- **docs/database/schema.md**: Agregar las tablas de la app (o crear un schema.md separado en `docs/apps/{prefijo}/`).

---

## Paso 9: Despliegue

### 9.1 Migraciones

Las migraciones de la app se ejecutan junto con las del core, en orden secuencial:

```
0001_create_organizations.sql       <-- Core
0002_create_users.sql               <-- Core
0003_create_memberships.sql         <-- Core
pos_0001_create_products.sql        <-- App POS
pos_0002_create_categories.sql      <-- App POS
pos_0003_create_sales.sql           <-- App POS
logistics_0001_create_shipments.sql <-- App Logistics
```

### 9.2 Variables de entorno

Si la app necesita configuracion propia, agregar variables con el prefijo `SAVVY_` seguido del prefijo de la app:

```env
# Variables de SavvyPOS
SAVVY_POS_RECEIPT_PRINTER_ENABLED=true
SAVVY_POS_DEFAULT_TAX_RATE=0.19

# Variables de SavvyLogistics
SAVVY_LOGISTICS_GOOGLE_MAPS_API_KEY=xxx
SAVVY_LOGISTICS_DEFAULT_TRACKING_INTERVAL=30
```

---

## Checklist final

Antes de hacer merge de la nueva app:

- [ ] Prefijo unico definido y registrado
- [ ] Estructura de carpetas creada
- [ ] Migraciones de BD creadas y probadas
- [ ] RLS en todas las tablas con organization_id
- [ ] Routers, services, modelos implementados
- [ ] Schemas Pydantic para validacion de input
- [ ] Routers registrados en app/main.py
- [ ] Feature flag dependency implementada
- [ ] Tests unitarios (> 80% cobertura en services)
- [ ] Tests de integracion (todos los endpoints)
- [ ] Test de aislamiento multi-tenant
- [ ] Test de feature flag
- [ ] Documentacion creada (README.md de la app)
- [ ] Documentacion del core actualizada
- [ ] Variables de entorno documentadas
- [ ] Code review aprobado

---

## Diagrama resumen del proceso

```
+-------------------+     +-------------------+     +-------------------+
| 1. PLANIFICAR     |     | 2. ESTRUCTURA     |     | 3. BASE DE DATOS  |
|                   |     |                   |     |                   |
| - Definir alcance |---->| - Crear carpetas  |---->| - Disenar tablas  |
| - Elegir prefijo  |     | - Modelos         |     | - Migraciones     |
| - MVP features    |     | - Routers         |     | - RLS + indices   |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                            v
+-------------------+     +-------------------+     +-------------------+
| 6. DOCUMENTAR     |     | 5. TESTING        |     | 4. IMPLEMENTAR    |
|                   |     |                   |     |                   |
| - README app      |<----| - Unitarios       |<----| - Routers         |
| - Actualizar core |     | - Integracion     |     | - Services        |
| - Endpoints       |     | - Multi-tenant    |     | - Schemas         |
+-------------------+     +-------------------+     +-------------------+
        |
        v
+-------------------+
| 7. DEPLOY         |
|                   |
| - Migraciones     |
| - Variables env   |
| - Feature flags   |
+-------------------+
```

---

## Referencias

- [Apps sobre SavvyCore](../apps/README.md)
- [Plantilla de app](../apps/_template/README.md)
- [Guia: Agregar un modulo](./adding-a-module.md)
- [Arquitectura General](../architecture/overview.md)
- [Convenciones de BD](../database/conventions.md)
- [Convenciones API](../api/README.md)
