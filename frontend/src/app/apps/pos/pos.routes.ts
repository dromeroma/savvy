import { Routes } from '@angular/router';
import { PosLayoutComponent } from './layout/pos-layout.component';

export const POS_ROUTES: Routes = [
  { path: '', component: PosLayoutComponent, children: [
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    { path: 'dashboard', loadComponent: () => import('./dashboard/pos-dashboard.component').then(m => m.PosDashboardComponent) },
    { path: 'terminal', loadComponent: () => import('./pos-terminal/pos-terminal.component').then(m => m.PosTerminalComponent) },
    { path: 'products', loadComponent: () => import('./products/products.component').then(m => m.PosProductsComponent) },
    { path: 'inventory', loadComponent: () => import('./inventory/inventory.component').then(m => m.PosInventoryComponent) },
    { path: 'sales', loadComponent: () => import('./sales/sales.component').then(m => m.PosSalesComponent) },
    { path: 'registers', loadComponent: () => import('./registers/registers.component').then(m => m.PosRegistersComponent) },
    { path: 'locations', loadComponent: () => import('./locations/locations.component').then(m => m.PosLocationsComponent) },
  ]},
];
