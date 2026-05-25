import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PortalService } from '../../core/services/portal.service';
import { PortalConsumptionItem } from '../../core/models/portal.model';

@Component({
  selector: 'app-portal-consumption',
  imports: [CommonModule],
  template: `
    <div>
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90 mb-1">Mi consumo</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-5">
        Lecturas mensuales del medidor. Compara meses para detectar fugas.
      </p>

      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-sky-200 border-t-sky-600"></div>
        </div>
      } @else if (rows().length === 0) {
        <div class="rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-10 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">Aún no hay lecturas registradas.</p>
        </div>
      } @else {
        <!-- Compact visual: bar per month relative to max -->
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 mb-4">
          <div class="space-y-2">
            @for (r of rowsAsc(); track r.period_year + '-' + r.period_month) {
              <div class="flex items-center gap-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 w-16 shrink-0">
                  {{ r.period_year }}-{{ pad(r.period_month) }}
                </div>
                <div class="flex-1 h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div class="h-full rounded-full bg-gradient-to-r from-sky-500 to-cyan-600 transition-all"
                    [style.width.%]="barPct(r)"></div>
                </div>
                <div class="text-xs font-semibold text-gray-800 dark:text-white/90 w-20 text-right shrink-0">
                  {{ r.consumption_cubic }} m³
                </div>
              </div>
            }
          </div>
        </div>

        <!-- Detailed table -->
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-700/30">
              <tr class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <th class="px-4 py-3">Periodo</th>
                <th class="px-4 py-3">Fecha lectura</th>
                <th class="px-4 py-3 text-right">Anterior</th>
                <th class="px-4 py-3 text-right">Actual</th>
                <th class="px-4 py-3 text-right">Consumo</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              @for (r of rows(); track r.period_year + '-' + r.period_month) {
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ r.period_year }}-{{ pad(r.period_month) }}</td>
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ r.reading_date }}</td>
                  <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ r.previous_reading }}</td>
                  <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ r.current_reading }}</td>
                  <td class="px-4 py-3 text-right font-semibold text-gray-800 dark:text-white/90">{{ r.consumption_cubic }} m³</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class PortalConsumptionComponent implements OnInit {
  private readonly portal = inject(PortalService);
  loading = signal(true);
  rows = signal<PortalConsumptionItem[]>([]);

  // Same data but oldest-first for the visual
  readonly rowsAsc = computed(() => [...this.rows()].reverse());

  readonly max = computed(() => {
    const all = this.rows().map((r) => parseFloat(r.consumption_cubic));
    return all.length ? Math.max(...all, 1) : 1;
  });

  ngOnInit(): void {
    this.portal.consumption().subscribe({
      next: (data) => { this.rows.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  barPct(r: PortalConsumptionItem): number {
    return (parseFloat(r.consumption_cubic) / this.max()) * 100;
  }
  pad(n: number): string { return String(n).padStart(2, '0'); }
}
