import { Routes } from '@angular/router';
import { CondoLayoutComponent } from './layout/condo-layout.component';

export const CONDO_ROUTES: Routes = [
  { path: '', component: CondoLayoutComponent, children: [
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    { path: 'dashboard', loadComponent: () => import('./dashboard/condo-dashboard.component').then(m => m.CondoDashboardComponent) },
    { path: 'properties', loadComponent: () => import('./properties/properties.component').then(m => m.CondoPropertiesComponent) },
    { path: 'residents', loadComponent: () => import('./residents/residents.component').then(m => m.CondoResidentsComponent) },
    { path: 'fees', loadComponent: () => import('./fees/fees.component').then(m => m.CondoFeesComponent) },
    { path: 'areas', loadComponent: () => import('./areas/areas.component').then(m => m.CondoAreasComponent) },
    { path: 'maintenance', loadComponent: () => import('./maintenance/maintenance.component').then(m => m.CondoMaintenanceComponent) },
    { path: 'governance', loadComponent: () => import('./governance/governance.component').then(m => m.CondoGovernanceComponent) },
    { path: 'announcements', loadComponent: () => import('./communication/announcements.component').then(m => m.CondoAnnouncementsComponent) },
  ]},
];
