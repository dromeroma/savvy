import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { WaterService } from '../../../core/services/water.service';
import { WaterDashboardKpis } from '../../../core/models/water.model';

@Component({
  selector: 'app-water-dashboard',
  imports: [CommonModule, RouterLink, DecimalPipe],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">SavvyWater</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Gestión integral del acueducto.</p>
        </div>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-20">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (error()) {
        <div class="p-4 bg-error-50 border border-error-200 text-error-700 dark:bg-error-500/10 dark:border-error-500/30 dark:text-error-400 rounded-lg">
          {{ error() }}
        </div>
      } @else if (kpis()) {
        @let k = kpis()!;

        <!-- KPIs row -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Suscriptores</div>
            <div class="mt-1 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ k.total_subscribers }}</div>
            <div class="text-[10px] text-gray-400 mt-1">Total registrados</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Activos</div>
            <div class="mt-1 text-2xl font-semibold text-emerald-600">{{ k.by_status.active }}</div>
            <div class="text-[10px] text-gray-400 mt-1">Servicio normal</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">En mora</div>
            <div class="mt-1 text-2xl font-semibold text-amber-600">{{ k.by_status.overdue }}</div>
            <div class="text-[10px] text-gray-400 mt-1">Con saldo vencido</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Suspendidos</div>
            <div class="mt-1 text-2xl font-semibold text-red-600">{{ k.by_status.suspended }}</div>
            <div class="text-[10px] text-gray-400 mt-1">Servicio cortado</div>
          </div>
        </div>

        <!-- Billing + treasury row -->
        <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Facturas del mes</div>
            <div class="mt-1 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ k.invoices_this_month }}</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Facturado del mes</div>
            <div class="mt-1 text-xl font-semibold text-gray-800 dark:text-white/90">$ {{ k.billed_this_month | number:'1.0-0' }}</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Cartera pendiente</div>
            <div class="mt-1 text-xl font-semibold text-red-600">$ {{ k.pending_balance | number:'1.0-0' }}</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Recaudo del mes</div>
            <div class="mt-1 text-xl font-semibold text-emerald-700">$ {{ k.paid_this_month | number:'1.0-0' }}</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Recaudo de hoy</div>
            <div class="mt-1 text-xl font-semibold text-emerald-700">$ {{ k.paid_today | number:'1.0-0' }}</div>
          </div>
        </div>

        <!-- Overdue row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="rounded-2xl border border-red-200 dark:border-red-700/40 bg-red-50/40 dark:bg-red-500/5 p-5">
            <div class="text-xs uppercase tracking-wider text-red-700 dark:text-red-300">Suscriptores morosos</div>
            <div class="mt-1 text-2xl font-semibold text-red-700 dark:text-red-300">{{ k.overdue_subscribers }}</div>
          </div>
          <div class="rounded-2xl border border-red-200 dark:border-red-700/40 bg-red-50/40 dark:bg-red-500/5 p-5">
            <div class="text-xs uppercase tracking-wider text-red-700 dark:text-red-300">Facturas vencidas</div>
            <div class="mt-1 text-2xl font-semibold text-red-700 dark:text-red-300">{{ k.overdue_invoices }}</div>
          </div>
          <div class="rounded-2xl border border-red-200 dark:border-red-700/40 bg-red-50/40 dark:bg-red-500/5 p-5">
            <div class="text-xs uppercase tracking-wider text-red-700 dark:text-red-300">Saldo vencido</div>
            <div class="mt-1 text-xl font-semibold text-red-700 dark:text-red-300">$ {{ k.overdue_balance | number:'1.0-0' }}</div>
          </div>
        </div>

        <!-- Treasury row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="rounded-2xl border border-emerald-200 dark:border-emerald-700/40 bg-emerald-50/40 dark:bg-emerald-500/5 p-5">
            <div class="text-xs uppercase tracking-wider text-emerald-700 dark:text-emerald-300">Efectivo total en caja</div>
            <div class="mt-1 text-2xl font-semibold text-emerald-700 dark:text-emerald-300">$ {{ k.cash_on_hand | number:'1.0-0' }}</div>
            <div class="text-[10px] text-emerald-600 dark:text-emerald-400 mt-1">{{ k.cash_accounts_count }} cuenta(s) de tesorería</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 flex items-center justify-between">
            <div>
              <div class="text-xs uppercase tracking-wider text-gray-400">Tesorería</div>
              <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">Ver saldos, movimientos y arqueos</div>
            </div>
            <a routerLink="/water/treasury"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium">
              Abrir →
            </a>
          </div>
        </div>

        <!-- Meters row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Medidores</div>
            <div class="mt-1 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ k.total_meters }}</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Asignados</div>
            <div class="mt-1 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ k.assigned_meters }}</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-xs uppercase tracking-wider text-gray-400">Sin asignar</div>
            <div class="mt-1 text-2xl font-semibold text-orange-500">{{ k.unassigned_meters }}</div>
          </div>
        </div>

        <!-- Quick actions -->
        <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
          <div class="flex flex-wrap gap-3">
            <a routerLink="/water/consumptions"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium">
              Registrar lecturas
            </a>
            <a routerLink="/water/invoices"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 text-sm font-medium">
              Generar facturas del mes
            </a>
            <a routerLink="/water/payments"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 text-sm font-medium">
              Registrar pago
            </a>
            <a routerLink="/water/cartera"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 text-sm font-medium">
              Ver cartera
            </a>
            <a routerLink="/water/routes"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 text-sm font-medium">
              Rutas de cobro
            </a>
            <a routerLink="/water/tariffs"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 text-sm font-medium">
              Tarifas
            </a>
          </div>
        </div>

        <!-- Roadmap placeholder -->
        <div class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">Próximamente en SavvyWater</h3>
          <ul class="text-sm text-gray-500 dark:text-gray-400 list-disc pl-5 space-y-1">
            <li>Portal del cliente / suscriptor (Fase 5)</li>
            <li>Notificaciones (WhatsApp / email) y reportes ejecutivos (Fase 6)</li>
            <li>Integración con SavvyAccounting (futuro)</li>
          </ul>
        </div>
      }
    </div>
  `,
})
export class WaterDashboardComponent implements OnInit {
  private readonly water = inject(WaterService);

  loading = signal(true);
  error = signal('');
  kpis = signal<WaterDashboardKpis | null>(null);

  ngOnInit(): void {
    this.water.getKpis().subscribe({
      next: (data) => {
        this.kpis.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail || 'No se pudieron cargar los KPIs.');
      },
    });
  }
}
