import { Routes } from '@angular/router';
import { PortalLayoutComponent } from './layout/portal-layout.component';

export const PORTAL_ROUTES: Routes = [
  {
    path: '',
    redirectTo: 'water/dashboard',
    pathMatch: 'full',
  },
  {
    path: 'water',
    component: PortalLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./water/portal-dashboard.component').then(
            (m) => m.PortalDashboardComponent,
          ),
      },
      {
        path: 'invoices',
        loadComponent: () =>
          import('./water/portal-invoices.component').then(
            (m) => m.PortalInvoicesComponent,
          ),
      },
      {
        path: 'payments',
        loadComponent: () =>
          import('./water/portal-payments.component').then(
            (m) => m.PortalPaymentsComponent,
          ),
      },
      {
        path: 'consumption',
        loadComponent: () =>
          import('./water/portal-consumption.component').then(
            (m) => m.PortalConsumptionComponent,
          ),
      },
      {
        path: 'pqrs',
        loadComponent: () =>
          import('./water/portal-pqrs.component').then(
            (m) => m.PortalPqrsComponent,
          ),
      },
    ],
  },
];
