# Guia: Agregar un nuevo modulo a SavvyCore

---

## Resumen

Esta guia describe el proceso paso a paso para agregar un nuevo modulo al core de SavvyCore. Un modulo core provee funcionalidad compartida que todas las aplicaciones SaaS pueden utilizar (ej: notifications, billing, audit-log).

**Antes de empezar**: Asegurate de que la funcionalidad realmente pertenece al core y no a una app especifica. Si solo la necesita una app, deberia ser parte de esa app, no del core.

---

## Criterios para un modulo core

Un modulo pertenece al core si cumple AL MENOS dos de estos criterios:

- [ ] Lo necesitan (o necesitaran) multiples aplicaciones SaaS.
- [ ] Es funcionalidad transversal (auth, notifications, billing, audit).
- [ ] Gestiona datos que son compartidos entre apps.
- [ ] Es infraestructura que toda app requiere.

---

## Paso 1: Definir el modulo

Antes de escribir codigo, documentar:

1. **Nombre del modulo**: Sustantivo en ingles, singular o plural segun convenga (ej: `notifications`, `billing`, `audit`).
2. **Proposito**: Una frase que resuma que hace.
3. **Alcance**: Que incluye y que NO incluye.
4. **Dependencias**: Que otros modulos necesita.
5. **Tabla de endpoints** preliminar.
6. **Tablas de BD** preliminares.

Crear un documento en `docs/modules/{nombre}/README.md` con esta informacion.

---

## Paso 2: Crear la estructura de carpetas

```
app/
  models/
    {nombre}.py                <-- Modelo SQLAlchemy
  routers/
    {nombre}.py                <-- Router FastAPI con endpoints
  schemas/
    {nombre}.py                <-- Schemas Pydantic (request/response)
  services/
    {nombre}_service.py        <-- Logica de negocio
```

### Export del modulo

Cada router se registra en `app/main.py`:

```python
# app/main.py
from app.routers import auth, organizations, nombre

app = FastAPI()
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(nombre.router)
```

---

## Paso 3: Crear las tablas de base de datos

### 3.1 Crear la migracion

```
migrations/{numero_secuencial}_create_{nombre_tabla}.sql
```

### 3.2 Seguir las convenciones de BD

Checklist obligatorio:

- [ ] `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- [ ] `organization_id UUID NOT NULL REFERENCES organizations(id)` (si la tabla tiene datos por org)
- [ ] `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- [ ] `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- [ ] Trigger `trg_{tabla}_updated_at`
- [ ] Indices en foreign keys
- [ ] Indice en `organization_id` (si aplica)
- [ ] RLS habilitado (si tiene `organization_id`)
- [ ] `deleted_at TIMESTAMPTZ` si se necesita soft delete

### 3.3 Crear el modelo SQLAlchemy

```python
# app/models/{nombre}.py
import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, OrgMixin, TimestampMixin

class NombreTabla(Base, OrgMixin, TimestampMixin):
    __tablename__ = "{tabla}"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # organization_id viene de OrgMixin
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # ... campos adicionales
    # created_at, updated_at vienen de TimestampMixin
```

---

## Paso 4: Implementar el servicio

El servicio contiene la logica de negocio. Valida reglas de negocio, coordina acceso a datos, y emite eventos.

```python
# app/services/{nombre}_service.py
from sqlalchemy.ext.asyncio import AsyncSession

class NombreService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, org_id: uuid.UUID, data: CreateNombreInput) -> NombreEntity:
        # 1. Validar reglas de negocio
        # 2. Crear en BD
        # 3. Emitir evento (si aplica)
        # 4. Retornar resultado
        ...

    async def get_by_id(self, org_id: uuid.UUID, item_id: uuid.UUID) -> NombreEntity | None:
        ...

    async def list_by_org(self, org_id: uuid.UUID, page: int, per_page: int):
        ...
```

---

## Paso 5: Implementar los schemas Pydantic

```python
# app/schemas/{nombre}.py
from pydantic import BaseModel

class CreateNombreRequest(BaseModel):
    name: str  # min_length=2, max_length=100
    description: str | None = None

class NombreResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
```

---

## Paso 6: Implementar el router

Un router con todos los endpoints del modulo:

```python
# app/routers/{nombre}.py
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, get_org_id, require_role

router = APIRouter(prefix="/api/v1/{nombre}", tags=["{nombre}"])

@router.get("/")
async def list_items(
    org_id: uuid.UUID = Depends(get_org_id),
    user = Depends(get_current_user),
):
    ...

@router.post("/", status_code=201)
async def create_item(
    data: CreateNombreRequest,
    org_id: uuid.UUID = Depends(get_org_id),
    user = Depends(require_role("admin")),
):
    ...

@router.get("/{item_id}")
async def get_item(
    item_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    user = Depends(get_current_user),
):
    ...

@router.patch("/{item_id}")
async def update_item(
    item_id: uuid.UUID,
    data: UpdateNombreRequest,
    org_id: uuid.UUID = Depends(get_org_id),
    user = Depends(require_role("admin")),
):
    ...

@router.delete("/{item_id}")
async def delete_item(
    item_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    user = Depends(require_role("admin")),
):
    ...
```

---

## Paso 7: Registrar en la app FastAPI

Agregar el router al punto de entrada:

```python
# app/main.py
from app.routers.{nombre} import router as nombre_router

app.include_router(nombre_router)
```

---

## Paso 8: Escribir tests

### Tests unitarios (services)

```python
# tests/{nombre}/test_{nombre}_service.py
import pytest

class TestNombreService:
    async def test_create_item(self, db_session):
        # Arrange: preparar datos
        # Act: llamar al servicio
        # Assert: verificar resultado
        ...

    async def test_business_rules(self, db_session):
        ...
```

### Tests de integracion (endpoints)

```python
# tests/{nombre}/test_{nombre}_routes.py
import pytest
from httpx import AsyncClient

class TestNombreEndpoints:
    async def test_create_returns_201(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/{nombre}",
            json={"name": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Test"

    async def test_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/{nombre}")
        assert response.status_code == 401
```

### Test de aislamiento multi-tenant

```python
async def test_org_isolation(self, client, org_a_headers, org_b_headers):
    # 1. Crear recurso con org A
    response = await client.post(
        "/api/v1/{nombre}",
        json={"name": "Recurso A"},
        headers=org_a_headers,
    )
    item_id = response.json()["data"]["id"]

    # 2. Intentar acceder con org B
    response = await client.get(
        f"/api/v1/{{nombre}}/{item_id}",
        headers=org_b_headers,
    )
    assert response.status_code == 404
```

---

## Paso 9: Documentar

Actualizar la documentacion:

1. **Crear** `docs/modules/{nombre}/README.md` con la documentacion completa del modulo.
2. **Crear** `docs/api/{nombre}-endpoints.md` con los endpoints detallados.
3. **Actualizar** `docs/database/schema.md` con las nuevas tablas.
4. **Actualizar** `docs/README.md` agregando el modulo al indice.

---

## Checklist final

Antes de hacer merge del modulo:

- [ ] Estructura de carpetas correcta
- [ ] Migracion de BD creada y probada
- [ ] RLS configurado en tablas con organization_id
- [ ] Schemas Pydantic para toda validacion de input
- [ ] Router, servicios y modelos implementados
- [ ] Router registrado en app/main.py
- [ ] Tests unitarios con cobertura > 80%
- [ ] Tests de integracion para endpoints principales
- [ ] Test de aislamiento multi-tenant
- [ ] Documentacion creada y actualizada
- [ ] Code review aprobado

---

## Ejemplo completo: Modulo Notifications

Para ver un ejemplo completo de un modulo, revisa la estructura del modulo Auth en `app/routers/auth.py` y su documentacion en [docs/modules/auth/README.md](../modules/auth/README.md).

---

## Referencias

- [Arquitectura General](../architecture/overview.md)
- [Convenciones de BD](../database/conventions.md)
- [Convenciones API](../api/README.md)
