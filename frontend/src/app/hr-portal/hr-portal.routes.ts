import { Routes } from '@angular/router';

export const HR_PORTAL_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./portal-login.component').then((m) => m.HrPortalLoginComponent),
  },
  {
    path: 'home',
    loadComponent: () =>
      import('./portal-home.component').then((m) => m.HrPortalHomeComponent),
  },
];
