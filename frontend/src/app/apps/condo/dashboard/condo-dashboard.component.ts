import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-condo-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyCondo</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Administracion de propiedades horizontales</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Propiedades</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ kpis().total_properties }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Unidades</p>
          <p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{{ kpis().total_units }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Residentes Activos</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{{ kpis().active_residents }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Cuotas Pendientes</p>
          <p class="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">$ {{ kpis().pending_fees_amount | number:'1.0-0' }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ kpis().pending_fees_count }} cuotas</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Mantenimiento Abierto</p>
          <p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{{ kpis().open_maintenance }}</p>
        </div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones</h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          @for (a of actions; track a.label) {
            <a [routerLink]="a.route" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center">
              <span class="text-2xl">{{ a.icon }}</span><span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ a.label }}</span>
            </a>
          }
        </div>
      </div>
    </div>
  `,
})
export class CondoDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  kpis = signal<any>({ total_properties: 0, total_units: 0, active_residents: 0, pending_fees_count: 0, pending_fees_amount: 0, open_maintenance: 0 });
  readonly actions = [
    { label: 'Propiedades', route: '/condo/properties', icon: '🏢' },
    { label: 'Residentes', route: '/condo/residents', icon: '👥' },
    { label: 'Cuotas', route: '/condo/fees', icon: '💰' },
    { label: 'Areas Comunes', route: '/condo/areas', icon: '🏊' },
    { label: 'Mantenimiento', route: '/condo/maintenance', icon: '🔧' },
    { label: 'Asambleas', route: '/condo/governance', icon: '🗳️' },
    { label: 'Comunicados', route: '/condo/announcements', icon: '📢' },
  ];
  ngOnInit(): void { this.api.get<any>('/condo/dashboard/kpis').subscribe({ next: (r) => this.kpis.set(r) }); }
}
