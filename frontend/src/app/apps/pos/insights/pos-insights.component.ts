import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { AiService, PosInsights } from '../../../core/services/ai.service';
import { KpiCardComponent, ChartCardComponent } from '../../../shared/components/bento';

@Component({
  selector: 'app-pos-insights',
  imports: [CommonModule, DecimalPipe, KpiCardComponent, ChartCardComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-6">
      <header>
        <p class="text-xs uppercase tracking-wider text-violet-600 dark:text-violet-400 font-medium">SavvyInsights ✨</p>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white mt-1">Sugerencias inteligentes</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Reabastecimiento, productos estancados y oportunidades de promoción según tu ritmo de ventas.
        </p>
      </header>

      @if (loading()) {
        <p class="text-sm text-slate-500 dark:text-slate-400">Analizando…</p>
      } @else if (data(); as d) {
        <section class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <app-kpi-card label="Por reabastecer" [value]="d.reorder_count" hint="stock bajo vs ventas" [tone]="d.reorder_count ? 'warn' : 'default'" />
          <app-kpi-card label="Estancados" [value]="d.stale_count" hint="con stock, sin ventas" [tone]="d.stale_count ? 'info' : 'default'" />
          <app-kpi-card label="Ideas de promo" [value]="d.count" hint="combos sugeridos" [tone]="d.count ? 'violet' : 'default'" />
        </section>

        @if (d.reorder_count === 0 && d.stale_count === 0 && d.count === 0) {
          <div class="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-10 text-center">
            <p class="text-sm text-slate-500 dark:text-slate-400">
              Aún no hay suficientes ventas para generar sugerencias. Empieza a vender y vuelve aquí —
              SavvyInsights aprende de tu operación.
            </p>
          </div>
        }

        @if (d.reorder.length) {
          <app-chart-card title="🛒 Reabastecimiento sugerido" subtitle="ordenados por urgencia">
            <div class="overflow-x-auto">
              <table class="min-w-full text-sm">
                <thead class="text-xs text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr><th class="text-left py-2">Producto</th><th class="text-right">Stock</th><th class="text-right">Venta/día</th><th class="text-right">Días restantes</th><th class="text-right">Pedir</th><th class="text-right">Costo est.</th><th></th></tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                  @for (r of d.reorder; track r.sku) {
                    <tr>
                      <td class="py-2"><div class="font-medium text-slate-900 dark:text-white">{{ r.product }}</div><div class="text-xs text-slate-400 font-mono">{{ r.sku }}</div></td>
                      <td class="text-right tabular-nums">{{ r.current_stock | number:'1.0-0' }}</td>
                      <td class="text-right tabular-nums">{{ r.per_day | number:'1.0-2' }}</td>
                      <td class="text-right tabular-nums">{{ r.days_left | number:'1.0-1' }}</td>
                      <td class="text-right tabular-nums font-semibold text-violet-700 dark:text-violet-300">{{ r.suggested_qty | number:'1.0-0' }}</td>
                      <td class="text-right tabular-nums">$ {{ r.est_cost | number:'1.0-0' }}</td>
                      <td class="text-right"><span class="text-[10px] px-1.5 py-0.5 rounded" [class]="r.urgency === 'alta' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'">{{ r.urgency }}</span></td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </app-chart-card>
        }

        @if (d.promos.length) {
          <app-chart-card title="🎯 Ideas de promoción" subtitle="mueve lo estancado con tus best-sellers">
            <ul class="space-y-2">
              @for (p of d.promos; track p.promote) {
                <li class="rounded-lg border border-violet-200 dark:border-violet-900/50 bg-violet-50/40 dark:bg-violet-500/5 p-3">
                  <p class="text-sm text-slate-800 dark:text-slate-200">{{ p.idea }}</p>
                  <p class="text-xs text-slate-400 mt-0.5">Ancla: {{ p.anchor }} ({{ p.anchor_sold }} vendidos) · Promover: {{ p.promote }} ({{ p.promote_stock }} en stock)</p>
                </li>
              }
            </ul>
          </app-chart-card>
        }

        @if (d.stale.length) {
          <app-chart-card title="🐌 Productos estancados" subtitle="capital inmovilizado">
            <div class="overflow-x-auto">
              <table class="min-w-full text-sm">
                <thead class="text-xs text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr><th class="text-left py-2">Producto</th><th class="text-right">Stock</th><th class="text-right">Capital inmovilizado</th></tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                  @for (s of d.stale; track s.sku) {
                    <tr>
                      <td class="py-2"><div class="font-medium text-slate-900 dark:text-white">{{ s.product }}</div><div class="text-xs text-slate-400 font-mono">{{ s.sku }}</div></td>
                      <td class="text-right tabular-nums">{{ s.current_stock | number:'1.0-0' }}</td>
                      <td class="text-right tabular-nums font-semibold">$ {{ s.tied_capital | number:'1.0-0' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </app-chart-card>
        }
      }
    </div>
  `,
})
export class PosInsightsComponent implements OnInit {
  private readonly ai = inject(AiService);
  loading = signal(true);
  data = signal<PosInsights | null>(null);

  ngOnInit(): void {
    this.ai.insightsPos().subscribe({
      next: (d) => { this.data.set(d); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
}
