import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SparklineComponent } from './sparkline.component';

export type HeroTone = 'brand' | 'emerald' | 'violet' | 'amber' | 'slate';

/**
 * Tarjeta HERO destacada con gradiente, número grande y sparkline opcional.
 * Pensada para LA métrica más importante del dashboard.
 */
@Component({
  selector: 'app-hero-metric-card',
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
      <a [routerLink]="link()" [class]="rootClass() + ' hover:scale-[1.01] transition'">
        <ng-container *ngTemplateOutlet="content"></ng-container>
      </a>
    </ng-template>

    <ng-template #content>
      <div class="relative h-full flex flex-col">
        <!-- Glow decorativo -->
        <div class="pointer-events-none absolute -top-20 -right-20 w-64 h-64 rounded-full opacity-20 blur-3xl"
          [class]="glowClass()"></div>

        <div class="relative z-10 flex items-start justify-between gap-3">
          <div>
            <div class="text-xs font-medium uppercase tracking-wider" [class]="labelClass()">
              {{ label() }}
            </div>
            @if (subtitle()) {
              <div class="text-[11px] mt-0.5" [class]="subtitleClass()">
                {{ subtitle() }}
              </div>
            }
          </div>
          @if (icon()) {
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg" [class]="iconClass()">
              {{ icon() }}
            </div>
          }
        </div>

        <div class="relative z-10 mt-4 sm:mt-6">
          <div class="text-4xl sm:text-5xl font-bold tabular-nums leading-none" [class]="valueClass()">
            {{ value() }}
          </div>
          <div class="flex items-baseline gap-3 mt-2.5">
            @if (delta()) {
              <span class="text-[11px] font-semibold px-2 py-0.5 rounded" [class]="deltaClass()">
                {{ delta() }}
              </span>
            }
            @if (hint()) {
              <span class="text-xs" [class]="hintClass()">{{ hint() }}</span>
            }
          </div>
        </div>

        @if (series() && series()!.length >= 2) {
          <div class="relative z-10 mt-auto pt-6 h-16">
            <app-sparkline [data]="series()!" [color]="sparkColor()" />
          </div>
        }
      </div>
    </ng-template>
  `,
})
export class HeroMetricCardComponent {
  label = input.required<string>();
  value = input.required<string | number>();
  subtitle = input<string | null>(null);
  hint = input<string | null>(null);
  delta = input<string | null>(null);
  tone = input<HeroTone>('brand');
  icon = input<string | null>(null);
  series = input<number[] | null>(null);
  link = input<string | null>(null);

  rootClass(): string {
    const base = 'rounded-3xl border p-6 sm:p-7 overflow-hidden relative h-full min-h-[200px] block';
    const tones: Record<HeroTone, string> = {
      brand: 'bg-gradient-to-br from-brand-50 via-white to-brand-50/40 dark:from-brand-950/40 dark:via-slate-900 dark:to-slate-900 border-brand-200 dark:border-brand-900/60',
      emerald: 'bg-gradient-to-br from-emerald-50 via-white to-emerald-50/40 dark:from-emerald-950/40 dark:via-slate-900 dark:to-slate-900 border-emerald-200 dark:border-emerald-900/60',
      violet: 'bg-gradient-to-br from-violet-50 via-white to-violet-50/40 dark:from-violet-950/40 dark:via-slate-900 dark:to-slate-900 border-violet-200 dark:border-violet-900/60',
      amber: 'bg-gradient-to-br from-amber-50 via-white to-amber-50/40 dark:from-amber-950/40 dark:via-slate-900 dark:to-slate-900 border-amber-200 dark:border-amber-900/60',
      slate: 'bg-gradient-to-br from-slate-50 via-white to-slate-50/40 dark:from-slate-900 dark:via-slate-900 dark:to-slate-950 border-slate-200 dark:border-slate-800',
    };
    return `${base} ${tones[this.tone()]}`;
  }

  glowClass(): string {
    const tones: Record<HeroTone, string> = {
      brand: 'bg-brand-500', emerald: 'bg-emerald-500', violet: 'bg-violet-500',
      amber: 'bg-amber-500', slate: 'bg-slate-500',
    };
    return tones[this.tone()];
  }

  iconClass(): string {
    const tones: Record<HeroTone, string> = {
      brand: 'bg-brand-500/15 text-brand-600 dark:text-brand-300',
      emerald: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300',
      violet: 'bg-violet-500/15 text-violet-600 dark:text-violet-300',
      amber: 'bg-amber-500/15 text-amber-600 dark:text-amber-300',
      slate: 'bg-slate-500/15 text-slate-600 dark:text-slate-300',
    };
    return tones[this.tone()];
  }

  labelClass(): string {
    const tones: Record<HeroTone, string> = {
      brand: 'text-brand-700 dark:text-brand-300',
      emerald: 'text-emerald-700 dark:text-emerald-300',
      violet: 'text-violet-700 dark:text-violet-300',
      amber: 'text-amber-700 dark:text-amber-300',
      slate: 'text-slate-600 dark:text-slate-400',
    };
    return tones[this.tone()];
  }

  subtitleClass(): string {
    const tones: Record<HeroTone, string> = {
      brand: 'text-brand-600/70 dark:text-brand-400/70',
      emerald: 'text-emerald-600/70 dark:text-emerald-400/70',
      violet: 'text-violet-600/70 dark:text-violet-400/70',
      amber: 'text-amber-600/70 dark:text-amber-400/70',
      slate: 'text-slate-500 dark:text-slate-500',
    };
    return tones[this.tone()];
  }

  valueClass(): string {
    const tones: Record<HeroTone, string> = {
      brand: 'text-brand-900 dark:text-white',
      emerald: 'text-emerald-900 dark:text-white',
      violet: 'text-violet-900 dark:text-white',
      amber: 'text-amber-900 dark:text-white',
      slate: 'text-slate-900 dark:text-white',
    };
    return tones[this.tone()];
  }

  hintClass(): string {
    return 'text-slate-600 dark:text-slate-400';
  }

  deltaClass(): string {
    const d = this.delta() || '';
    if (d.startsWith('-') || d.includes('▼')) {
      return 'bg-rose-100/80 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300';
    }
    if (d.startsWith('+') || d.includes('▲')) {
      return 'bg-emerald-100/80 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300';
    }
    return 'bg-slate-200/60 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
  }

  sparkColor(): 'emerald' | 'amber' | 'rose' | 'blue' | 'violet' | 'brand' | 'slate' {
    const map: Record<HeroTone, 'emerald' | 'amber' | 'violet' | 'brand' | 'slate'> = {
      brand: 'brand', emerald: 'emerald', violet: 'violet',
      amber: 'amber', slate: 'slate',
    };
    return map[this.tone()];
  }
}
