import { Routes } from '@angular/router';

export const MEMORIAL_PORTAL_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./portal-login.component').then((m) => m.MemorialPortalLoginComponent),
  },
  {
    path: 'home',
    loadComponent: () =>
      import('./portal-home.component').then((m) => m.MemorialPortalHomeComponent),
  },
];
