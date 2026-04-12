import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-health-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6"><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyHealth</h2><p class="text-sm text-gray-500 dark:text-gray-400">Gestion clinica integral</p></div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Pacientes</p><p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ kpis().total_patients }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Profesionales</p><p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{{ kpis().total_providers }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Citas Hoy</p><p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{{ kpis().today_appointments }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Pendientes</p><p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{{ kpis().pending_appointments }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Completadas</p><p class="text-2xl font-bold text-teal-600 dark:text-teal-400 mt-1">{{ kpis().completed_appointments }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Ingresos</p><p class="text-2xl font-bold text-pink-600 dark:text-pink-400 mt-1">$ {{ kpis().total_revenue | number:'1.0-0' }}</p></div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones</h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          @for (a of actions; track a.label) { <a [routerLink]="a.route" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center"><span class="text-2xl">{{ a.icon }}</span><span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ a.label }}</span></a> }
        </div>
      </div>
    </div>
  `,
})
export class HealthDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  kpis = signal<any>({ total_patients: 0, total_providers: 0, today_appointments: 0, pending_appointments: 0, completed_appointments: 0, total_revenue: 0 });
  readonly actions = [
    { label: 'Pacientes', route: '/health/patients', icon: '🏥' },
    { label: 'Profesionales', route: '/health/providers', icon: '👨‍⚕️' },
    { label: 'Citas', route: '/health/appointments', icon: '📅' },
    { label: 'Historias', route: '/health/clinical', icon: '📋' },
    { label: 'Servicios', route: '/health/services', icon: '💊' },
  ];
  ngOnInit(): void { this.api.get<any>('/health/dashboard/kpis').subscribe({ next: (r) => this.kpis.set(r) }); }
}
