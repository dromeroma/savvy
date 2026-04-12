import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { appAccessGuard } from './core/guards/app-access.guard';
import { LayoutComponent } from './shell/layout/layout.component';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'auth',
    loadChildren: () =>
      import('./shell/auth/auth.routes').then((m) => m.AUTH_ROUTES),
  },
  {
    path: '',
    canActivate: [authGuard],
    component: LayoutComponent,
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./shell/dashboard/dashboard.component').then(
            (m) => m.DashboardComponent,
          ),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./shell/settings/organization-settings.component').then(
            (m) => m.OrganizationSettingsComponent,
          ),
      },
      {
        path: 'church',
        loadChildren: () =>
          import('./apps/church/church.routes').then((m) => m.CHURCH_ROUTES),
        data: { app: 'church' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'accounting',
        loadChildren: () =>
          import('./apps/accounting/accounting.routes').then((m) => m.ACCOUNTING_ROUTES),
        data: { app: 'accounting' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'pos',
        loadChildren: () =>
          import('./apps/pos/pos.routes').then((m) => m.POS_ROUTES),
        data: { app: 'pos' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'edu',
        loadChildren: () =>
          import('./apps/edu/edu.routes').then((m) => m.EDU_ROUTES),
        data: { app: 'edu' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'pay',
        loadChildren: () =>
          import('./apps/pay/pay.routes').then((m) => m.PAY_ROUTES),
        data: { app: 'pay' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'health',
        loadChildren: () =>
          import('./apps/health/health.routes').then((m) => m.HEALTH_ROUTES),
        data: { app: 'health' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'credit',
        loadChildren: () =>
          import('./apps/credit/credit.routes').then((m) => m.CREDIT_ROUTES),
        data: { app: 'credit' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'parking',
        loadChildren: () =>
          import('./apps/parking/parking.routes').then((m) => m.PARKING_ROUTES),
        data: { app: 'parking' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'crm',
        loadChildren: () =>
          import('./apps/crm/crm.routes').then((m) => m.CRM_ROUTES),
        data: { app: 'crm' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'condo',
        loadChildren: () =>
          import('./apps/condo/condo.routes').then((m) => m.CONDO_ROUTES),
        data: { app: 'condo' },
        canActivate: [appAccessGuard],
      },
      {
        path: 'family',
        loadChildren: () =>
          import('./apps/family/family.routes').then((m) => m.FAMILY_ROUTES),
        data: { app: 'family' },
        canActivate: [appAccessGuard],
      },
    ],
  },
  { path: '**', redirectTo: 'dashboard' },
];
