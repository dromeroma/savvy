import { Routes } from '@angular/router';
import { WaterLayoutComponent } from './layout/water-layout.component';

export const WATER_ROUTES: Routes = [
  {
    path: '',
    component: WaterLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/water-dashboard.component').then(
            (m) => m.WaterDashboardComponent,
          ),
      },
      {
        path: 'subscribers',
        loadComponent: () =>
          import('./subscribers/subscribers-list.component').then(
            (m) => m.SubscribersListComponent,
          ),
      },
      {
        path: 'meters',
        loadComponent: () =>
          import('./meters/meters-list.component').then(
            (m) => m.MetersListComponent,
          ),
      },
      {
        path: 'tariffs',
        loadComponent: () =>
          import('./tariffs/tariffs-list.component').then(
            (m) => m.TariffsListComponent,
          ),
      },
      {
        path: 'consumptions',
        loadComponent: () =>
          import('./consumptions/consumptions-list.component').then(
            (m) => m.ConsumptionsListComponent,
          ),
      },
      {
        path: 'invoices',
        loadComponent: () =>
          import('./invoices/invoices-list.component').then(
            (m) => m.InvoicesListComponent,
          ),
      },
      {
        path: 'payments',
        loadComponent: () =>
          import('./payments/payments-list.component').then(
            (m) => m.PaymentsListComponent,
          ),
      },
    ],
  },
];
