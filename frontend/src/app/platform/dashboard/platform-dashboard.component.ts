import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';

interface DashboardKPIs {
  total_organizations: number;
  active_organizations: number;
  trial_organizations: number;
  suspended_organizations: number;
  total_users: number;
  mrr: number;
  new_orgs_last_30d: number;
  cancelled_last_30d: number;
  subscriptions_by_plan: Record<string, number>;
}

@Component({
  selector: 'app-platform-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Dashboard de plataforma</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Estado global del ecosistema Savvy</p>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-24">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (kpis()) {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-5">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 font-medium">Organizaciones totales</p>
            <p class="mt-2 text-3xl font-bold text-gray-800 dark:text-white/90">{{ kpis()!.total_organizations }}</p>
            <p class="mt-1 text-xs text-success-600 dark:text-success-400">+{{ kpis()!.new_orgs_last_30d }} últimos 30 días</p>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-5">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 font-medium">Con plan activo</p>
            <p class="mt-2 text-3xl font-bold text-success-600 dark:text-success-400">{{ kpis()!.active_organizations }}</p>
            <p class="mt-1 text-xs text-gray-500">{{ kpis()!.trial_organizations }} en trial</p>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-5">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 font-medium">MRR estimado</p>
            <p class="mt-2 text-3xl font-bold text-brand-600 dark:text-brand-400">$ {{ formatMrr(kpis()!.mrr) }}</p>
            <p class="mt-1 text-xs text-gray-500">USD / mes</p>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-5">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 font-medium">Usuarios totales</p>
            <p class="mt-2 text-3xl font-bold text-gray-800 dark:text-white/90">{{ kpis()!.total_users }}</p>
            <p class="mt-1 text-xs text-gray-500">Cross-organization</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-6">
            <h3 class="text-base font-semibold text-gray-800 dark:text-white/90 mb-4">Distribución por plan</h3>
            <div class="space-y-3">
              @for (entry of planEntries(); track entry.code) {
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <span class="w-2 h-2 rounded-full" [style.background-color]="entry.color"></span>
                    <span class="text-sm text-gray-700 dark:text-gray-300 capitalize">{{ entry.code }}</span>
                  </div>
                  <span class="text-sm font-bold text-gray-800 dark:text-white/90">{{ entry.count }}</span>
                </div>
              }
              @if (planEntries().length === 0) {
                <p class="text-sm text-gray-400">Sin suscripciones activas</p>
              }
            </div>
          </div>

          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-6">
            <h3 class="text-base font-semibold text-gray-800 dark:text-white/90 mb-4">Estado del ecosistema</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Suspendidas</span>
                <span class="text-sm font-bold text-warning-600 dark:text-warning-400">{{ kpis()!.suspended_organizations }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Canceladas últimos 30d</span>
                <span class="text-sm font-bold text-error-600 dark:text-error-400">{{ kpis()!.cancelled_last_30d }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Nuevas últimos 30d</span>
                <span class="text-sm font-bold text-success-600 dark:text-success-400">{{ kpis()!.new_orgs_last_30d }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-3">
          <a routerLink="/platform/organizations" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
            Ver organizaciones
          </a>
          <a routerLink="/platform/organizations/new" class="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition">
            + Nueva organización
          </a>
        </div>
      }
    </div>
  `,
})
export class PlatformDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  loading = signal(true);
  kpis = signal<DashboardKPIs | null>(null);

  ngOnInit(): void {
    this.api.get<DashboardKPIs>('/platform/dashboard').subscribe({
      next: (k) => {
        this.kpis.set(k);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  planEntries(): Array<{ code: string; count: number; color: string }> {
    const k = this.kpis();
    if (!k) return [];
    const colors: Record<string, string> = {
      starter: '#60a5fa',
      professional: '#a78bfa',
      enterprise: '#34d399',
      platform: '#f59e0b',
    };
    return Object.entries(k.subscriptions_by_plan).map(([code, count]) => ({
      code,
      count,
      color: colors[code] || '#9ca3af',
    }));
  }

  formatMrr(value: number | string): string {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num || 0);
  }
}
