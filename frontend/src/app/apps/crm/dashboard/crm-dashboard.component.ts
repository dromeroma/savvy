import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-crm-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyCRM</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Pipeline de ventas y gestión comercial</p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Pipeline Abierto</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">$ {{ (kpis().pipeline_value || 0) | number:'1.0-0' }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ kpis().open_deals }} deals abiertos</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Revenue Cerrado</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">$ {{ (kpis().won_value || 0) | number:'1.0-0' }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ kpis().won_deals }} ganados</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Win Rate</p>
          <p class="text-2xl font-bold mt-1" [class]="kpis().win_rate >= 30 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">{{ kpis().win_rate }}%</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Contactos</p>
          <p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{{ kpis().total_contacts }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Leads Nuevos</p>
          <p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{{ kpis().new_leads }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Leads Calificados</p>
          <p class="text-2xl font-bold text-teal-600 dark:text-teal-400 mt-1">{{ kpis().qualified_leads }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Convertidos</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{{ kpis().converted_leads }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Deals Perdidos</p>
          <p class="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{{ kpis().lost_deals }}</p>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones rápidas</h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          @for (a of actions; track a.label) {
            <a [routerLink]="a.route" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center">
              <span class="text-2xl">{{ a.icon }}</span>
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ a.label }}</span>
            </a>
          }
        </div>
      </div>
    </div>
  `,
})
export class CrmDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  kpis = signal<any>({ pipeline_value: 0, won_value: 0, win_rate: 0, total_contacts: 0, open_deals: 0, won_deals: 0, lost_deals: 0, new_leads: 0, qualified_leads: 0, converted_leads: 0 });
  readonly actions = [
    { label: 'Contactos', route: '/crm/contacts', icon: '👤' },
    { label: 'Empresas', route: '/crm/companies', icon: '🏢' },
    { label: 'Leads', route: '/crm/leads', icon: '🎯' },
    { label: 'Pipelines', route: '/crm/pipelines', icon: '⚙️' },
    { label: 'Deals', route: '/crm/deals', icon: '💼' },
    { label: 'Actividades', route: '/crm/activities', icon: '📋' },
  ];
  ngOnInit(): void {
    this.api.get<any>('/crm/dashboard/kpis').subscribe({ next: (r) => this.kpis.set(r) });
  }
}
