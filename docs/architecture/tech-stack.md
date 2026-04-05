# Stack Tecnologico

---

## Resumen

Este documento detalla cada tecnologia elegida para SavvyCore, las alternativas evaluadas y las razones de la decision.

---

## Tabla resumen

| Capa | Tecnologia elegida | Alternativas evaluadas | Justificacion clave |
|------|-------------------|----------------------|-------------------|
| Lenguaje | **Python 3.12+** | TypeScript/Node.js, Go, Rust | Productividad, ecosistema, velocidad de desarrollo |
| Framework HTTP | **FastAPI** | Django, Flask, Litestar | Rendimiento, tipado, OpenAPI automatico |
| Base de datos | **PostgreSQL 16** | MySQL, MongoDB, CockroachDB | RLS, JSON, extensiones, madurez |
| ORM | **SQLAlchemy 2.0** | Tortoise ORM, SQLModel, raw SQL | Madurez, flexibilidad, async nativo |
| Migraciones | **Alembic** | dbmate, Flyway, manual | Integrado con SQLAlchemy, autogeneracion |
| Cache | **Redis** | Memcached, KeyDB | Estructuras de datos, pub/sub, madurez |
| Autenticacion | **JWT (python-jose / PyJWT)** | Auth0, Clerk, Authlib | Control total, sin dependencia externa |
| Validacion | **Pydantic v2** | Marshmallow, Cerberus, attrs | Integrado con FastAPI, rendimiento, tipado |
| Testing | **pytest** | unittest, nose2 | Ecosistema, fixtures, plugins |
| Contenedores | **Docker** | Podman, nativo | Estandar de la industria, ecosistema |
| CI/CD | **GitHub Actions** | GitLab CI, Jenkins | Integrado con GitHub, gratuito para OSS |
| Hosting (inicial) | **Railway / Fly.io** | AWS, DigitalOcean, Render | Simplicidad, costo bajo, buen DX |
| Monitoreo | **Grafana + Prometheus** | Datadog, New Relic | Open source, flexible, costo predecible |

---

## Decisiones detalladas

### Lenguaje: Python 3.12+

| Criterio | Python | TypeScript/Node.js | Go |
|----------|--------|-------------------|-----|
| Productividad de desarrollo | Excelente | Alta | Media |
| Ecosistema de librerias | Enorme | Enorme | Grande |
| Tipado estatico | Opcional (type hints) | Nativo | Nativo |
| Rendimiento HTTP | Bueno (con async) | Bueno | Excelente |
| Facilidad de contratacion | Alta | Alta | Media |
| Soporte para IA/ML | Excelente (nativo) | Limitado | Limitado |

**Decision**: Python ofrece productividad superior, un ecosistema maduro para backend, y capacidades nativas para futuras integraciones con IA/ML. Con FastAPI y async/await, el rendimiento es mas que suficiente para nuestras necesidades.

### Framework HTTP: FastAPI

| Criterio | FastAPI | Django | Flask | Litestar |
|----------|---------|--------|-------|----------|
| Rendimiento | Excelente (async nativo) | Medio | Medio | Excelente |
| OpenAPI automatico | Si (nativo) | Con extensiones | Con extensiones | Si |
| Tipado / Validacion | Pydantic integrado | Manual / DRF | Manual | Attrs/Pydantic |
| Curva de aprendizaje | Baja | Media-alta | Baja | Media |
| Ecosistema | Grande y creciente | Enorme | Enorme | Pequeno |
| Async nativo | Si | Parcial (Django 4.1+) | Con extensiones | Si |

**Decision**: FastAPI combina rendimiento excelente con generacion automatica de OpenAPI, validacion integrada via Pydantic, y soporte async nativo. Es ideal para APIs REST modernas y tiene una comunidad activa.

### Base de datos: PostgreSQL 16

| Criterio | PostgreSQL | MySQL | MongoDB | CockroachDB |
|----------|-----------|-------|---------|-------------|
| Row Level Security | Nativo | No | No | Parcial |
| Tipos JSON | jsonb (indexable) | JSON (limitado) | Nativo | jsonb |
| Extensiones | Enorme ecosistema | Limitado | N/A | Limitado |
| Full-text search | Nativo | Nativo | Nativo (Atlas) | Nativo |
| Transacciones ACID | Completas | Completas | Multi-doc (v4+) | Completas |
| Escalabilidad horizontal | Via Citus/particiones | Group Replication | Nativa | Nativa |
| Costo (managed) | Bajo-medio | Bajo | Medio | Alto |
| Comunidad | Enorme | Enorme | Grande | Creciente |

**Decision**: PostgreSQL es la eleccion natural por RLS nativo (critico para multi-tenancy), soporte avanzado de JSON, extensiones como `pg_trgm` para busqueda fuzzy, y `pgvector` para futuras integraciones con IA. Es la BD relacional mas completa disponible.

### ORM: SQLAlchemy 2.0

| Criterio | SQLAlchemy 2.0 | Tortoise ORM | SQLModel | Raw SQL |
|----------|---------------|-------------|----------|---------|
| Madurez | Excelente (20+ anos) | Media | Baja | N/A |
| Async nativo | Si (2.0+) | Si | Si | Si |
| Flexibilidad de queries | Total (SQL expression) | Media | Media | Total |
| Soporte de tipos Python | Excelente (mapped_column) | Bueno | Excelente | N/A |
| Migraciones | Alembic (integrado) | Aerich | Alembic | Manual |
| Comunidad | Enorme | Media | Creciente | N/A |

**Decision**: SQLAlchemy 2.0 es el ORM mas maduro y flexible de Python. Su nuevo estilo declarativo con `mapped_column` ofrece excelente soporte de tipos. Permite queries complejas con `organization_id`, indices parciales, y RLS sin limitaciones.

### Autenticacion: JWT con PyJWT / python-jose

| Criterio | JWT propio | Auth0 | Clerk |
|----------|-----------|-------|-------|
| Control | Total | Limitado | Limitado |
| Costo | $0 | $23+/mes (>7K MAU) | $25+/mes |
| Latencia | Minima (local) | +50-200ms (API call) | +50-200ms |
| Personalizacion | Total | Media | Baja |
| Multi-tenancy nativo | Lo implementamos | Si | Si |
| Mantenimiento | Alto | Bajo | Bajo |

**Decision**: Para Fase 1, implementamos JWT propio. Esto nos da control total sobre el flujo de autenticacion, cero costo, y latencia minima.

**Plan futuro**: Si se necesita SSO empresarial o social login masivo, evaluar integracion con Auth0 o implementar OAuth2 provider propio.

### Validacion: Pydantic v2

| Criterio | Pydantic v2 | Marshmallow | Cerberus |
|----------|------------|-------------|----------|
| Integracion con FastAPI | Nativa | Manual | Manual |
| Rendimiento | Excelente (Rust core) | Bueno | Bueno |
| Inferencia de tipos | Excelente | Limitada | Limitada |
| Ecosistema | Enorme | Grande | Medio |

**Decision**: Pydantic v2 es la opcion natural con FastAPI. Su core en Rust lo hace extremadamente rapido, y la integracion nativa elimina boilerplate. Los modelos Pydantic se usan tanto para validacion como para serializacion de respuestas.

### Testing: pytest

**Decision**: pytest es el estandar de facto para testing en Python. Su sistema de fixtures, parametrizacion, y extenso ecosistema de plugins (pytest-asyncio, pytest-cov, httpx para testing de FastAPI) lo hacen ideal para nuestro stack.

### Contenedores y Deploy

**Fase 1**: Docker Compose local + Railway/Fly.io para produccion.
**Fase 2+**: Kubernetes (cuando se necesite orquestacion de multiples servicios).

```
docker-compose.yml (desarrollo)
  +-------------------------+
  | app (Python + FastAPI)  |  Puerto 8000
  +-------------------------+
  | postgres:16             |  Puerto 5432
  +-------------------------+
  | redis:7                 |  Puerto 6379
  +-------------------------+
```

---

## Dependencias principales (pyproject.toml / requirements.txt)

```
# Core
fastapi>=0.110
uvicorn[standard]>=0.29
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29
alembic>=1.13
pydantic>=2.6
pydantic-settings>=2.2

# Auth
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
bcrypt>=4.1

# Cache
redis>=5.0

# Utilities
python-multipart>=0.0.9
httpx>=0.27

# Dev
pytest>=8.0
pytest-asyncio>=0.23
pytest-cov>=4.1
ruff>=0.3
mypy>=1.9
```

---

## Variables de entorno

Todas las variables de configuracion usan el prefijo `SAVVY_`:

```env
# Base de datos
SAVVY_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/savvycore

# JWT
SAVVY_JWT_SECRET_KEY=your-secret-key
SAVVY_JWT_ALGORITHM=HS256
SAVVY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
SAVVY_JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
SAVVY_REDIS_URL=redis://localhost:6379/0

# Servidor
SAVVY_HOST=0.0.0.0
SAVVY_PORT=8000
SAVVY_DEBUG=true
SAVVY_CORS_ORIGINS=["http://localhost:3000"]
```

---

## Principios de seleccion de tecnologia

1. **Preferir open source** sobre soluciones propietarias.
2. **Preferir librerias maduras y bien mantenidas** sobre las mas nuevas.
3. **Preferir estandares** (ASGI, OpenAPI, SQL) sobre APIs propietarias.
4. **Evaluar costo total** incluyendo hosting, licencias, y tiempo de desarrollo.
5. **Mantener opciones de salida** -- nunca depender de un vendor sin plan de migracion.

---

## Referencias

- [Arquitectura General](./overview.md)
- [Escalabilidad](./scalability.md)
