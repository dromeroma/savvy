import { Routes } from '@angular/router';
import { HealthLayoutComponent } from './layout/health-layout.component';

export const HEALTH_ROUTES: Routes = [
  { path: '', component: HealthLayoutComponent, children: [
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    { path: 'dashboard', loadComponent: () => import('./dashboard/health-dashboard.component').then(m => m.HealthDashboardComponent) },
    { path: 'patients', loadComponent: () => import('./patients/patients.component').then(m => m.HealthPatientsComponent) },
    { path: 'providers', loadComponent: () => import('./providers/providers.component').then(m => m.HealthProvidersComponent) },
    { path: 'appointments', loadComponent: () => import('./appointments/appointments.component').then(m => m.HealthAppointmentsComponent) },
    { path: 'clinical', loadComponent: () => import('./clinical/clinical.component').then(m => m.HealthClinicalComponent) },
    { path: 'services', loadComponent: () => import('./services/health-services.component').then(m => m.HealthServicesListComponent) },
  ]},
];
