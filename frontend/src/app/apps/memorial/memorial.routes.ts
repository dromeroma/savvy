import { Routes } from '@angular/router';
import { MemorialLayoutComponent } from './layout/memorial-layout.component';

export const MEMORIAL_ROUTES: Routes = [
  {
    path: '',
    component: MemorialLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/memorial-dashboard.component').then(
            (m) => m.MemorialDashboardComponent,
          ),
      },
      {
        path: 'services',
        loadComponent: () =>
          import('./services/services-list.component').then(
            (m) => m.MemorialServicesListComponent,
          ),
      },
      {
        path: 'services/:id',
        loadComponent: () =>
          import('./services/service-detail.component').then(
            (m) => m.MemorialServiceDetailComponent,
          ),
      },
      {
        path: 'plans',
        loadComponent: () =>
          import('./plans/plans-list.component').then(
            (m) => m.MemorialPlansListComponent,
          ),
      },
      {
        path: 'contracts',
        loadComponent: () =>
          import('./contracts/contracts-list.component').then(
            (m) => m.MemorialContractsListComponent,
          ),
      },
      {
        path: 'contracts/:id',
        loadComponent: () =>
          import('./contracts/contract-detail.component').then(
            (m) => m.MemorialContractDetailComponent,
          ),
      },
      {
        path: 'invoices',
        loadComponent: () =>
          import('./invoices/invoices-list.component').then(
            (m) => m.MemorialInvoicesListComponent,
          ),
      },
      {
        path: 'payments',
        loadComponent: () =>
          import('./payments/payments-list.component').then(
            (m) => m.MemorialPaymentsListComponent,
          ),
      },
      {
        path: 'cartera',
        loadComponent: () =>
          import('./cartera/cartera.component').then(
            (m) => m.MemorialCarteraComponent,
          ),
      },
      {
        path: 'logistics',
        loadComponent: () =>
          import('./logistics/logistics.component').then(
            (m) => m.MemorialLogisticsComponent,
          ),
      },
      {
        path: 'transfers',
        loadComponent: () =>
          import('./transfers/transfers-list.component').then(
            (m) => m.MemorialTransfersListComponent,
          ),
      },
    ],
  },
];
