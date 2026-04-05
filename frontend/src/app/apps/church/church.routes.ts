import { Routes } from '@angular/router';
import { ChurchLayoutComponent } from './layout/church-layout.component';

export const CHURCH_ROUTES: Routes = [
  {
    path: '',
    component: ChurchLayoutComponent,
    children: [
      { path: '', redirectTo: 'members', pathMatch: 'full' },
      {
        path: 'members',
        loadComponent: () =>
          import('./members/member-list.component').then(
            (m) => m.MemberListComponent,
          ),
      },
      {
        path: 'finance',
        loadComponent: () =>
          import('./finance/finance-dashboard.component').then(
            (m) => m.FinanceDashboardComponent,
          ),
      },
      {
        path: 'reports',
        loadComponent: () =>
          import('./reports/reports-dashboard.component').then(
            (m) => m.ReportsDashboardComponent,
          ),
      },
    ],
  },
];
