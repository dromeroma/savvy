import { Routes } from '@angular/router';
import { PayLayoutComponent } from './layout/pay-layout.component';

export const PAY_ROUTES: Routes = [
  { path: '', component: PayLayoutComponent, children: [
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    { path: 'dashboard', loadComponent: () => import('./dashboard/pay-dashboard.component').then(m => m.PayDashboardComponent) },
    { path: 'ledger', loadComponent: () => import('./ledger/ledger.component').then(m => m.PayLedgerComponent) },
    { path: 'transactions', loadComponent: () => import('./transactions/transactions.component').then(m => m.PayTransactionsComponent) },
    { path: 'wallets', loadComponent: () => import('./wallets/wallets.component').then(m => m.PayWalletsComponent) },
    { path: 'fees', loadComponent: () => import('./fees/fees.component').then(m => m.PayFeesComponent) },
    { path: 'payouts', loadComponent: () => import('./payouts/payouts.component').then(m => m.PayPayoutsComponent) },
    { path: 'subscriptions', loadComponent: () => import('./subscriptions/subscriptions.component').then(m => m.PaySubscriptionsComponent) },
  ]},
];
