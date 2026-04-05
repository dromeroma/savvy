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
    ],
  },
  { path: '**', redirectTo: 'dashboard' },
];
