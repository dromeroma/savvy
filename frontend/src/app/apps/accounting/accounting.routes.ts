import { Routes } from '@angular/router';

export const ACCOUNTING_ROUTES: Routes = [
  {
    path: '',
    redirectTo: 'chart',
    pathMatch: 'full',
  },
  {
    path: 'chart',
    loadComponent: () =>
      import('./chart-of-accounts.component').then(m => m.ChartOfAccountsComponent),
  },
  {
    path: 'journal',
    loadComponent: () =>
      import('./journal-entries.component').then(m => m.JournalEntriesComponent),
  },
  {
    path: 'periods',
    loadComponent: () =>
      import('./fiscal-periods.component').then(m => m.FiscalPeriodsComponent),
  },
  {
    path: 'income-statement',
    loadComponent: () =>
      import('./income-statement.component').then(m => m.IncomeStatementComponent),
  },
  {
    path: 'balance-sheet',
    loadComponent: () =>
      import('./balance-sheet.component').then(m => m.BalanceSheetComponent),
  },
];
