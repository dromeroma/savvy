import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface DonutSlice {
  label: string;
  value: number;
  color?: string; // hex
}

const DEFAULT_PALETTE = [
  '#6366f1', // indigo
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#a855f7', // purple
  '#ef4444', // red
  '#84cc16', // lime
];

interface DonutSegment {
  d: string;
  color: string;
  label: string;
  value: number;
  pct: number;
}

@Component({
  selector: 'app-donut-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (total() === 0) {
      <div class="text-center py-8">
        <p class="text-xs text-slate-400 dark:text-slate-500">Sin datos para mostrar.</p>
      </div>
    } @else {
      <div class="flex items-center gap-5 flex-col sm:flex-row">
        <svg viewBox="0 0 120 120" class="w-32 h-32 shrink-0 -rotate-90">
          @for (s of segments(); track $index) {
            <path [attr.d]="s.d" [attr.fill]="s.color" [attr.stroke]="strokeColor()" stroke-width="2" />
          }
          <circle cx="60" cy="60" r="32" fill="white" class="dark:fill-slate-900"
            [style.fill]="strokeColor()" />
        </svg>
        <div class="flex-1 min-w-0 w-full">
          <div class="text-2xl font-bold tabular-nums text-slate-900 dark:text-white leading-none">
            {{ total() }}
          </div>
          <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{{ totalLabel() }}</div>
          <ul class="mt-3 space-y-1.5">
            @for (s of segments(); track s.label) {
              <li class="flex items-center justify-between gap-2 text-xs">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="w-2.5 h-2.5 rounded-sm shrink-0" [style.background-color]="s.color"></span>
                  <span class="truncate text-slate-700 dark:text-slate-300">{{ s.label }}</span>
                </div>
                <div class="shrink-0 tabular-nums">
                  <span class="font-mono text-slate-900 dark:text-white">{{ s.value }}</span>
                  <span class="text-slate-400 ml-1">({{ s.pct }}%)</span>
                </div>
              </li>
            }
          </ul>
        </div>
      </div>
    }
  `,
  styles: [`
    :host { display: block; }
  `],
})
export class DonutChartComponent {
  data = input.required<DonutSlice[]>();
  totalLabel = input<string>('total');

  readonly total = computed(() => this.data().reduce((sum, s) => sum + s.value, 0));

  readonly strokeColor = computed(() => {
    // Detect dark mode at component level isn't easy without inspect — leave default.
    // We use the CSS class to style the center circle in dark mode.
    return 'transparent';
  });

  readonly segments = computed<DonutSegment[]>(() => {
    const items = this.data().filter((s) => s.value > 0);
    const total = items.reduce((sum, s) => sum + s.value, 0);
    if (total === 0) return [];
    const r = 50;
    const cx = 60;
    const cy = 60;
    let accAngle = 0;
    return items.map((s, idx) => {
      const pct = s.value / total;
      const startAngle = accAngle * 2 * Math.PI;
      const endAngle = (accAngle + pct) * 2 * Math.PI;
      accAngle += pct;
      const largeArc = pct > 0.5 ? 1 : 0;
      const x1 = cx + r * Math.cos(startAngle);
      const y1 = cy + r * Math.sin(startAngle);
      const x2 = cx + r * Math.cos(endAngle);
      const y2 = cy + r * Math.sin(endAngle);
      const d = `M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${largeArc} 1 ${x2.toFixed(2)},${y2.toFixed(2)} Z`;
      return {
        d,
        color: s.color || DEFAULT_PALETTE[idx % DEFAULT_PALETTE.length],
        label: s.label,
        value: s.value,
        pct: Math.round(pct * 100),
      };
    });
  });
}
