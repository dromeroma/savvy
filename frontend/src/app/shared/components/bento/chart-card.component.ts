import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

/**
 * Contenedor estándar para una gráfica/visualización. Header con título + opciones
 * y un slot para el contenido.
 */
@Component({
  selector: 'app-chart-card',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 sm:p-6 h-full flex flex-col">
      <div class="flex items-start justify-between gap-3 mb-4">
        <div>
          <h3 class="text-sm font-semibold text-slate-900 dark:text-white">{{ title() }}</h3>
          @if (subtitle()) {
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{{ subtitle() }}</p>
          }
        </div>
        @if (action()) {
          <a [routerLink]="action()!.link"
            class="text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline shrink-0">
            {{ action()!.label }} →
          </a>
        }
      </div>
      <div class="flex-1 min-h-0">
        <ng-content></ng-content>
      </div>
    </div>
  `,
})
export class ChartCardComponent {
  title = input.required<string>();
  subtitle = input<string | null>(null);
  action = input<{ label: string; link: string } | null>(null);
}
