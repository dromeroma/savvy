import { Routes } from '@angular/router';
import { HrLayoutComponent } from './layout/hr-layout.component';

export const HR_ROUTES: Routes = [
  {
    path: '',
    component: HrLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/hr-dashboard.component').then((m) => m.HrDashboardComponent),
      },
      {
        path: 'employees',
        loadComponent: () =>
          import('./employees/employees-list.component').then((m) => m.HrEmployeesListComponent),
      },
      {
        path: 'employees/:id',
        loadComponent: () =>
          import('./employees/employee-detail.component').then((m) => m.HrEmployeeDetailComponent),
      },
      {
        path: 'departments',
        loadComponent: () =>
          import('./departments/departments.component').then((m) => m.HrDepartmentsComponent),
      },
      {
        path: 'positions',
        loadComponent: () =>
          import('./positions/positions.component').then((m) => m.HrPositionsComponent),
      },
      {
        path: 'contracts',
        loadComponent: () =>
          import('./contracts/contracts-list.component').then((m) => m.HrContractsListComponent),
      },
    ],
  },
];
