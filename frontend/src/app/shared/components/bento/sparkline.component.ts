import { Component, computed, input } from '@angular/core';

/**
 * Sparkline SVG ligero. Acepta una serie numérica y dibuja área + línea.
 * Sin dependencias externas. Auto-escala al contenedor.
 *
 * @example
 *   <app-sparkline [data]="[12, 18, 15, 22, 30, 28, 35]" color="emerald" />
 */
@Component({
  selector: 'app-sparkline',
  standalone: true,
  template: `
    @if (data().length >= 2) {
      <svg viewBox="0 0 100 30" preserveAspectRatio="none"
        class="w-full h-full overflow-visible"
        [class.text-emerald-500]="color() === 'emerald'"
        [class.text-amber-500]="color() === 'amber'"
        [class.text-rose-500]="color() === 'rose'"
        [class.text-blue-500]="color() === 'blue'"
        [class.text-violet-500]="color() === 'violet'"
        [class.text-brand-500]="color() === 'brand'"
        [class.text-slate-400]="color() === 'slate'">
        <defs>
          <linearGradient [attr.id]="gradientId()" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="currentColor" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="currentColor" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <path [attr.d]="areaPath()" [attr.fill]="'url(#' + gradientId() + ')'" stroke="none"/>
        <path [attr.d]="linePath()" fill="none" stroke="currentColor" stroke-width="1.5"
          vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round"/>
        <circle [attr.cx]="lastX()" [attr.cy]="lastY()" r="2" fill="currentColor"
          vector-effect="non-scaling-stroke"/>
      </svg>
    }
  `,
})
export class SparklineComponent {
  data = input.required<number[]>();
  color = input<'emerald' | 'amber' | 'rose' | 'blue' | 'violet' | 'brand' | 'slate'>('brand');

  readonly gradientId = computed(() =>
    'spark-' + Math.random().toString(36).slice(2, 9));

  private readonly scaled = computed(() => {
    const d = this.data();
    if (d.length < 2) return [];
    const min = Math.min(...d);
    const max = Math.max(...d);
    const range = max - min || 1;
    return d.map((v, i) => ({
      x: (i / (d.length - 1)) * 100,
      y: 30 - ((v - min) / range) * 26 - 2,
    }));
  });

  readonly linePath = computed(() => {
    const pts = this.scaled();
    if (pts.length === 0) return '';
    return 'M' + pts.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' L');
  });

  readonly areaPath = computed(() => {
    const pts = this.scaled();
    if (pts.length === 0) return '';
    const line = pts.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' L');
    return `M${pts[0].x},30 L${line} L${pts[pts.length - 1].x},30 Z`;
  });

  readonly lastX = computed(() => {
    const pts = this.scaled();
    return pts.length ? pts[pts.length - 1].x.toFixed(2) : '0';
  });
  readonly lastY = computed(() => {
    const pts = this.scaled();
    return pts.length ? pts[pts.length - 1].y.toFixed(2) : '0';
  });
}
