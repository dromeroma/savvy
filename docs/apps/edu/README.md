# SavvyEdu — Plataforma de Gestion Educativa

## Tabla de Contenidos

1. [Proposito](#proposito)
2. [Principio Arquitectonico](#principio-arquitectonico)
3. [Modulos](#modulos)
4. [Configuracion Institucional](#configuracion-institucional)
5. [Estructura Academica](#estructura-academica)
6. [Estudiantes y Docentes](#estudiantes-y-docentes)
7. [Secciones y Matricula](#secciones-y-matricula)
8. [Horarios y Salones](#horarios-y-salones)
9. [Evaluaciones y Calificaciones](#evaluaciones-y-calificaciones)
10. [GradingEngine](#gradingengine)
11. [Asistencia](#asistencia)
12. [Finanzas Educativas](#finanzas-educativas)
13. [Documentos](#documentos)
14. [Consumo de Modulos Compartidos](#consumo-de-modulos-compartidos)
15. [Endpoints API](#endpoints-api)
16. [Diagrama de Relaciones](#diagrama-de-relaciones)

---

## Proposito

SavvyEdu es la app de **gestion academica integral** del ecosistema Savvy. Diseñada para servir:

- Colegios (K-12)
- Universidades
- Institutos tecnicos
- Academias online
- Instituciones hibridas

**Principio rector**: Todo es **configuration-driven**. No hay logica hardcodeada por tipo de institucion. Cada organizacion configura sus propios sistemas de calificacion, calendarios academicos, modelos de evaluacion y reglas de promocion.

### Usuarios objetivo

| Tipo           | Descripcion                                    |
|----------------|------------------------------------------------|
| Admin          | Configura la institucion, programas, periodos  |
| Coordinador    | Gestiona cursos, secciones, horarios           |
| Docente        | Califica, registra asistencia                  |
| Estudiante     | Consulta notas, horarios (futuro)              |
| Acudiente      | Consulta estado del estudiante (futuro)        |

---

## Principio Arquitectonico

```
+-------------------------------------------------------------------+
|  SavvyEdu NO tiene:                                               |
|  x Tabla de personas (usa people via PeopleService)               |
|  x Sistema financiero propio (usa SavvyFinance + Accounting)      |
|  x Sistema de auth propio (usa SavvyCore)                         |
|                                                                   |
|  SavvyEdu SI tiene:                                               |
|  + Config: grading systems, grade scales, period types, eval tpl  |
|  + Structure: periods, programs, courses, prerequisites, curricula|
|  + Students: edu_students, edu_guardians (extends people)         |
|  + Teachers: edu_teachers (extends people)                        |
|  + Enrollment: sections, enrollments, waitlists                   |
|  + Scheduling: rooms, schedules (with conflict detection)         |
|  + Grading: evaluations, grades, final_grades + GradingEngine     |
|  + Attendance: edu_attendance (per section/date)                  |
|  + Finance: tuition plans, charges, scholarships, awards          |
|  + Documents: templates, issued documents                         |
+-------------------------------------------------------------------+
```

---

## Modulos

| Modulo       | Tablas                                                    | Descripcion                           |
|--------------|-----------------------------------------------------------|---------------------------------------|
| Config       | `edu_grading_systems`, `edu_grade_scales`, `edu_academic_period_types`, `edu_evaluation_templates` | Configuracion institucional |
| Structure    | `edu_academic_periods`, `edu_programs`, `edu_courses`, `edu_prerequisites`, `edu_curriculum_versions` | Estructura academica |
| Students     | `edu_students`, `edu_guardians`                           | Datos academicos de estudiantes       |
| Teachers     | `edu_teachers`                                            | Datos laborales de docentes           |
| Enrollment   | `edu_sections`, `edu_enrollments`, `edu_waitlists`        | Secciones y matricula                 |
| Scheduling   | `edu_rooms`, `edu_schedules`                              | Horarios con deteccion de conflictos  |
| Grading      | `edu_evaluations`, `edu_grades`, `edu_final_grades`       | Calificaciones + GradingEngine        |
| Attendance   | `edu_attendance`                                          | Asistencia por seccion/fecha          |
| Finance      | `edu_tuition_plans`, `edu_student_charges`, `edu_scholarships`, `edu_scholarship_awards` | Finanzas educativas |
| Documents    | `edu_document_templates`, `edu_issued_documents`          | Certificados y documentos             |

**Total: 24 tablas propias**.

---

## Configuracion Institucional

### Sistemas de Calificacion (`edu_grading_systems` + `edu_grade_scales`)

Cada institucion define sus propios sistemas. Ejemplos:

| Institucion     | Tipo       | Min  | Max  | Aprobacion | Escalas              |
|-----------------|------------|------|------|------------|----------------------|
| Colegio Col.    | numeric    | 0    | 5    | 3.0        | 5.0=Excelente, 4.0=Bueno... |
| Universidad US  | letter     | 0    | 4    | 2.0        | A=4.0, B=3.0, C=2.0... |
| Instituto %     | percentage | 0    | 100  | 60         | 90-100=A, 80-89=B...  |

### Tipos de Periodo Academico (`edu_academic_period_types`)

| Codigo     | Nombre       | Duracion default |
|------------|-------------|------------------|
| semester   | Semestre     | 16 semanas       |
| trimester  | Trimestre    | 12 semanas       |
| quarter    | Cuatrimestre | 10 semanas       |
| annual     | Anual        | 40 semanas       |

### Plantillas de Evaluacion (`edu_evaluation_templates`)

Definen los componentes de evaluacion con sus pesos:

```json
{
  "name": "Modelo Estandar Universidad",
  "components": [
    {"name": "Parcial 1", "weight": 0.25, "type": "exam"},
    {"name": "Parcial 2", "weight": 0.25, "type": "exam"},
    {"name": "Trabajos",  "weight": 0.20, "type": "assignment"},
    {"name": "Final",     "weight": 0.30, "type": "exam"}
  ]
}
```

---

## Estructura Academica

### Programas (`edu_programs`)

Un programa vincula: grading system + evaluation template + scope (facultad/dept) + duracion + creditos.

### Cursos (`edu_courses`)

Materias/asignaturas con creditos, horas semanales, prerrequisitos. Pueden pertenecer a un programa o ser compartidos.

### Prerrequisitos (`edu_prerequisites`)

Relacion entre cursos con nota minima opcional. Se valida como **DAG** (grafo aciclico dirigido) para evitar ciclos.

### Versiones de Curricula (`edu_curriculum_versions`)

Malla curricular versionada por programa. Los estudiantes quedan vinculados a la version de su ingreso:

```json
{
  "version": "2026",
  "course_map": {
    "1": ["MAT101", "FIS101", "HUM101"],
    "2": ["MAT201", "FIS201", "PRG101"],
    "3": ["MAT301", "PRG201", "BD101"]
  }
}
```

---

## Estudiantes y Docentes

### Estudiantes (`edu_students`)

Extension de `people` con datos academicos:

- `student_code`: Codigo unico del estudiante
- `program_id`: Programa matriculado
- `curriculum_version_id`: Version de malla asignada
- `academic_status`: active, inactive, graduated, suspended, expelled
- `cumulative_gpa`: GPA acumulado (calculado por GradingEngine)
- `completed_credits`: Creditos aprobados acumulados

### Docentes (`edu_teachers`)

Extension de `people` con datos laborales:

- `employee_code`: Codigo de empleado
- `department_scope_id`: Departamento/facultad
- `specialization`: Area de especializacion
- `contract_type`: full_time, part_time, adjunct

### Acudientes (`edu_guardians`)

Vincula personas (acudientes) con estudiantes:

- `relationship`: parent, mother, father, guardian, tutor
- `is_primary`: Acudiente principal

---

## Secciones y Matricula

### Secciones (`edu_sections`)

Instancia de un curso en un periodo (ej: MAT101-A 2026-I):

- Vincula: curso + periodo + docente
- Control de capacidad: `capacity` vs `enrolled_count`
- Estados: open, closed, cancelled

### Matricula (`edu_enrollments`)

Inscripcion de estudiante en seccion:

- Estados: enrolled, dropped, completed, failed, withdrawn
- Si la seccion esta llena, el estudiante va a `edu_waitlists` con posicion

---

## Horarios y Salones

### Salones (`edu_rooms`)

Espacios fisicos con tipo (classroom, lab, auditorium, virtual) y capacidad.

### Horarios (`edu_schedules`)

Bloques horarios por seccion con deteccion de conflictos:

- **Conflicto de salon**: Dos secciones en el mismo salon a la misma hora
- **Conflicto de docente**: Un docente con dos secciones simultaneas

El `SchedulingService` rechaza asignaciones con conflicto.

---

## Evaluaciones y Calificaciones

### Evaluaciones (`edu_evaluations`)

Actividades evaluativas por seccion con peso y puntaje maximo.

### Calificaciones (`edu_grades`)

Nota individual por evaluacion con porcentaje calculado automaticamente.

### Calificaciones Finales (`edu_final_grades`)

Nota final consolidada por estudiante/seccion con:

- `numeric_grade`: Nota en la escala del grading system
- `letter_grade`: Letra segun grade_scales
- `gpa_points`: Puntos GPA segun escala
- `status`: approved / failed

---

## GradingEngine

El `GradingEngine` calcula notas finales automaticamente:

```
1. Obtener evaluaciones activas de la seccion
2. Para cada estudiante matriculado:
   a. Calcular promedio ponderado: SUM(percentage * weight) / SUM(weight)
   b. Convertir a escala del grading system del programa
   c. Buscar letra y GPA en grade_scales
   d. Determinar aprobado/reprobado segun passing_grade
3. Guardar/actualizar edu_final_grades
```

### Cadena de resolucion del grading system

```
Seccion -> Curso -> Programa -> programa.grading_system_id
                                       |
                                       v (si es null)
                        Org default grading system (is_default=true)
```

---

## Asistencia

Registro bulk por seccion y fecha con estados: present, absent, late, excused.

Resumen por seccion: total sesiones, presentes, ausentes, tasa de asistencia.

---

## Finanzas Educativas

### Planes de Matricula (`edu_tuition_plans`)

Plan por programa/periodo con monto total y cuotas (JSONB installments).

### Cobros (`edu_student_charges`)

Cargos individuales a estudiantes con saldo pendiente. Estados: pending, paid, overdue, cancelled.

### Becas (`edu_scholarships` + `edu_scholarship_awards`)

Definicion de becas (porcentaje o monto fijo) y asignacion a estudiantes especificos.

> Los pagos reales se registran via `SavvyFinance` con `app_code='edu'`.

---

## Documentos

### Plantillas (`edu_document_templates`)

Tipos: certificate, transcript, report_card, paz_y_salvo. Con HTML template y variables configurables.

### Documentos Emitidos (`edu_issued_documents`)

Documentos generados para un estudiante con los datos interpolados (JSONB).

---

## Consumo de Modulos Compartidos

| Responsabilidad         | Delegado a        | SavvyEdu solo tiene...                |
|------------------------|-------------------|---------------------------------------|
| Datos de personas      | SavvyPeople       | `person_id` + datos academicos        |
| Estructura jerarquica  | SavvyGroups       | `scope_id` para facultad/departamento |
| Ingresos y egresos     | SavvyFinance      | Planes, cobros, becas (metadata)      |
| Contabilidad           | SavvyAccounting   | Nada — delegado completamente         |

---

## Endpoints API

### Base URL: `/api/v1/edu/`

#### Config

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/config/grading-systems`               | Listar sistemas de calificacion |
| POST   | `/config/grading-systems`               | Crear sistema                   |
| GET    | `/config/period-types`                  | Listar tipos de periodo         |
| POST   | `/config/period-types`                  | Crear tipo                      |
| GET    | `/config/evaluation-templates`          | Listar plantillas de evaluacion |
| POST   | `/config/evaluation-templates`          | Crear plantilla                 |

#### Structure

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/structure/periods`                    | Listar periodos academicos      |
| POST   | `/structure/periods`                    | Crear periodo                   |
| GET    | `/structure/programs`                   | Listar programas                |
| POST   | `/structure/programs`                   | Crear programa                  |
| GET    | `/structure/courses`                    | Listar cursos (paginado)        |
| POST   | `/structure/courses`                    | Crear curso con prerrequisitos  |
| GET    | `/structure/programs/{id}/curriculum`   | Listar versiones de curricula   |
| POST   | `/structure/curriculum`                 | Crear version de curricula      |

#### Students & Teachers

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/students`                             | Listar estudiantes (paginado)   |
| POST   | `/students`                             | Crear estudiante                |
| PATCH  | `/students/{id}`                        | Actualizar estudiante           |
| GET    | `/students/{id}/guardians`              | Listar acudientes               |
| POST   | `/students/{id}/guardians`              | Agregar acudiente               |
| GET    | `/teachers`                             | Listar docentes (paginado)      |
| POST   | `/teachers`                             | Crear docente                   |
| PATCH  | `/teachers/{id}`                        | Actualizar docente              |

#### Enrollment

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/enrollment/sections`                  | Listar secciones                |
| POST   | `/enrollment/sections`                  | Crear seccion                   |
| POST   | `/enrollment/enroll`                    | Matricular (o waitlist si lleno)|
| GET    | `/enrollment/sections/{id}/students`    | Listar matriculados             |
| PATCH  | `/enrollment/enrollments/{id}`          | Actualizar estado matricula     |

#### Scheduling

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/scheduling/rooms`                     | Listar salones                  |
| POST   | `/scheduling/rooms`                     | Crear salon                     |
| GET    | `/scheduling/schedules`                 | Listar horarios                 |
| POST   | `/scheduling/schedules`                 | Asignar horario (con conflicto) |
| DELETE | `/scheduling/schedules/{id}`            | Eliminar horario                |

#### Grading

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/grading/evaluations?section_id=`      | Listar evaluaciones             |
| POST   | `/grading/evaluations`                  | Crear evaluacion                |
| POST   | `/grading/grades/bulk`                  | Registrar notas en lote         |
| GET    | `/grading/grades?evaluation_id=`        | Listar notas                    |
| POST   | `/grading/final-grades/{section_id}/calculate` | Calcular notas finales   |
| GET    | `/grading/final-grades/{section_id}`    | Listar notas finales            |

#### Attendance

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| POST   | `/attendance/bulk`                      | Registrar asistencia en lote    |
| GET    | `/attendance?section_id=&date=`         | Listar asistencia               |
| GET    | `/attendance/summary/{section_id}`      | Resumen de asistencia           |

#### Finance

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/finance/tuition-plans`                | Listar planes de matricula      |
| POST   | `/finance/tuition-plans`                | Crear plan                      |
| GET    | `/finance/charges`                      | Listar cobros                   |
| POST   | `/finance/charges`                      | Crear cobro                     |
| GET    | `/finance/scholarships`                 | Listar becas                    |
| POST   | `/finance/scholarships`                 | Crear beca                      |
| POST   | `/finance/scholarships/award`           | Otorgar beca a estudiante       |

#### Documents

| Metodo | Ruta                                    | Descripcion                     |
|--------|-----------------------------------------|---------------------------------|
| GET    | `/documents/templates`                  | Listar plantillas               |
| POST   | `/documents/templates`                  | Crear plantilla                 |
| GET    | `/documents/issued`                     | Listar documentos emitidos      |
| POST   | `/documents/issue`                      | Emitir documento                |

---

## Diagrama de Relaciones

```
+------------------------------------------------------------------------+
|                    SAVVYEDU - DIAGRAMA DE ENTIDADES                     |
+------------------------------------------------------------------------+
|                                                                        |
|  [Config Layer]                                                        |
|  +------------------+  +---------------------+  +------------------+   |
|  | edu_grading_     |  | edu_academic_period_ |  | edu_evaluation_  |   |
|  | systems          |  | types                |  | templates        |   |
|  | + grade_scales   |  +----------+----------+  +--------+---------+   |
|  +--------+---------+             |                       |            |
|           |                       v                       |            |
|  [Structure Layer]     +------------------+               |            |
|  +------------+        | edu_academic_    |               |            |
|  | edu_       |        | periods          |               |            |
|  | programs   |<-------+------------------+               |            |
|  | (grading,  |                                           |            |
|  |  eval_tpl) |        +------------------+               |            |
|  +-----+------+------->| edu_courses      |               |            |
|        |               | + prerequisites  |               |            |
|        |               +--------+---------+               |            |
|        |                        |                         |            |
|        v                        v                         |            |
|  +------------------+  +------------------+               |            |
|  | edu_curriculum_  |  | edu_sections     |<--------------+            |
|  | versions         |  | (course+period+  |                            |
|  +------------------+  |  teacher)        |                            |
|                        +--------+---------+                            |
|  [People Layer]                 |                                      |
|  +--------------+      +-------v--------+     +------------------+     |
|  | edu_students |<-----| edu_enrollments|     | edu_schedules    |     |
|  | (person_id)  |      | + waitlists    |     | (section+room+   |     |
|  | + guardians  |      +----------------+     |  day+time)       |     |
|  +--------------+               |             +------------------+     |
|  +--------------+               |             +------------------+     |
|  | edu_teachers |               |             | edu_rooms        |     |
|  | (person_id)  |               |             +------------------+     |
|  +--------------+               v                                      |
|                        +------------------+                            |
|  [Grading Layer]       | edu_evaluations  |                            |
|                        +--------+---------+                            |
|                                 |                                      |
|                        +--------v---------+                            |
|                        | edu_grades       |                            |
|                        +--------+---------+                            |
|                                 |                                      |
|                        +--------v---------+                            |
|                        | edu_final_grades |                            |
|                        +------------------+                            |
|                                                                        |
|  [Finance Layer]                      [Documents Layer]                |
|  +------------------+                 +---------------------+          |
|  | edu_tuition_plans|                 | edu_document_       |          |
|  | + charges        |                 | templates           |          |
|  | + scholarships   |                 | + issued_documents  |          |
|  | + awards         |                 +---------------------+          |
|  +------------------+                                                  |
|                                                                        |
|  Modulos compartidos: SavvyPeople, SavvyGroups, SavvyFinance,         |
|                       SavvyAccounting                                  |
+------------------------------------------------------------------------+
```

---

> **Principio clave**: SavvyEdu es configuration-driven. Cada institucion define su propio sistema de calificacion, calendario y evaluacion. El GradingEngine aplica las reglas configuradas, no logica hardcodeada.
