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
      {
        path: 'shifts',
        loadComponent: () =>
          import('./shifts/shifts.component').then((m) => m.HrShiftsComponent),
      },
      {
        path: 'attendance',
        loadComponent: () =>
          import('./attendance/attendance.component').then((m) => m.HrAttendanceComponent),
      },
      {
        path: 'vacations',
        loadComponent: () =>
          import('./vacations/vacations.component').then((m) => m.HrVacationsComponent),
      },
      {
        path: 'leaves',
        loadComponent: () =>
          import('./leaves/leaves.component').then((m) => m.HrLeavesComponent),
      },
      {
        path: 'payroll/concepts',
        loadComponent: () =>
          import('./payroll/concepts.component').then((m) => m.HrPayrollConceptsComponent),
      },
      {
        path: 'payroll/periods',
        loadComponent: () =>
          import('./payroll/periods-list.component').then((m) => m.HrPayrollPeriodsComponent),
      },
      {
        path: 'payroll/periods/:id',
        loadComponent: () =>
          import('./payroll/period-detail.component').then((m) => m.HrPayrollPeriodDetailComponent),
      },
      {
        path: 'evaluations',
        loadComponent: () =>
          import('./evaluations/evaluations.component').then((m) => m.HrEvaluationsComponent),
      },
      {
        path: 'training',
        loadComponent: () =>
          import('./training/training.component').then((m) => m.HrTrainingComponent),
      },
      {
        path: 'reports',
        loadComponent: () =>
          import('./reports/reports.component').then((m) => m.HrReportsComponent),
      },
      {
        path: 'liquidations',
        loadComponent: () =>
          import('./liquidations/liquidations-list.component').then((m) => m.HrLiquidationsListComponent),
      },
      {
        path: 'liquidations/new/:employeeId',
        loadComponent: () =>
          import('./liquidations/liquidation-wizard.component').then((m) => m.HrLiquidationWizardComponent),
      },
      {
        path: 'liquidations/:id',
        loadComponent: () =>
          import('./liquidations/liquidation-detail.component').then((m) => m.HrLiquidationDetailComponent),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./settings/hr-settings.component').then((m) => m.HrSettingsComponent),
      },
    ],
  },
];
