# Savvy{NombreApp} - Documentacion

> **Nota**: Esta es una plantilla. Reemplaza todo el contenido entre `{llaves}` con la informacion real de tu aplicacion.

---

## Resumen

**Savvy{NombreApp}** es una aplicacion SaaS construida sobre SavvyCore para el dominio de {descripcion del dominio}.

**Estado**: {En planificacion | En desarrollo | Beta | Produccion}
**Version actual**: {0.1.0}
**Responsable**: {Nombre del responsable}

---

## Proposito

{Descripcion detallada del problema que resuelve esta aplicacion. Quienes son los usuarios objetivo. Que valor entrega.}

### Usuarios objetivo

| Tipo de usuario | Descripcion | Ejemplo |
|-----------------|-------------|---------|
| {Tipo 1} | {Descripcion} | {Ejemplo concreto} |
| {Tipo 2} | {Descripcion} | {Ejemplo concreto} |

### Funcionalidades principales

1. **{Funcionalidad 1}**: {Descripcion breve}
2. **{Funcionalidad 2}**: {Descripcion breve}
3. **{Funcionalidad 3}**: {Descripcion breve}
4. **{Funcionalidad 4}**: {Descripcion breve}

---

## Arquitectura

### Diagrama de modulos

```
+===================================================================+
|                         SavvyCore                                 |
|  +--------+  +---------------+  +---------+                      |
|  | Auth   |  | Organizations |  | Gateway |                      |
+===================================================================+
                         |
                         v
+===================================================================+
|                    Savvy{NombreApp}                                |
|                                                                   |
|  +----------------+  +----------------+  +------------------+     |
|  | {Modulo 1}     |  | {Modulo 2}     |  | {Modulo 3}       |    |
|  | - {feature a}  |  | - {feature a}  |  | - {feature a}    |    |
|  | - {feature b}  |  | - {feature b}  |  | - {feature b}    |    |
|  +----------------+  +----------------+  +------------------+     |
+===================================================================+
```

### Dependencias del core

| Modulo del core | Como se usa |
|----------------|------------|
| Auth | {Ej: Autenticacion de usuarios, RBAC para permisos de la app} |
| Organization | {Ej: Contexto de tenant para aislar datos} |
| Gateway | {Ej: Middleware pipeline para las rutas de la app} |

### Roles extendidos (si aplica)

Si la app necesita roles o permisos adicionales a los del core:

| Rol/Permiso | Codigo | Descripcion |
|-------------|--------|-------------|
| {Rol 1} | `{codigo}` | {Descripcion} |
| {Rol 2} | `{codigo}` | {Descripcion} |

---

## Endpoints de la API

### Base URL

```
/api/v1/{app_prefix}/
```

### Tabla de endpoints

| Metodo | Ruta | Descripcion | Rol minimo |
|--------|------|-------------|-----------|
| GET | `/{recurso}` | {Listar recursos} | {member} |
| POST | `/{recurso}` | {Crear recurso} | {member} |
| GET | `/{recurso}/:id` | {Obtener detalle} | {member} |
| PUT | `/{recurso}/:id` | {Actualizar} | {admin} |
| DELETE | `/{recurso}/:id` | {Eliminar} | {admin} |

### Detalle de endpoints

Para cada endpoint principal, documentar:

#### {METODO} /{ruta}

**Descripcion**: {Que hace este endpoint}

**Request**:
```http
{METODO} /api/v1/{app_prefix}/{ruta}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "{campo1}": "{valor1}",
  "{campo2}": "{valor2}"
}
```

**Response ({status})**:
```json
{
  "data": {
    "id": "uuid",
    "{campo1}": "{valor1}"
  }
}
```

**Errores**:
| Status | Codigo | Cuando |
|--------|--------|--------|
| {400} | `{CODIGO}` | {Descripcion} |

---

## Base de datos

### Tablas

Listar todas las tablas que agrega esta app.

#### Tabla: {nombre_tabla}

```sql
CREATE TABLE {nombre_tabla} (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID    NOT NULL REFERENCES organizations(id),
    {campo1}    {TIPO}      {NOT NULL} {DEFAULT},
    {campo2}    {TIPO}      {NOT NULL} {DEFAULT},
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| `id` | UUID | Identificador unico |
| `organization_id` | UUID | FK a organizations |
| `{campo1}` | {TIPO} | {Descripcion} |

### Diagrama de relaciones

```
{Diagrama ASCII de las relaciones entre tablas de la app}
```

### Migraciones

```
{app_prefix}_0001_{descripcion}.sql
{app_prefix}_0002_{descripcion}.sql
```

---

## Escalabilidad

### Volumen esperado

| Metrica | Estimacion Fase 1 | Estimacion Fase 2 |
|---------|-------------------|-------------------|
| {Metrica 1} | {valor} | {valor} |
| {Metrica 2} | {valor} | {valor} |

### Estrategias de escalabilidad

1. **{Estrategia 1}**: {Descripcion}
2. **{Estrategia 2}**: {Descripcion}

---

## Integracion con el core

### Eventos emitidos

| Evento | Payload | Cuando se emite |
|--------|---------|----------------|
| `{app}.{entidad}.{accion}` | `{ id, organization_id, ... }` | {Descripcion} |

### Eventos consumidos

| Evento | Origen | Accion tomada |
|--------|--------|--------------|
| `{modulo}.{entidad}.{accion}` | {Core/OtraApp} | {Descripcion} |

---

## Testing

### Tipos de test

| Tipo | Cobertura objetivo | Herramienta |
|------|-------------------|-------------|
| Unitarios | {80%+} | pytest |
| Integracion | {Endpoints criticos} | pytest + httpx |
| E2E | {Flujos principales} | {Herramienta} |

### Ejecutar tests

```bash
# Todos los tests de la app
pytest tests/apps/{app_prefix}/

# Tests unitarios
pytest tests/apps/{app_prefix}/ -k "unit"

# Tests de integracion
pytest tests/apps/{app_prefix}/ -k "integration"
```

---

## Roadmap

| Fase | Funcionalidades | Estimacion |
|------|----------------|-----------|
| Fase 1 | {Lista de funcionalidades MVP} | {Semanas} |
| Fase 2 | {Funcionalidades adicionales} | {Semanas} |
| Fase 3 | {Funcionalidades avanzadas} | {Semanas} |

---

## Referencias

- [SavvyCore - Arquitectura](../../architecture/overview.md)
- [Convenciones API](../../api/README.md)
- [Convenciones BD](../../database/conventions.md)
- [Guia: Agregar una app](../../guides/adding-an-app.md)
