# SavvyHealth — Gestion Clinica Integral

## Proposito

SavvyHealth es la app de **gestion de clinicas y consultorios** del ecosistema Savvy. Soporta historias clinicas estructuradas (EHR), citas, prescripciones, laboratorio y facturacion.

## Entidades (12 tablas)

| Tabla | Descripcion |
|-------|-------------|
| `health_patients` | Pacientes (extends People) con sangre, alergias, condiciones cronicas |
| `health_insurance` | Informacion de seguro/EPS del paciente |
| `health_providers` | Medicos/especialistas con licencia, horario, duracion consulta |
| `health_services` | Catalogo de servicios con precio y duracion |
| `health_appointments` | Citas con lifecycle completo (6 estados) |
| `health_clinical_records` | Historia clinica SOAP + clinical_data JSONB |
| `health_vitals` | Signos vitales por consulta (PA, FC, temp, SpO2, peso, talla) |
| `health_diagnoses` | Diagnosticos CIE-10 con tipo (primary, secondary, differential) |
| `health_prescriptions` | Prescripciones con medicamento, dosis, frecuencia, duracion |
| `health_lab_orders` | Ordenes de laboratorio con urgencia y resultados JSONB |
| `health_treatment_plans` | Planes de tratamiento con objetivos JSONB |
| `health_documents` | Certificados, remisiones, incapacidades |

## Clinical Record (SOAP)

Estructura SOAP: chief_complaint, present_illness, physical_exam, assessment, plan + clinical_data JSONB para extensibilidad.

## Appointment Lifecycle

scheduled -> confirmed -> in_progress -> completed / cancelled / no_show

## Frontend (7 vistas)

Dashboard 6 KPIs, pacientes, profesionales, citas con completar, historias clinicas SOAP, servicios.

## Endpoints API

Base: `/api/v1/health/`

Patients: GET/POST `/patients`, GET/PATCH `/{id}`, POST `/patients/insurance`
Providers: GET/POST `/providers`
Appointments: GET/POST `/appointments`, PATCH `/{id}`
Clinical: GET/POST `/clinical/records`, POST `/clinical/vitals`, POST/GET `/clinical/diagnoses`, POST/GET `/clinical/prescriptions`, POST/GET `/clinical/lab-orders`
Services: GET/POST `/services`
Dashboard: GET `/dashboard/kpis`
