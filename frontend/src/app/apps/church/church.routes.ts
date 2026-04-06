import { Routes } from '@angular/router';
import { ChurchLayoutComponent } from './layout/church-layout.component';

export const CHURCH_ROUTES: Routes = [
  {
    path: '',
    component: ChurchLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/church-dashboard.component').then(
            (m) => m.ChurchDashboardComponent,
          ),
      },
      {
        path: 'congregants',
        loadComponent: () =>
          import('./members/member-list.component').then(
            (m) => m.MemberListComponent,
          ),
      },
      {
        path: 'members',
        redirectTo: 'congregants',
        pathMatch: 'full',
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
      {
        path: 'groups',
        loadComponent: () =>
          import('./groups/groups.component').then(
            (m) => m.GroupsComponent,
          ),
      },
      {
        path: 'visitors',
        loadComponent: () =>
          import('./visitors/visitors.component').then(
            (m) => m.VisitorsComponent,
          ),
      },
      {
        path: 'events',
        loadComponent: () =>
          import('./events/events.component').then(
            (m) => m.EventsComponent,
          ),
      },
      {
        path: 'attendance',
        loadComponent: () =>
          import('./attendance/attendance.component').then(
            (m) => m.AttendanceComponent,
          ),
      },
    ],
  },
];
