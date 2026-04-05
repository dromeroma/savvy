# Documentacion de SavvyCore

> Base modular para todas las aplicaciones SaaS de Savvitrix Solutions.

---

## Acerca de este repositorio

**SavvyCore** es el nucleo compartido sobre el cual se construyen todas las aplicaciones SaaS de Savvitrix Solutions (SavvyPOS, SavvyLogistics, SavvyInventory, etc.). Proporciona autenticacion, gestion de organizaciones, gateway API, multi-tenancy y las convenciones base que todo producto debe seguir.

**Stack tecnologico**: Python 3.12+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis

---

## Indice de documentacion

### Arquitectura

| Documento | Descripcion |
|-----------|-------------|
| [Arquitectura General](./architecture/overview.md) | Vision general: monolito modular, API-first, multi-tenant |
| [Multi-tenancy](./architecture/multi-tenancy.md) | Estrategia de multi-tenancy: BD compartida, schema compartido, RLS con organization_id |
| [Escalabilidad](./architecture/scalability.md) | Plan de evolucion: microservicios, event bus, multi-region, IA |
| [Stack Tecnologico](./architecture/tech-stack.md) | Decisiones de tecnologia con alternativas evaluadas |

### Modulos del Core

| Documento | Descripcion |
|-----------|-------------|
| [Auth](./modules/auth/README.md) | Autenticacion JWT, flujos de registro/login, RBAC |
| [Organization](./modules/organization/README.md) | Gestion de organizaciones, membresias, invitaciones |
| [API Gateway](./modules/gateway/README.md) | Pipeline de middleware, routing, versionado |

### Base de Datos

| Documento | Descripcion |
|-----------|-------------|
| [Esquema de BD](./database/schema.md) | Esquema completo Fase 1: tablas, columnas, tipos, constraints |
| [Convenciones de BD](./database/conventions.md) | Naming, UUIDs, organization_id, timestamps, indices |

### API

| Documento | Descripcion |
|-----------|-------------|
| [Convenciones API](./api/README.md) | REST, versionado, headers, errores, paginacion |
| [Endpoints de Auth](./api/auth-endpoints.md) | Endpoints de autenticacion con ejemplos (7 endpoints) |
| [Endpoints de Organization](./api/organization-endpoints.md) | Endpoints de organizacion con ejemplos (7 endpoints) |

### Aplicaciones SaaS

| Documento | Descripcion |
|-----------|-------------|
| [Apps sobre SavvyCore](./apps/README.md) | Como se construyen las apps SaaS sobre el core |
| [Template de App](./apps/_template/README.md) | Plantilla para documentar una nueva aplicacion |

### Guias de Desarrollo

| Documento | Descripcion |
|-----------|-------------|
| [Agregar un Modulo](./guides/adding-a-module.md) | Paso a paso para crear un nuevo modulo en el core |
| [Agregar una App](./guides/adding-an-app.md) | Paso a paso para crear una nueva app SaaS |

---

## Endpoints de la API (13 total)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Registrar nuevo usuario |
| POST | `/api/v1/auth/login` | Iniciar sesion |
| POST | `/api/v1/auth/refresh` | Renovar access token |
| POST | `/api/v1/auth/logout` | Cerrar sesion |
| GET | `/api/v1/auth/me` | Obtener perfil del usuario |
| PATCH | `/api/v1/auth/me` | Actualizar perfil del usuario |
| POST | `/api/v1/auth/change-password` | Cambiar contrasena |
| GET | `/api/v1/organizations/me` | Obtener organizacion activa |
| PATCH | `/api/v1/organizations/me` | Actualizar organizacion activa |
| GET | `/api/v1/organizations/members` | Listar miembros |
| POST | `/api/v1/organizations/members/invite` | Enviar invitacion |
| PATCH | `/api/v1/organizations/members/{membership_id}/role` | Cambiar rol de miembro |
| DELETE | `/api/v1/organizations/members/{membership_id}` | Remover miembro |
| POST | `/api/v1/organizations/invitations/{token}/accept` | Aceptar invitacion |

---

## Convenciones de esta documentacion

- **Idioma**: Toda la documentacion esta en espanol.
- **Diagramas**: Se usan diagramas ASCII/texto para maxima portabilidad.
- **Formato**: Cada documento es auto-contenido y puede leerse de forma independiente.
- **Actualizacion**: Al modificar codigo que afecte la arquitectura, actualizar la documentacion correspondiente.

---

## Estructura de carpetas

```
docs/
  README.md                          <-- Este archivo
  architecture/
    overview.md                      <-- Arquitectura general
    multi-tenancy.md                 <-- Estrategia multi-tenant
    scalability.md                   <-- Plan de escalabilidad
    tech-stack.md                    <-- Stack tecnologico
  modules/
    auth/README.md                   <-- Modulo de autenticacion
    organization/README.md           <-- Modulo de organizaciones
    gateway/README.md                <-- API Gateway
  database/
    schema.md                        <-- Esquema de base de datos
    conventions.md                   <-- Convenciones de BD
  api/
    README.md                        <-- Convenciones API
    auth-endpoints.md                <-- Endpoints de auth
    organization-endpoints.md        <-- Endpoints de organizacion
  apps/
    README.md                        <-- Guia de apps SaaS
    _template/README.md              <-- Plantilla para nueva app
  guides/
    adding-a-module.md               <-- Guia: agregar modulo
    adding-an-app.md                 <-- Guia: agregar app
```

---

*Mantenido por el equipo de Savvitrix Solutions.*
