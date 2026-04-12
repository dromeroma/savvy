import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-pos-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6"><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyPOS</h2><p class="text-sm text-gray-500 dark:text-gray-400">Punto de venta cloud integrado al ecosistema</p></div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Ventas Hoy</p><p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">$ {{ kpis().today_revenue | number:'1.0-0' }}</p><p class="text-xs text-gray-400 mt-1">{{ kpis().today_sales }} ventas</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Ingresos Totales</p><p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">$ {{ kpis().total_revenue | number:'1.0-0' }}</p><p class="text-xs text-gray-400 mt-1">{{ kpis().total_sales }} ventas</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Productos Activos</p><p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{{ kpis().active_products }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Stock Bajo</p><p class="text-2xl font-bold mt-1" [class]="kpis().low_stock_items > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">{{ kpis().low_stock_items }}</p></div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones</h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          @for (a of actions; track a.label) { <a [routerLink]="a.route" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center"><span class="text-2xl">{{ a.icon }}</span><span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ a.label }}</span></a> }
        </div>
      </div>
    </div>
  `,
})
export class PosDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  kpis = signal<any>({ today_sales: 0, today_revenue: 0, total_sales: 0, total_revenue: 0, active_products: 0, low_stock_items: 0 });
  readonly actions = [
    { label: 'Terminal', route: '/pos/terminal', icon: '💳' },
    { label: 'Productos', route: '/pos/products', icon: '📦' },
    { label: 'Inventario', route: '/pos/inventory', icon: '📊' },
    { label: 'Ventas', route: '/pos/sales', icon: '🧾' },
    { label: 'Cajas', route: '/pos/registers', icon: '💰' },
    { label: 'Sucursales', route: '/pos/locations', icon: '🏪' },
  ];
  ngOnInit(): void { this.api.get<any>('/pos/dashboard/kpis').subscribe({ next: (r) => this.kpis.set(r) }); }
}
