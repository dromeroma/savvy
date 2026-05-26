import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  MemorialAgingReport,
  MemorialOverdueDebtor,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-cartera',
  imports: [CommonModule, RouterLink],
  template: `
    <div class="p-4 sm:p-6 lg:p-8">
      <div class="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">Cartera</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Aging por antigüedad y lista de morosos. Recalcula para aplicar mora compuesta y
            suspender contratos con cuotas vencidas.
          </p>
        </div>
        <button (click)="recalculate()" [disabled]="recalculating()"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium disabled:bg-brand-300">
          {{ recalculating() ? 'Calculando…' : 'Recalcular cartera' }}
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-20">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-gray-600"></div>
        </div>
      } @else {
        <!-- Aging buckets -->
        @if (aging(); as a) {
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 mb-6">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-sm font-semibold text-gray-800 dark:text-white/90">Aging por antigüedad</h2>
              <span class="text-sm font-mono text-gray-700 dark:text-gray-300">
                Total: <span class="font-semibold">$ {{ (+a.total_balance) | number:'1.0-0' }}</span>
              </span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
              @for (b of a.buckets; track b.bucket) {
                <div class="rounded-lg p-3 border"
                  [ngClass]="bucketStyle(b.bucket)">
                  <div class="text-[11px] uppercase tracking-wider opacity-80">{{ bucketLabel(b.bucket) }}</div>
                  <div class="text-xl font-semibold mt-1 font-mono">$ {{ (+b.balance) | number:'1.0-0' }}</div>
                  <div class="text-xs opacity-80 mt-0.5">{{ b.invoices }} factura(s)</div>
                </div>
              }
            </div>
          </div>
        }

        <!-- Overdue list -->
        <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
          <div class="p-5 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-sm font-semibold text-gray-800 dark:text-white/90">Morosos</h2>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Contratos y servicios con facturas vencidas, ordenados por antigüedad de la deuda.
            </p>
          </div>
          @if (debtors().length === 0) {
            <div class="p-10 text-center">
              <p class="text-sm text-gray-500 dark:text-gray-400">No hay morosos. Excelente.</p>
            </div>
          } @else {
            <table class="w-full text-sm">
              <thead class="bg-gray-50 dark:bg-gray-700/30">
                <tr class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <th class="px-4 py-3">Código</th>
                  <th class="px-4 py-3">Responsable</th>
                  <th class="px-4 py-3">Contacto</th>
                  <th class="px-4 py-3 text-center">Facturas</th>
                  <th class="px-4 py-3 text-right">Días vencido</th>
                  <th class="px-4 py-3 text-right">Saldo</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                @for (d of debtors(); track d.code) {
                  <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                    <td class="px-4 py-3 font-mono text-xs">
                      @if (d.contract_id) {
                        <a [routerLink]="['/memorial/contracts', d.contract_id]" class="text-brand-500 hover:text-brand-600">
                          {{ d.code }}
                        </a>
                      } @else if (d.service_id) {
                        <a [routerLink]="['/memorial/services', d.service_id]" class="text-brand-500 hover:text-brand-600">
                          {{ d.code }}
                        </a>
                      } @else {
                        {{ d.code }}
                      }
                    </td>
                    <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ d.name }}</td>
                    <td class="px-4 py-3 text-xs text-gray-700 dark:text-gray-300">
                      @if (d.phone) { <div class="font-mono">{{ d.phone }}</div> }
                      @if (d.email) { <div class="font-mono text-gray-500">{{ d.email }}</div> }
                      @if (!d.phone && !d.email) { <span class="text-gray-400 italic">Sin contacto</span> }
                    </td>
                    <td class="px-4 py-3 text-center text-gray-700 dark:text-gray-300">{{ d.overdue_invoices }}</td>
                    <td class="px-4 py-3 text-right text-red-600 font-semibold">{{ d.days_overdue }} días</td>
                    <td class="px-4 py-3 text-right font-mono text-xs font-semibold text-red-600">
                      $ {{ (+d.total_balance) | number:'1.0-0' }}
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          }
        </div>
      }
    </div>
  `,
})
export class MemorialCarteraComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  aging = signal<MemorialAgingReport | null>(null);
  debtors = signal<MemorialOverdueDebtor[]>([]);
  recalculating = signal(false);

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    let pending = 2;
    const done = () => {
      pending--;
      if (pending === 0) this.loading.set(false);
    };
    this.memorial.cartera_aging().subscribe({
      next: (a) => { this.aging.set(a); done(); },
      error: () => done(),
    });
    this.memorial.cartera_overdue().subscribe({
      next: (d) => { this.debtors.set(d); done(); },
      error: () => done(),
    });
  }

  recalculate(): void {
    if (!confirm('Recalcular cartera: aplica intereses de mora a facturas vencidas y suspende contratos con 3+ cuotas vencidas. ¿Continuar?')) return;
    this.recalculating.set(true);
    this.memorial.recalcCartera().subscribe({
      next: (r) => {
        this.recalculating.set(false);
        this.notify.show({
          type: 'success', title: 'Cartera recalculada',
          message: `${r.invoices_marked_overdue} vencidas, ${r.contracts_suspended} contratos suspendidos, $ ${Math.round(+r.total_interest_applied).toLocaleString('es-CO')} en intereses.`,
        });
        this.load();
      },
      error: () => {
        this.recalculating.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo recalcular.' });
      },
    });
  }

  bucketLabel(b: string): string {
    switch (b) {
      case 'current': return 'Al día';
      case '0_30': return '1-30 días';
      case '31_60': return '31-60 días';
      case '61_90': return '61-90 días';
      case '90_plus': return '+90 días';
      default: return b;
    }
  }

  bucketStyle(b: string): string {
    switch (b) {
      case 'current': return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300';
      case '0_30': return 'border-amber-200 dark:border-amber-700/40 bg-amber-50/60 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300';
      case '31_60': return 'border-orange-200 dark:border-orange-700/40 bg-orange-50/60 dark:bg-orange-500/10 text-orange-700 dark:text-orange-300';
      case '61_90': return 'border-red-200 dark:border-red-700/40 bg-red-50/60 dark:bg-red-500/10 text-red-700 dark:text-red-300';
      case '90_plus': return 'border-red-300 dark:border-red-600/50 bg-red-100/70 dark:bg-red-500/20 text-red-800 dark:text-red-200';
      default: return 'border-gray-200 dark:border-gray-700';
    }
  }
}
