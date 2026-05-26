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
    ],
  },
];
