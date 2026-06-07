import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import { MemorialDashboardKpis } from '../../../core/models/memorial.model';
import {
  BarChartComponent,
  BarRow,
  ChartCardComponent,
  DonutChartComponent,
  DonutSlice,
  HeroMetricCardComponent,
  KpiCardComponent,
} from '../../../shared/components/bento';

const STATUS_LABELS: Record<string, string> = {
  iniciado: 'Iniciado',
  en_proceso: 'En proceso',
  pendiente: 'Pendiente',
  finalizado: 'Finalizado',
  cancelado: 'Cancelado',
};

const STATUS_COLORS: Record<string, string> = {
  iniciado: '#f59e0b',
  en_proceso: '#6366f1',
  pendiente: '#94a3b8',
  finalizado: '#10b981',
  cancelado: '#ef4444',
};

@Component({
  selector: 'app-memorial-dashboard',
  imports: [
    CommonModule, RouterLink,
    HeroMetricCardComponent, KpiCardComponent, ChartCardComponent,
    DonutChartComponent, BarChartComponent,
  ],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-7">
      <header class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2">
        <div>
          <p class="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-medium">
            SavvyMemorial
          </p>
          <h1 class="text-3xl font-bold text-slate-900 dark:text-white mt-1">Operación funeraria</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Servicios, contratos exequiales y cartera.
          </p>
        </div>
        <div class="text-right">
          <div class="text-[11px] uppercase tracking-wider text-slate-400">Última actualización</div>
          <div class="text-xs text-slate-600 dark:text-slate-300 tabular-nums">{{ now }}</div>
        </div>
      </header>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (kpis(); as k) {

        <!-- ============== BENTO: HERO (recaudado del mes) + 4 KPIs ============== -->
        <section class="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
          <div class="lg:col-span-7 lg:row-span-2">
            <app-hero-metric-card
              [label]="'Recaudado este mes'"
              [value]="'$ ' + fmt(+k.paid_this_month)"
              tone="emerald"
              icon="$"
              [subtitle]="'sobre $ ' + fmt(+k.billed_this_month) + ' facturado'"
              [hint]="collectionPct(k) + '% de cobranza efectiva'"
              link="/memorial/payments" />
          </div>

          <div class="lg:col-span-5 grid grid-cols-2 gap-4">
            <app-kpi-card
              label="Cartera pendiente"
              [value]="'$ ' + fmt(+k.pending_balance)"
              hint="saldo por cobrar"
              tone="warn"
              link="/memorial/invoices" />

            <app-kpi-card
              label="Cartera vencida"
              [value]="'$ ' + fmt(+k.overdue_balance)"
              [hint]="k.overdue_invoices + ' factura(s) vencidas'"
              [tone]="(+k.overdue_balance) > 0 ? 'danger' : 'default'"
              link="/memorial/cartera" />

            <app-kpi-card
              label="Servicios activos"
              [value]="k.services_active"
              hint="en proceso · pendiente"
              tone="info"
              link="/memorial/services" />

            <app-kpi-card
              label="Defunciones hoy"
              [value]="k.services_today"
              hint="iniciadas en el día"
              tone="violet"
              link="/memorial/services" />
          </div>
        </section>

        <!-- ============== BENTO: charts ============== -->
        <section class="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
          <!-- Donut: servicios por estado -->
          <div class="lg:col-span-5">
            <app-chart-card title="Servicios por estado"
              [subtitle]="k.services_total + ' servicios en total'"
              [action]="{ label: 'Ver lista', link: '/memorial/services' }">
              <app-donut-chart [data]="servicesByStatus(k)" totalLabel="servicios" />
            </app-chart-card>
          </div>

          <!-- Bar: comparativo financiero del mes -->
          <div class="lg:col-span-7">
            <app-chart-card title="Comparativa financiera"
              subtitle="facturado vs recaudado vs cartera"
              [action]="{ label: 'Cartera', link: '/memorial/cartera' }">
              <app-bar-chart [data]="financeBreakdown(k)" tone="emerald" />
            </app-chart-card>
          </div>

          <!-- Stack de planes/contratos/afiliados -->
          <div class="lg:col-span-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <app-kpi-card
              label="Contratos exequiales"
              [value]="k.active_contracts"
              hint="activos"
              tone="info" size="lg"
              link="/memorial/contracts" />

            <app-kpi-card
              label="Afiliados"
              [value]="k.total_affiliates"
              hint="beneficiarios vigentes"
              tone="violet" size="lg" />

            <app-kpi-card
              label="Planes en catálogo"
              [value]="k.plans_active"
              hint="activos para vender"
              tone="default" size="lg"
              link="/memorial/plans" />
          </div>
        </section>

        <!-- ============== Acciones rápidas ============== -->
        <section>
          <h2 class="text-base font-semibold text-slate-900 dark:text-white mb-3">Atajos</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            @for (link of quickLinks; track link.route) {
              <a [routerLink]="link.route"
                class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 hover:ring-2 hover:ring-brand-300 dark:hover:ring-brand-700 transition">
                <div class="text-2xl mb-1">{{ link.icon }}</div>
                <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ link.label }}</div>
                <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{{ link.hint }}</div>
              </a>
            }
          </div>
        </section>

      } @else {
        <div class="p-5 bg-rose-50 border border-rose-200 dark:bg-rose-500/10 dark:border-rose-500/30 rounded-2xl text-sm text-rose-700 dark:text-rose-400">
          No se pudo cargar el resumen de SavvyMemorial.
        </div>
      }
    </div>
  `,
})
export class MemorialDashboardComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);

  loading = signal(true);
  kpis = signal<MemorialDashboardKpis | null>(null);

  readonly now = new Date().toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

  readonly quickLinks = [
    { route: '/memorial/services', icon: '⚱️', label: 'Servicios', hint: 'gestionar exequias' },
    { route: '/memorial/contracts', icon: '📄', label: 'Contratos', hint: 'exequiales activos' },
    { route: '/memorial/invoices', icon: '🧾', label: 'Facturación', hint: 'cuotas · facturas' },
    { route: '/memorial/cartera', icon: '💰', label: 'Cartera', hint: 'aging · morosos' },
  ];

  ngOnInit(): void {
    this.memorial.getKpis().subscribe({
      next: (d) => { this.kpis.set(d); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  servicesByStatus(k: MemorialDashboardKpis): DonutSlice[] {
    return Object.entries(k.services_by_status)
      .filter(([, v]) => v > 0)
      .map(([key, value]) => ({
        label: STATUS_LABELS[key] || key,
        value,
        color: STATUS_COLORS[key],
      }));
  }

  financeBreakdown(k: MemorialDashboardKpis): BarRow[] {
    return [
      { label: 'Facturado mes', value: Math.round(+k.billed_this_month) },
      { label: 'Recaudado mes', value: Math.round(+k.paid_this_month) },
      { label: 'Cartera pendiente', value: Math.round(+k.pending_balance) },
      { label: 'Cartera vencida', value: Math.round(+k.overdue_balance) },
    ].filter((r) => r.value > 0);
  }

  collectionPct(k: MemorialDashboardKpis): number {
    const billed = +k.billed_this_month;
    if (billed === 0) return 0;
    return Math.round((+k.paid_this_month / billed) * 100);
  }

  fmt(n: number): string {
    return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(n);
  }
}
