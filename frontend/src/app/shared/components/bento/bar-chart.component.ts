import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface BarRow {
  label: string;
  value: number;
  color?: string;
}

/**
 * Gráfica de barras horizontales: ranking. Cada fila muestra label, valor y barra %.
 */
@Component({
  selector: 'app-bar-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (rows().length === 0) {
      <p class="text-xs text-slate-400 dark:text-slate-500 text-center py-6">Sin datos.</p>
    } @else {
      <ul class="space-y-3">
        @for (r of rows(); track r.label) {
          <li>
            <div class="flex items-center justify-between gap-2 mb-1.5 text-xs">
              <span class="text-slate-700 dark:text-slate-300 truncate">{{ r.label }}</span>
              <div class="shrink-0 tabular-nums">
                <span class="font-mono text-slate-900 dark:text-white font-semibold">{{ r.value }}</span>
                <span class="text-slate-400 ml-1">{{ r.pct }}%</span>
              </div>
            </div>
            <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500"
                [style.width.%]="r.pct"
                [style.background]="r.gradient"></div>
            </div>
          </li>
        }
      </ul>
    }
  `,
})
export class BarChartComponent {
  data = input.required<BarRow[]>();
  /** Tone for the default gradient when row.color is not provided. */
  tone = input<'brand' | 'emerald' | 'amber' | 'rose' | 'violet'>('brand');

  private readonly toneStops: Record<string, [string, string]> = {
    brand: ['#a855f7', '#6366f1'],
    emerald: ['#34d399', '#059669'],
    amber: ['#fbbf24', '#d97706'],
    rose: ['#fb7185', '#e11d48'],
    violet: ['#c084fc', '#7c3aed'],
  };

  readonly rows = computed(() => {
    const items = this.data();
    const max = items.reduce((m, r) => Math.max(m, r.value), 0) || 1;
    const [start, end] = this.toneStops[this.tone()];
    return items.map((r) => ({
      ...r,
      pct: Math.round((r.value / max) * 100),
      gradient: r.color
        ? r.color
        : `linear-gradient(90deg, ${start}, ${end})`,
    }));
  });
}
