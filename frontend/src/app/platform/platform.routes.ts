import { Routes } from '@angular/router';
import { PlatformLayoutComponent } from './layout/platform-layout.component';

export const PLATFORM_ROUTES: Routes = [
  {
    path: '',
    component: PlatformLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/platform-dashboard.component').then(
            (m) => m.PlatformDashboardComponent,
          ),
      },
      {
        path: 'organizations',
        loadComponent: () =>
          import('./organizations/organizations-list.component').then(
            (m) => m.OrganizationsListComponent,
          ),
      },
      {
        path: 'organizations/new',
        loadComponent: () =>
          import('./organizations/organization-create.component').then(
            (m) => m.OrganizationCreateComponent,
          ),
      },
      {
        path: 'organizations/:id',
        loadComponent: () =>
          import('./organizations/organization-detail.component').then(
            (m) => m.OrganizationDetailComponent,
          ),
      },
      {
        path: 'plans',
        loadComponent: () =>
          import('./plans/plans-list.component').then((m) => m.PlansListComponent),
      },
      {
        path: 'subscriptions',
        loadComponent: () =>
          import('./subscriptions/subscriptions-list.component').then(
            (m) => m.SubscriptionsListComponent,
          ),
      },
      {
        path: 'users',
        loadComponent: () =>
          import('./users/platform-users-list.component').then(
            (m) => m.PlatformUsersListComponent,
          ),
      },
      {
        path: 'audit',
        loadComponent: () =>
          import('./audit/audit-log.component').then((m) => m.AuditLogComponent),
      },
    ],
  },
];
