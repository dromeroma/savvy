import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

interface DashboardKPIs {
  active_congregants: number;
  inactive_congregants: number;
  new_this_month: number;
  income_this_month: number;
  expenses_this_month: number;
  net_this_month: number;
  income_last_month: number;
}

@Component({
  selector: 'app-church-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Dashboard</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Resumen general de tu iglesia</p>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (kpis(); as k) {
        <!-- KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <!-- Active Members -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-500/20 flex items-center justify-center">
                <svg class="w-5 h-5 text-brand-600 dark:text-brand-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <span class="text-sm text-gray-500 dark:text-gray-400">Congregantes activos</span>
            </div>
            <p class="text-2xl font-bold text-gray-800 dark:text-white/90">{{ k.active_congregants }}</p>
            @if (k.new_this_month > 0) {
              <p class="text-xs text-success-600 dark:text-success-400 mt-1">+{{ k.new_this_month }} este mes</p>
            }
          </div>

          <!-- Inactive -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                <svg class="w-5 h-5 text-gray-500 dark:text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="18" y1="8" x2="23" y2="13"/><line x1="23" y1="8" x2="18" y2="13"/>
                </svg>
              </div>
              <span class="text-sm text-gray-500 dark:text-gray-400">Inactivos</span>
            </div>
            <p class="text-2xl font-bold text-gray-800 dark:text-white/90">{{ k.inactive_congregants }}</p>
          </div>

          <!-- Income this month -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-success-50 dark:bg-success-500/20 flex items-center justify-center">
                <svg class="w-5 h-5 text-success-600 dark:text-success-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
              </div>
              <span class="text-sm text-gray-500 dark:text-gray-400">Ingresos del mes</span>
            </div>
            <p class="text-2xl font-bold text-success-600 dark:text-success-400">{{ fmt(k.income_this_month) }}</p>
            @if (k.income_last_month > 0) {
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Mes anterior: {{ fmt(k.income_last_month) }}</p>
            }
          </div>

          <!-- Net this month -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                [ngClass]="k.net_this_month >= 0 ? 'bg-success-50 dark:bg-success-500/20' : 'bg-error-50 dark:bg-error-500/20'">
                <svg class="w-5 h-5" [ngClass]="k.net_this_month >= 0 ? 'text-success-600 dark:text-success-400' : 'text-error-600 dark:text-error-400'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>
                </svg>
              </div>
              <span class="text-sm text-gray-500 dark:text-gray-400">Balance neto</span>
            </div>
            <p class="text-2xl font-bold" [ngClass]="k.net_this_month >= 0 ? 'text-success-600 dark:text-success-400' : 'text-error-600 dark:text-error-400'">
              {{ fmt(k.net_this_month) }}
            </p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Gastos: {{ fmt(k.expenses_this_month) }}</p>
          </div>
        </div>

        <!-- Quick Actions -->
        <h3 class="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Accesos rápidos</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <a routerLink="/church/congregants"
            class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:border-brand-300 dark:hover:border-brand-500 transition group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-purple-50 dark:bg-purple-500/20 flex items-center justify-center">
                <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-white/90 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition">Congregantes</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Gestionar miembros</p>
              </div>
            </div>
          </a>
          <a routerLink="/church/finance"
            class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:border-brand-300 dark:hover:border-brand-500 transition group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-green-50 dark:bg-green-500/20 flex items-center justify-center">
                <svg class="w-5 h-5 text-green-600 dark:text-green-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-white/90 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition">Finanzas</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Ingresos y egresos</p>
              </div>
            </div>
          </a>
          <a routerLink="/church/reports"
            class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:border-brand-300 dark:hover:border-brand-500 transition group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-500/20 flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-white/90 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition">Reportes</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Resúmenes mensuales</p>
              </div>
            </div>
          </a>
          <a routerLink="/church/groups"
            class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:border-brand-300 dark:hover:border-brand-500 transition group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-orange-50 dark:bg-orange-500/20 flex items-center justify-center">
                <svg class="w-5 h-5 text-orange-600 dark:text-orange-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-white/90 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition">Grupos</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Ministerios y células</p>
              </div>
            </div>
          </a>
        </div>
      }
    </div>
  `,
})
export class ChurchDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  loading = signal(true);
  kpis = signal<DashboardKPIs | null>(null);

  ngOnInit(): void {
    this.api.get<DashboardKPIs>('/church/dashboard/kpis').subscribe({
      next: (data) => {
        this.kpis.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  fmt(value: number | undefined | null): string {
    if (value == null) return '$0';
    return '$' + Number(value).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }
}
