import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-parking-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyParking</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Control de parqueaderos en tiempo real</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Vehículos Activos</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ kpis().active_sessions }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Ocupación</p>
          <p class="text-2xl font-bold mt-1" [class]="kpis().occupancy_rate > 80 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">{{ kpis().occupancy_rate }}%</p>
          <p class="text-xs text-gray-400 mt-1">{{ kpis().current_occupancy }} / {{ kpis().total_capacity }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Disponibles</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{{ kpis().available_spots }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Ingreso Hoy</p>
          <p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">$ {{ kpis().today_revenue | number:'1.0-0' }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ kpis().completed_today }} salidas</p>
        </div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones</h3>
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
export class ParkingDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  kpis = signal<any>({ active_sessions: 0, occupancy_rate: 0, current_occupancy: 0, total_capacity: 0, available_spots: 0, today_revenue: 0, completed_today: 0 });
  readonly actions = [
    { label: 'Infraestructura', route: '/parking/infrastructure', icon: '🏗️' },
    { label: 'Vehículos', route: '/parking/vehicles', icon: '🚗' },
    { label: 'Sesiones', route: '/parking/sessions', icon: '🅿️' },
    { label: 'Tarifas', route: '/parking/pricing', icon: '💲' },
    { label: 'Servicios', route: '/parking/services', icon: '🧽' },
  ];
  ngOnInit(): void { this.api.get<any>('/parking/dashboard/kpis').subscribe({ next: (r) => this.kpis.set(r) }); }
}
