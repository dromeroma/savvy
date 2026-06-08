# Savvy AI OS — Estrategia de Evolución Inteligente

> Documento de estrategia fusionada (visión de producto + arquitectura de ingeniería).
> Fuente: síntesis del análisis estratégico de Deimer + plan de arquitectura.
> Estado: **vivo** — el progreso se rastrea en [`savvy-ai-roadmap.md`](./savvy-ai-roadmap.md).
> Creado: 2026-06-08.

---

## 1. La meta

No es "un ERP con IA". Es convertir Savvy en un **AI Operating System**: un
ecosistema donde la IA interpreta documentos, automatiza procesos, entiende
imágenes/cámaras, predice comportamientos, recomienda acciones y permite
interacción conversacional — **conectando los 13 módulos entre sí**.

**Principio rector único:** **Zero-Form** — el formulario es el último recurso,
no el primero. Cada formulario eliminado, cada clic reducido y cada proceso
automatizado hace que Savvy se sienta premium, moderno y poderoso.

**Norte estético:** Notion · Linear · Stripe · Arc. Minimalista, elegante,
extremadamente fácil. Menos "sistema administrativo", más "herramienta que la
gente ama usar".

---

## 2. El cambio de experiencia

| Antes (hoy) | Después (Savvy AI OS) |
|---|---|
| 1. El usuario entra | 1. El usuario sube evidencia (imagen, PDF, audio, texto) |
| 2. Llena formularios | 2. Savvy entiende automáticamente |
| 3. Guarda datos | 3. Savvy **propone** acciones |
| 4. Busca manualmente | 4. El usuario **confirma** |
| 5. Genera reportes | 5. Todo se ejecuta y se conecta solo |

---

## 3. La superficie física: **Savvy Command** (⌘K, la barra mágica)

Una sola caja, presente en toda la plataforma (estilo ⌘K de Linear/Arc, pero
IA-nativa). El usuario puede:

- **escribir** lenguaje natural → *"registra una compra de $200k a Distribuidora XYZ"*
- **arrastrar un archivo** → factura / cédula / contrato → se extrae y prellena
- **pegar** texto o imagen
- **dictar** por voz 🎙️
- **buscar** cualquier cosa cross-módulo → *"todo de Carlos"*

Savvy detecta intención + módulo, **propone la acción en una tarjeta** y el
usuario confirma. Esto fusiona en UNA experiencia el Copilot + OCR + Búsqueda
Universal + Formularios Inteligentes. Es el momento "wow".

---

## 4. Arquitectura conceptual (4 niveles)

1. **Automatización inteligente** — autollenado, registros automáticos,
   actualización de inventario, clasificación.
2. **Interpretación inteligente** — imágenes, PDFs, facturas, cédulas,
   contratos, placas, voz, conversaciones.
3. **Inteligencia predictiva** — stock por agotarse, productos estancados,
   riesgo financiero, anomalías, oportunidades de venta, vencimientos.
4. **Interacción conversacional** — escribir o hablar para consultar y ejecutar.

---

## 5. Las 3 ideas-moat (lo no copiable)

### 5.1 🕸️ Savvy Graph — inteligencia cruzada entre apps
La misma persona es cliente de parking + comprador en POS + afiliado en Memorial
+ paciente en Health. Ningún competidor puede hacerlo porque son apps sueltas.
Savvy tiene todo en **una BD multi-tenant compartida** → un grafo de entidades
que conecta a "Carlos" en los 13 módulos. Habilita: *"Carlos debe $200k en
parking pero es VIP en POS — ofrécele un plan"*. **Magia que solo Savvy puede hacer.**

### 5.2 🃏 Confirmable Actions — el patrón UX que da confianza
Ni formulario ni chat: una **tarjeta** *"Savvy entendió esto → [Confirmar]
[Editar] [Descartar]"*, reusando los componentes bento. El human-in-the-loop
deja de ser fricción y se vuelve una primitiva visual elegante y consistente.
Resuelve el problema #1 de adoptar IA en pymes LATAM: la desconfianza.

### 5.3 ☀️ Savvy Briefing — el resumen proactivo
El dashboard narrativo pero **empujado, no consultado**. Cada mañana, según el
rol: *"Buenos días. Ayer vendiste $1.2M (▲12%). 3 productos lácteos vencen esta
semana — sugiero promo. Parking al 87%. Cartera vencida +$400k — 2 clientes."*
Llega por la app o WhatsApp. Es el "standup diario" escrito por IA.

---

## 6. Capacidades núcleo (horizontales, las usan todas las apps)

| Capacidad | Qué hace |
|---|---|
| **Savvy Command** ⭐ | Barra mágica ⌘K: texto/archivo/voz/búsqueda → acción propuesta |
| **SavvyScan** | Documento/imagen → datos estructurados → prellena formulario |
| **SavvyCopilot** | Chat por app: NL → consulta o ejecuta (Tool Use sobre la API existente) |
| **SavvySuggest** | Autocompletado, detección de duplicados, validación en vivo |
| **SavvyInsights** | Anomalías + predicciones + narrativa sobre los dashboards bento |
| **SavvyFlow** | Workflows no-code (estilo Zapier/n8n) + agentes en background |
| **SavvyVision** | Cámaras/IoT: placas, entrada/salida, incidentes (parking) |
| **SavvyVoice** | Dictado voz→texto (Whisper) alimentando Command/Scan |
| **Savvy Briefing** | Resumen proactivo diario por rol (app + WhatsApp) |
| **Savvy Graph** | Entidad unificada cross-app (el moat) |

---

## 7. Decisiones técnicas (opinionadas, anti-sobreingeniería)

**Regla de oro:** empezar con **un proveedor, una BD**. Agregar vendors solo
cuando un caso real lo exija. Velocidad > arquitectura perfecta.

| Área | Decisión | Por qué |
|---|---|---|
| LLM | **Claude** (interfaz abstracta para cambiar luego) | Modelo de casa. Visión + OCR + structured output en uno. Multi-proveedor = 3× complejidad. |
| Tiers | **Haiku 4.5** (clasificación/validación) · **Sonnet 4.6** (extracción/copilot) · **Opus 4.8** (insights/agentes) | Control de costo por tarea. |
| OCR | **Claude Vision** (90% de casos); DocAI dedicado solo si llega alto volumen de formularios fijos | No se necesita vendor de OCR aparte al inicio. |
| Vector DB | **pgvector en Supabase** (ya existe) | Cero infra nueva. Qdrant/Weaviate solo a escala de millones. |
| Grafo | Postgres + tablas de enlace al inicio; FalkorDB/grafo dedicado más adelante | El Savvy Graph arranca como vistas/joins. |
| Visión (placas) | **YOLO/OpenCV** (ANPR) — no LLM | Las placas requieren modelo especializado. |
| Voz | **Whisper** | Estándar. |
| Herramientas del agente | **Los ~760 endpoints existentes** vía Tool Use | El 80% del Copilot ya está construido. |

---

## 8. Disciplinas no negociables (multi-tenant)

- **Human-in-the-loop**: la IA *propone*, el usuario *confirma* antes de escribir
  en BD. Nunca auto-guardar sin revisión (al menos en fases tempranas).
- **Audit log de IA**: qué se extrajo, de qué documento, qué modelo, quién
  confirmó, cuánto costó.
- **Aislamiento por tenant**: el contexto de IA de una org jamás toca otra (RLS).
- **Medición de uso por org**: cuota de IA por organización → habilita el modelo
  de negocio.
- **PII**: marcar campos sensibles; opción de no enviar ciertos datos al modelo.

---

## 9. Modelo de negocio

**"Savvy AI" como tier premium medido.** Cada org tiene cuota de IA; los planes
Pro/Enterprise la amplían. La IA deja de ser un costo y se vuelve la principal
palanca de **upsell** (como Notion AI / Stripe). El medidor de uso de la Fase 0
es la base de la facturación.

---

## 10. Catálogo de funcionalidades por aplicativo

| App | Funcionalidad IA estrella |
|---|---|
| **POS** | Foto de factura de compra → actualiza stock, ajusta costos/precios, registra inventario. Sugiere promos (estancado + alta rotación). Alerta de vencimientos → descuento. Predicción de demanda. |
| **Parking** | Cámara lee placa (entra/sale), tarifa automática. Detecta carro sucio → ofrece lavado → notifica al listo. Predice ocupación. |
| **Memorial** | Cédula → prellena contrato. Copilot de vencimientos. Predice mora. Redacta comunicados/condolencias. |
| **HR** | Hoja de vida → crea empleado. Liquidación explicada. Predice rotación. Resume evaluaciones 360°. |
| **Health** | Consulta por voz → historia clínica. Resume historial. Sugiere CIE-10. |
| **Credit** | Documentos → perfil de riesgo. Scoring asistido. Mora temprana. |
| **CRM** | Transcribe/resume llamadas. Redacta correos. Prioriza leads. |
| **Edu** | Genera/califica evaluaciones. Boletines narrativos. Estudiantes en riesgo. |
| **Water** | Foto del medidor → lectura. Detecta consumos anómalos (fugas). Proyecta facturación. |
| **Church** | Transcribe/resume prédicas. Segmenta congregación. Comunicados. |
| **Condo** | Clasifica/enruta PQRs por NL. Concilia pagos desde comprobantes. |
| **Accounting/Pay** | Factura → asiento contable sugerido. Conciliación bancaria asistida. |

---

## 11. Hoja de ruta (fases)

Detalle, criterios de aceptación y checkboxes vivos en
[`savvy-ai-roadmap.md`](./savvy-ai-roadmap.md).

- **Fase 0 — Cimiento**: módulo `savvy_ai` (cliente Claude, tiering, jobs async,
  medición de uso, audit log, patrón Confirmable Action).
- **Fase 1 — WOW**: Savvy Command (⌘K) + SavvyScan, arrancando con **factura→inventario en POS**.
- **Fase 2 — Copilot + Briefing + Búsqueda Universal** + Savvy Graph básico.
- **Fase 3 — Predictivo + Workflows visuales** (recomendaciones, riesgo, no-code).
- **Fase 4 — Voz + WhatsApp + Vision (Parking) + Agentes**.

**Filosofía de arranque:** no 10 cosas a medias. Un flujo perfecto
(factura→inventario) que demuestra toda la visión, sobre un cimiento sólido.
