# Plan de Escalabilidad

---

## Resumen

Este documento describe como SavvyCore esta preparado para evolucionar desde un monolito modular hacia una arquitectura mas distribuida conforme crezca la demanda. El enfoque es **no sobre-ingeniear prematuramente**, sino asegurar que las decisiones actuales no bloqueen la evolucion futura.

---

## Hoja de ruta de escalabilidad

```
Fase 1 (Actual)          Fase 2                  Fase 3                 Fase 4
0-1K tenants             1K-10K tenants          10K-50K tenants        50K+ tenants

+----------------+       +----------------+      +----------------+     +------------------+
| Monolito       |       | Monolito +     |      | Microservicios |     | Multi-region +   |
| Modular        | ----> | Event Bus +    | ---> | Selectivos +   | --> | Sharding +       |
| 1 Servidor     |       | Cache Layer    |      | Message Queue  |     | CDN Global +     |
| PostgreSQL     |       | Read Replicas  |      | Kubernetes     |     | Edge Computing   |
+----------------+       +----------------+      +----------------+     +------------------+
```

---

## Fase 1: Monolito modular (actual)

### Arquitectura

- Un solo proceso Python/FastAPI que contiene todos los modulos.
- Un servidor PostgreSQL (Supabase).
- Redis para cache basico y rate limiting.
- Deploy en un solo servidor o contenedor.

### Capacidad estimada

| Metrica | Estimacion |
|---------|-----------|
| Tenants concurrentes | Hasta 1,000 |
| Requests por segundo | 500-1,000 RPS |
| Tamano de BD | Hasta 50 GB |
| Usuarios concurrentes | Hasta 10,000 |

### Estrategias de optimizacion en esta fase

1. **Indices de BD** apropiados en todas las tablas (especialmente `organization_id`).
2. **Connection pooling** con pool nativo de SQLAlchemy async o PgBouncer.
3. **Cache en Redis** para datos de lectura frecuente (perfiles, permisos, configuracion de org).
4. **Compresion gzip/brotli** en respuestas HTTP.
5. **Paginacion obligatoria** en todos los endpoints de listado.

---

## Fase 2: Cache agresivo + Event Bus

### Cuando migrar

- El tiempo de respuesta promedio supera 200ms.
- La BD tiene mas de 50GB y las queries se ralentizan.
- Se necesitan mas de 1,000 RPS sostenidos.

### Cambios arquitectonicos

```
+----------------+       +----------------+
| Monolito       |       | Redis Cluster  |
| Modular        |------>| (Cache Layer)  |
| (FastAPI)      |       +----------------+
|                |
|                |       +----------------+
|                |------>| Event Bus      |
|                |       | (Redis Streams |
|                |       |  o Celery)     |
|                |       +----------------+
|                |
|                |       +----------------+       +----------------+
|                |------>| PostgreSQL     |------>| Read Replica   |
|                |       | (Primary)      |       | (Lecturas)     |
+----------------+       +----------------+       +----------------+
```

### Event Bus interno

El event bus permite desacoplar modulos sin convertirlos en microservicios:

```
Modulo Auth                    Event Bus                  Modulo Notifications
+-----------+                 +----------+                +------------------+
| Login     |--- emite ----->| user.    |--- escucha --->| Enviar email de  |
| exitoso   |                | logged_in|                | login detectado  |
+-----------+                +----------+                +------------------+

Modulo Organization            Event Bus                  Modulo Audit
+-----------+                 +----------+                +------------------+
| Org       |--- emite ----->| org.     |--- escucha --->| Registrar en log |
| creada    |                | created  |                | de auditoria     |
+-----------+                +----------+                +------------------+
```

**Eventos planeados**:

| Evento | Productor | Consumidores potenciales |
|--------|-----------|--------------------------|
| `user.registered` | Auth | Notifications, Analytics |
| `user.logged_in` | Auth | Audit, Security |
| `org.created` | Organization | Notifications, Billing |
| `org.member_added` | Organization | Notifications, Audit |
| `org.member_removed` | Organization | Notifications, Audit |

### Read Replicas

- Separar lecturas de escrituras a nivel de repositorio.
- Queries de listado y reportes van a la replica.
- Escrituras y lecturas criticas (post-escritura) van al primary.

---

## Fase 3: Extraccion selectiva de microservicios

### Cuando migrar

- Un modulo especifico requiere escalar independientemente.
- El equipo crece y necesita ownership separado.
- Un modulo tiene requisitos de disponibilidad distintos.

### Candidatos a extraccion

| Modulo | Razon para extraer | Prioridad |
|--------|-------------------|-----------|
| Notifications | Alto volumen, puede ser asincrono, tolerante a fallos | Alta |
| Billing | Requisitos de compliance, integracion con Stripe | Alta |
| Reporting/Analytics | Queries pesadas que no deben afectar la BD principal | Media |
| File Storage | Manejo de archivos con requisitos de I/O distintos | Media |
| Auth | Si se necesita SSO federado o OAuth provider propio | Baja |

### Patron de extraccion

```
ANTES (Monolito):
+------------------------------------------+
| Monolito (FastAPI)                       |
| +------+ +--------+ +-----------+        |
| | Auth | | Billing| | Notific.  |        |
| +------+ +--------+ +-----------+        |
+------------------------------------------+

DESPUES (Hibrido):
+------------------------------------------+
| Monolito (reducido)                      |
| +------+ +--------+                     |
| | Auth | | Org    |                     |
| +------+ +--------+                     |
+------------------------------------------+
        |              |
        v              v
+-------------+  +-----------+
| Billing     |  | Notific.  |
| Service     |  | Service   |
| (separado)  |  | (separado)|
+-------------+  +-----------+
```

### Comunicacion entre servicios

| Tipo | Tecnologia | Uso |
|------|-----------|-----|
| Sincrono | HTTP/gRPC | Consultas que necesitan respuesta inmediata |
| Asincrono | Message Queue (RabbitMQ/SQS) | Eventos, tareas en background |
| Eventos | Event Bus (Kafka/Redis Streams) | Notificaciones entre servicios |

### Message Queue

Para tareas que no necesitan respuesta inmediata:

```
+----------+     +----------------+     +----------+
| Servicio |---->| Message Queue  |---->| Worker   |
| (produce)|     | (RabbitMQ/SQS) |     | (consume)|
+----------+     +----------------+     +----------+

Ejemplos:
- Enviar email de bienvenida (asincrono)
- Generar reporte PDF (heavy processing)
- Sincronizar con servicio externo (tolerante a fallos)
- Procesar webhook de Stripe (retry automatico)
```

---

## Fase 4: Multi-region y escala global

### Cuando migrar

- Usuarios en multiples continentes con requisitos de latencia.
- Regulaciones de residencia de datos (GDPR, etc.).
- Disponibilidad 99.99%+.

### Arquitectura multi-region

```
                    +-------------------+
                    | DNS / Load        |
                    | Balancer Global   |
                    | (Cloudflare/AWS)  |
                    +---------+---------+
                              |
              +---------------+---------------+
              |                               |
    +---------v---------+           +---------v---------+
    | Region: Americas  |           | Region: Europa    |
    |                   |           |                   |
    | +---------------+ |           | +---------------+ |
    | | App Servers   | |           | | App Servers   | |
    | | (Kubernetes)  | |           | | (Kubernetes)  | |
    | +-------+-------+ |           | +-------+-------+ |
    |         |         |           |         |         |
    | +-------v-------+ |           | +-------v-------+ |
    | | PostgreSQL    | |<-- Repl.-->| | PostgreSQL    | |
    | | (Primary)     | |           | | (Replica)     | |
    | +---------------+ |           | +---------------+ |
    |                   |           |                   |
    | +---------------+ |           | +---------------+ |
    | | Redis Cluster | |           | | Redis Cluster | |
    | +---------------+ |           | +---------------+ |
    +-------------------+           +-------------------+
```

### Estrategia de datos multi-region

- **Datos de organizacion**: Residentes en la region de la organizacion (configurable).
- **Datos de referencia** (planes, features): Replicados globalmente.
- **Sesiones/Cache**: Locales por region.

---

## Integracion con Inteligencia Artificial

### Oportunidades de IA en la plataforma

| Area | Aplicacion de IA | Fase |
|------|-----------------|------|
| **SavvyPOS** | Prediccion de demanda, recomendaciones de productos | Fase 2-3 |
| **SavvyLogistics** | Optimizacion de rutas, ETAs inteligentes | Fase 2-3 |
| **Plataforma** | Deteccion de anomalias, chatbot de soporte | Fase 2 |
| **Analytics** | Insights automaticos, reportes en lenguaje natural | Fase 3 |
| **Seguridad** | Deteccion de fraude, comportamiento anomalo | Fase 2 |

### Arquitectura para IA

```
+-------------------+      +-------------------+      +-------------------+
| SavvyCore         |      | AI Service Layer  |      | Modelos IA        |
|                   |      |                   |      |                   |
| Datos operativos  |----->| Feature Store     |----->| Prediccion de     |
| (PostgreSQL)      |      | (transformacion)  |      | demanda           |
|                   |      |                   |      |                   |
| Eventos del bus   |----->| Pipeline de datos |----->| Deteccion de      |
| (Redis Streams)   |      | (ETL)            |      | anomalias         |
|                   |      |                   |      |                   |
| API Gateway       |<-----| Inference API     |<-----| Modelos           |
| (respuesta al     |      | (predicciones)    |      | entrenados        |
|  cliente)         |      |                   |      |                   |
+-------------------+      +-------------------+      +-------------------+
```

### Preparacion actual para IA

Para no bloquear la integracion futura con IA:

1. **Eventos estructurados**: El event bus emite eventos con datos suficientes para entrenar modelos.
2. **IDs correlacionados**: Toda accion tiene trace_id para reconstruir flujos.
3. **Datos temporales**: `created_at` y `updated_at` en toda tabla permiten analisis temporal.
4. **API estandar**: Los modelos de IA se integraran como un servicio mas consumiendo la misma API.
5. **Stack Python**: El uso de Python facilita la integracion directa con librerias de ML/IA.

---

## Metricas clave para decidir cuando escalar

| Metrica | Umbral de alerta | Accion |
|---------|-----------------|--------|
| Tiempo de respuesta P95 | > 500ms | Optimizar queries, agregar cache |
| Tiempo de respuesta P99 | > 2s | Escalar horizontalmente |
| CPU del servidor | > 70% sostenido | Agregar instancias |
| Conexiones a BD | > 80% del pool | Agregar read replicas |
| Tamano de BD | > 80% del disco | Escalar almacenamiento, particionar |
| Error rate | > 1% | Investigar, circuit breaker |
| Queue depth | > 1000 mensajes pendientes | Agregar workers |

---

## Principio guia

> **"No resolver problemas que aun no tenemos, pero asegurar que podamos resolverlos cuando aparezcan."**

Cada decision de Fase 1 esta tomada pensando en que no bloquee las fases futuras. El codigo modular, los eventos, las interfaces bien definidas y las convenciones de datos son los cimientos que permiten evolucionar sin reescribir.

---

## Referencias

- [Arquitectura General](./overview.md)
- [Multi-tenancy](./multi-tenancy.md)
- [Stack Tecnologico](./tech-stack.md)
