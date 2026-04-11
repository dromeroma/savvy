import { Routes } from '@angular/router';
import { CreditLayoutComponent } from './layout/credit-layout.component';

export const CREDIT_ROUTES: Routes = [
  {
    path: '',
    component: CreditLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/credit-dashboard.component').then((m) => m.CreditDashboardComponent),
      },
      {
        path: 'products',
        loadComponent: () =>
          import('./products/credit-products.component').then((m) => m.CreditProductsComponent),
      },
      {
        path: 'borrowers',
        loadComponent: () =>
          import('./borrowers/borrowers.component').then((m) => m.BorrowersComponent),
      },
      {
        path: 'applications',
        loadComponent: () =>
          import('./applications/applications.component').then((m) => m.ApplicationsComponent),
      },
      {
        path: 'loans',
        loadComponent: () =>
          import('./loans/loans.component').then((m) => m.LoansComponent),
      },
      {
        path: 'loans/:id',
        loadComponent: () =>
          import('./loans/loan-detail.component').then((m) => m.LoanDetailComponent),
      },
      {
        path: 'payments',
        loadComponent: () =>
          import('./payments/payments.component').then((m) => m.PaymentsComponent),
      },
    ],
  },
];
