import { Routes } from '@angular/router';
import { FamilyLayoutComponent } from './layout/family-layout.component';

export const FAMILY_ROUTES: Routes = [
  {
    path: '',
    component: FamilyLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/family-dashboard.component').then((m) => m.FamilyDashboardComponent),
      },
      {
        path: 'list',
        loadComponent: () =>
          import('./families/families.component').then((m) => m.FamiliesComponent),
      },
      {
        path: ':id',
        loadComponent: () =>
          import('./detail/family-detail.component').then((m) => m.FamilyDetailComponent),
      },
      {
        path: ':id/genogram',
        loadComponent: () =>
          import('./genogram/genogram.component').then((m) => m.GenogramComponent),
      },
    ],
  },
];
