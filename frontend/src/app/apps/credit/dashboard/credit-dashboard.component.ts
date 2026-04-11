import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-credit-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyCredit</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Gestión de créditos y préstamos</p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Cartera Activa</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ formatMoney(kpis().total_portfolio) }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ kpis().active_loans }} préstamos</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Total Colocado</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{{ formatMoney(kpis().total_disbursed) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Total Recaudado</p>
          <p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{{ formatMoney(kpis().total_collected) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Mora</p>
          <p class="text-2xl font-bold mt-1" [class]="kpis().delinquency_rate > 5 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
            {{ kpis().delinquency_rate }}%
          </p>
          <p class="text-xs text-gray-400 mt-1">{{ kpis().delinquent_loans }} en mora</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Prestatarios</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-white/90 mt-1">{{ kpis().total_borrowers }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Intereses por Cobrar</p>
          <p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{{ formatMoney(kpis().total_interest_receivable) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Monto en Mora</p>
          <p class="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{{ formatMoney(kpis().delinquent_amount) }}</p>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones rápidas</h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          @for (action of quickActions; track action.label) {
            <a [routerLink]="action.route"
              class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center">
              <span class="text-2xl">{{ action.icon }}</span>
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ action.label }}</span>
            </a>
          }
        </div>
      </div>
    </div>
  `,
})
export class CreditDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  kpis = signal<any>({
    active_loans: 0, total_portfolio: 0, total_disbursed: 0, total_collected: 0,
    delinquency_rate: 0, delinquent_loans: 0, delinquent_amount: 0,
    total_borrowers: 0, total_interest_receivable: 0, total_penalties: 0,
  });

  readonly quickActions = [
    { label: 'Productos', route: '/credit/products', icon: '📦' },
    { label: 'Prestatarios', route: '/credit/borrowers', icon: '👤' },
    { label: 'Solicitudes', route: '/credit/applications', icon: '📋' },
    { label: 'Préstamos', route: '/credit/loans', icon: '💰' },
  ];

  ngOnInit(): void {
    this.api.get<any>('/credit/dashboard/kpis').subscribe({
      next: (r) => this.kpis.set(r),
    });
  }

  formatMoney(v: number): string {
    return '$ ' + (v || 0).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }
}
