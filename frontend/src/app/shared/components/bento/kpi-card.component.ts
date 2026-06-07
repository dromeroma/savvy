import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SparklineComponent } from './sparkline.component';

export type KpiTone = 'default' | 'success' | 'warn' | 'danger' | 'info' | 'violet';
export type KpiSize = 'sm' | 'md' | 'lg';

/**
 * Tarjeta KPI bento. Soporta label, valor, hint, opcional sparkline + delta + link.
 *
 * @example
 *   <app-kpi-card label="Empleados activos" value="48" hint="de 51 totales"
 *     tone="success" [series]="trend" delta="+12%" link="/hr/employees" />
 */
@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [CommonModule, RouterLink, SparklineComponent],
  template: `
    <ng-container *ngTemplateOutlet="link() ? linked : plain"></ng-container>

    <ng-template #plain>
      <div [class]="rootClass()">
        <ng-container *ngTemplateOutlet="content"></ng-container>
      </div>
    </ng-template>

    <ng-template #linked>
      <a [routerLink]="link()" [class]="rootClass() + ' hover:ring-2 hover:ring-brand-300 dark:hover:ring-brand-700 transition'">
        <ng-container *ngTemplateOutlet="content"></ng-container>
      </a>
    </ng-template>

    <ng-template #content>
      <div class="flex items-start justify-between gap-2">
        <div class="text-[10.5px] uppercase tracking-wider font-medium" [class]="labelClass()">
          {{ label() }}
        </div>
        @if (delta()) {
          <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded" [class]="deltaClass()">
            {{ delta() }}
          </span>
        }
      </div>
      <div class="tabular-nums mt-1 leading-none" [class]="valueClass()">
        {{ value() }}
      </div>
      @if (hint()) {
        <div class="text-[11px] mt-1.5" [class]="hintClass()">
          {{ hint() }}
        </div>
      }
      @if (series() && series()!.length >= 2) {
        <div class="mt-3 -mb-1 h-8">
          <app-sparkline [data]="series()!" [color]="sparkColor()" />
        </div>
      }
    </ng-template>
  `,
})
export class KpiCardComponent {
  label = input.required<string>();
  value = input.required<string | number>();
  hint = input<string | null>(null);
  delta = input<string | null>(null);
  tone = input<KpiTone>('default');
  size = input<KpiSize>('md');
  series = input<number[] | null>(null);
  link = input<string | null>(null);

  rootClass(): string {
    const base = 'rounded-2xl border p-4 sm:p-5 flex flex-col bg-white dark:bg-slate-900 backdrop-blur-sm';
    const tones: Record<KpiTone, string> = {
      default: 'border-slate-200 dark:border-slate-800',
      success: 'border-emerald-200 dark:border-emerald-900/70 bg-emerald-50/40 dark:bg-emerald-500/5',
      warn: 'border-amber-200 dark:border-amber-900/70 bg-amber-50/40 dark:bg-amber-500/5',
      danger: 'border-rose-200 dark:border-rose-900/70 bg-rose-50/40 dark:bg-rose-500/5',
      info: 'border-blue-200 dark:border-blue-900/70 bg-blue-50/40 dark:bg-blue-500/5',
      violet: 'border-violet-200 dark:border-violet-900/70 bg-violet-50/40 dark:bg-violet-500/5',
    };
    return `${base} ${tones[this.tone()]}`;
  }

  labelClass(): string {
    const tones: Record<KpiTone, string> = {
      default: 'text-slate-500 dark:text-slate-400',
      success: 'text-emerald-700 dark:text-emerald-400',
      warn: 'text-amber-700 dark:text-amber-400',
      danger: 'text-rose-700 dark:text-rose-400',
      info: 'text-blue-700 dark:text-blue-400',
      violet: 'text-violet-700 dark:text-violet-400',
    };
    return tones[this.tone()];
  }

  valueClass(): string {
    const sizeMap: Record<KpiSize, string> = {
      sm: 'text-xl font-semibold',
      md: 'text-2xl font-bold',
      lg: 'text-3xl font-bold',
    };
    const tones: Record<KpiTone, string> = {
      default: 'text-slate-900 dark:text-white',
      success: 'text-emerald-800 dark:text-emerald-200',
      warn: 'text-amber-800 dark:text-amber-200',
      danger: 'text-rose-800 dark:text-rose-200',
      info: 'text-blue-800 dark:text-blue-200',
      violet: 'text-violet-800 dark:text-violet-200',
    };
    return `${sizeMap[this.size()]} ${tones[this.tone()]}`;
  }

  hintClass(): string {
    const tones: Record<KpiTone, string> = {
      default: 'text-slate-400 dark:text-slate-500',
      success: 'text-emerald-700/70 dark:text-emerald-400/70',
      warn: 'text-amber-700/70 dark:text-amber-400/70',
      danger: 'text-rose-700/70 dark:text-rose-400/70',
      info: 'text-blue-700/70 dark:text-blue-400/70',
      violet: 'text-violet-700/70 dark:text-violet-400/70',
    };
    return tones[this.tone()];
  }

  deltaClass(): string {
    const d = this.delta() || '';
    if (d.startsWith('-') || d.includes('▼')) {
      return 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300';
    }
    if (d.startsWith('+') || d.includes('▲')) {
      return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300';
    }
    return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
  }

  sparkColor(): 'emerald' | 'amber' | 'rose' | 'blue' | 'violet' | 'brand' | 'slate' {
    const map: Record<KpiTone, 'emerald' | 'amber' | 'rose' | 'blue' | 'violet' | 'brand' | 'slate'> = {
      default: 'brand', success: 'emerald', warn: 'amber',
      danger: 'rose', info: 'blue', violet: 'violet',
    };
    return map[this.tone()];
  }
}
