import { Routes } from '@angular/router';
import { CrmLayoutComponent } from './layout/crm-layout.component';

export const CRM_ROUTES: Routes = [
  {
    path: '',
    component: CrmLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', loadComponent: () => import('./dashboard/crm-dashboard.component').then(m => m.CrmDashboardComponent) },
      { path: 'contacts', loadComponent: () => import('./contacts/contacts.component').then(m => m.ContactsComponent) },
      { path: 'companies', loadComponent: () => import('./contacts/companies.component').then(m => m.CompaniesComponent) },
      { path: 'leads', loadComponent: () => import('./leads/leads.component').then(m => m.CrmLeadsComponent) },
      { path: 'pipelines', loadComponent: () => import('./pipelines/pipelines.component').then(m => m.PipelinesComponent) },
      { path: 'deals', loadComponent: () => import('./deals/deals.component').then(m => m.DealsComponent) },
      { path: 'activities', loadComponent: () => import('./activities/activities.component').then(m => m.CrmActivitiesComponent) },
    ],
  },
];
