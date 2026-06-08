import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { AiService, MemorialRisk } from '../../../core/services/ai.service';
import { HeroMetricCardComponent, KpiCardComponent } from '../../../shared/components/bento';

@Component({
  selector: 'app-memorial-risk',
  imports: [CommonModule, DecimalPipe, HeroMetricCardComponent, KpiCardComponent],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-6">
      <header>
        <p class="text-xs uppercase tracking-wider text-violet-600 dark:text-violet-400 font-medium">SavvyInsights ✨</p>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white mt-1">Riesgo de cartera</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Clientes con facturas vencidas, priorizados por riesgo de pérdida. La acción sugerida te dice qué hacer hoy.
        </p>
      </header>

      @if (loading()) {
        <p class="text-sm text-slate-500 dark:text-slate-400">Analizando cartera…</p>
      } @else if (data(); as d) {
        <section class="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
          <div class="lg:col-span-6 lg:row-span-2">
            <app-hero-metric-card
              label="Total vencido en riesgo"
              [value]="'$ ' + fmt(d.total_overdue_amount)"
              tone="amber" icon="⚠️"
              [subtitle]="d.total_at_risk + ' cliente(s) con mora'"
              hint="prioriza los de riesgo alto" />
          </div>
          <div class="lg:col-span-6 grid grid-cols-3 gap-4">
            <app-kpi-card label="Riesgo alto" [value]="d.by_tier.alto" hint="llamar hoy" [tone]="d.by_tier.alto ? 'danger' : 'default'" />
            <app-kpi-card label="Riesgo medio" [value]="d.by_tier.medio" hint="recordatorio" [tone]="d.by_tier.medio ? 'warn' : 'default'" />
            <app-kpi-card label="Riesgo bajo" [value]="d.by_tier.bajo" hint="monitorear" tone="info" />
          </div>
        </section>

        @if (d.at_risk.length === 0) {
          <div class="rounded-2xl border border-dashed border-emerald-300 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-500/5 p-10 text-center">
            <p class="text-sm text-emerald-700 dark:text-emerald-300">🎉 Sin clientes en mora. Tu cartera está al día.</p>
          </div>
        } @else {
          <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-4 py-3 font-medium">Cliente</th>
                  <th class="text-left px-4 py-3 font-medium">Contrato</th>
                  <th class="text-right px-4 py-3 font-medium">Fact. vencidas</th>
                  <th class="text-right px-4 py-3 font-medium">Días mora</th>
                  <th class="text-right px-4 py-3 font-medium">Vencido</th>
                  <th class="text-left px-4 py-3 font-medium">Riesgo</th>
                  <th class="text-left px-4 py-3 font-medium">Acción sugerida</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @for (r of d.at_risk; track r.contract_id) {
                  <tr [class.bg-rose-50/30]="r.risk_tier === 'alto'" [class.dark:bg-rose-900/10]="r.risk_tier === 'alto'">
                    <td class="px-4 py-2.5">
                      <div class="font-medium text-slate-900 dark:text-white">{{ r.name }}</div>
                      @if (r.phone) { <div class="text-xs text-slate-400">{{ r.phone }}</div> }
                    </td>
                    <td class="px-4 py-2.5 font-mono text-xs">{{ r.code }}</td>
                    <td class="px-4 py-2.5 text-right tabular-nums">{{ r.overdue_count }}</td>
                    <td class="px-4 py-2.5 text-right tabular-nums">{{ r.days_late }}</td>
                    <td class="px-4 py-2.5 text-right tabular-nums font-semibold">$ {{ r.overdue_amount | number:'1.0-0' }}</td>
                    <td class="px-4 py-2.5"><span class="text-xs px-2 py-0.5 rounded-md font-medium" [class]="tierClass(r.risk_tier)">{{ r.risk_tier }}</span></td>
                    <td class="px-4 py-2.5 text-xs text-slate-600 dark:text-slate-300">{{ r.action }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      }
    </div>
  `,
})
export class MemorialRiskComponent implements OnInit {
  private readonly ai = inject(AiService);
  loading = signal(true);
  data = signal<MemorialRisk | null>(null);

  ngOnInit(): void {
    this.ai.insightsMemorial().subscribe({
      next: (d) => { this.data.set(d); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  fmt(n: number): string { return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(n); }
  tierClass(t: string): string {
    const map: Record<string, string> = {
      alto: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
      medio: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
      bajo: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    };
    return map[t] || '';
  }
}
