import { Routes } from '@angular/router';
import { ParkingLayoutComponent } from './layout/parking-layout.component';

export const PARKING_ROUTES: Routes = [
  {
    path: '', component: ParkingLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', loadComponent: () => import('./dashboard/parking-dashboard.component').then(m => m.ParkingDashboardComponent) },
      { path: 'infrastructure', loadComponent: () => import('./infrastructure/infrastructure.component').then(m => m.InfrastructureComponent) },
      { path: 'vehicles', loadComponent: () => import('./vehicles/vehicles.component').then(m => m.ParkingVehiclesComponent) },
      { path: 'sessions', loadComponent: () => import('./sessions/sessions.component').then(m => m.SessionsComponent) },
      { path: 'pricing', loadComponent: () => import('./pricing/pricing.component').then(m => m.ParkingPricingComponent) },
      { path: 'services', loadComponent: () => import('./services/parking-services.component').then(m => m.ParkingServicesComponent) },
    ],
  },
];
