import { Routes } from '@angular/router';
import { EduLayoutComponent } from './layout/edu-layout.component';

export const EDU_ROUTES: Routes = [
  {
    path: '',
    component: EduLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/edu-dashboard.component').then((m) => m.EduDashboardComponent),
      },
      {
        path: 'config',
        loadComponent: () =>
          import('./config/edu-config.component').then((m) => m.EduConfigComponent),
      },
      {
        path: 'programs',
        loadComponent: () =>
          import('./programs/programs.component').then((m) => m.ProgramsComponent),
      },
      {
        path: 'courses',
        loadComponent: () =>
          import('./courses/courses.component').then((m) => m.CoursesComponent),
      },
      {
        path: 'students',
        loadComponent: () =>
          import('./students/students.component').then((m) => m.StudentsComponent),
      },
      {
        path: 'teachers',
        loadComponent: () =>
          import('./teachers/teachers.component').then((m) => m.TeachersComponent),
      },
      {
        path: 'enrollment',
        loadComponent: () =>
          import('./enrollment/enrollment.component').then((m) => m.EnrollmentComponent),
      },
      {
        path: 'scheduling',
        loadComponent: () =>
          import('./scheduling/scheduling.component').then((m) => m.SchedulingComponent),
      },
      {
        path: 'attendance',
        loadComponent: () =>
          import('./attendance/edu-attendance.component').then((m) => m.EduAttendanceComponent),
      },
      {
        path: 'grading',
        loadComponent: () =>
          import('./grading/grading.component').then((m) => m.GradingComponent),
      },
      {
        path: 'finance',
        loadComponent: () =>
          import('./finance/edu-finance.component').then((m) => m.EduFinanceComponent),
      },
      {
        path: 'documents',
        loadComponent: () =>
          import('./documents/edu-documents.component').then((m) => m.EduDocumentsComponent),
      },
    ],
  },
];
