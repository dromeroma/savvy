import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface AccountLine {
  account_code: string;
  account_name: string;
  total: number;
}

interface BalanceSheetData {
  assets: AccountLine[];
  liabilities: AccountLine[];
  equity: AccountLine[];
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
}

@Component({
  selector: 'app-balance-sheet',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Balance General</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Activos, pasivos y patrimonio</p>
        </div>
      </div>

      <!-- Date Selector -->
      <div class="flex flex-col sm:flex-row gap-3 mb-6">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-600 dark:text-gray-400">Fecha de corte</label>
          <input type="date" [(ngModel)]="asOfDate"
            class="h-11 px-4 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-theme-xs text-gray-800 dark:text-white/90 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
        </div>
        <div class="flex items-end">
          <button (click)="loadReport()" [disabled]="loading()"
            class="h-11 px-5 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition disabled:opacity-50 disabled:cursor-not-allowed">
            Consultar
          </button>
        </div>
      </div>

      <!-- Loading -->
      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (data()) {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="p-6 sm:p-8">
            <!-- Report Title -->
            <div class="text-center mb-8">
              <h3 class="text-lg font-bold text-gray-800 dark:text-white/90">Balance General</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">Al {{ asOfDate }}</p>
            </div>

            <!-- Balance Check -->
            <div class="mb-6 px-2">
              @if (isBalanced()) {
                <div class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  Cuadrado: Activos = Pasivos + Patrimonio
                </div>
              } @else {
                <div class="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                  </svg>
                  Descuadre: Activos ({{ formatAmount(data()!.total_assets) }}) != Pasivos + Patrimonio ({{ formatAmount(data()!.total_liabilities + data()!.total_equity) }})
                </div>
              }
            </div>

            <!-- Assets Section -->
            <div class="mb-6">
              <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                Activos
              </h4>
              @for (item of data()!.assets; track item.account_code) {
                <div class="flex items-center justify-between py-2 px-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded transition">
                  <div class="flex items-center gap-3">
                    <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ item.account_code }}</span>
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ item.account_name }}</span>
                  </div>
                  <span class="font-mono text-sm text-gray-800 dark:text-white/90">{{ formatAmount(item.total) }}</span>
                </div>
              }
              @if (data()!.assets.length === 0) {
                <p class="text-sm text-gray-400 dark:text-gray-500 py-2 px-2">Sin activos registrados</p>
              }
              <div class="flex items-center justify-between py-2 px-2 mt-1 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-semibold text-gray-800 dark:text-white/90">Total Activos</span>
                <span class="font-mono text-sm font-bold text-blue-600 dark:text-blue-400">{{ formatAmount(data()!.total_assets) }}</span>
              </div>
            </div>

            <!-- Liabilities Section -->
            <div class="mb-6">
              <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                Pasivos
              </h4>
              @for (item of data()!.liabilities; track item.account_code) {
                <div class="flex items-center justify-between py-2 px-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded transition">
                  <div class="flex items-center gap-3">
                    <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ item.account_code }}</span>
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ item.account_name }}</span>
                  </div>
                  <span class="font-mono text-sm text-gray-800 dark:text-white/90">{{ formatAmount(item.total) }}</span>
                </div>
              }
              @if (data()!.liabilities.length === 0) {
                <p class="text-sm text-gray-400 dark:text-gray-500 py-2 px-2">Sin pasivos registrados</p>
              }
              <div class="flex items-center justify-between py-2 px-2 mt-1 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-semibold text-gray-800 dark:text-white/90">Total Pasivos</span>
                <span class="font-mono text-sm font-bold text-red-600 dark:text-red-400">{{ formatAmount(data()!.total_liabilities) }}</span>
              </div>
            </div>

            <!-- Equity Section -->
            <div class="mb-6">
              <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                Patrimonio
              </h4>
              @for (item of data()!.equity; track item.account_code) {
                <div class="flex items-center justify-between py-2 px-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded transition">
                  <div class="flex items-center gap-3">
                    <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ item.account_code }}</span>
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ item.account_name }}</span>
                  </div>
                  <span class="font-mono text-sm text-gray-800 dark:text-white/90">{{ formatAmount(item.total) }}</span>
                </div>
              }
              @if (data()!.equity.length === 0) {
                <p class="text-sm text-gray-400 dark:text-gray-500 py-2 px-2">Sin patrimonio registrado</p>
              }
              <div class="flex items-center justify-between py-2 px-2 mt-1 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-semibold text-gray-800 dark:text-white/90">Total Patrimonio</span>
                <span class="font-mono text-sm font-bold text-purple-600 dark:text-purple-400">{{ formatAmount(data()!.total_equity) }}</span>
              </div>
            </div>

            <!-- Totals Summary -->
            <div class="border-t-2 border-gray-300 dark:border-gray-600 pt-4 mt-4 space-y-2">
              <div class="flex items-center justify-between px-2">
                <span class="text-sm font-bold text-gray-800 dark:text-white/90">Total Activos</span>
                <span class="font-mono text-base font-bold text-blue-600 dark:text-blue-400">{{ formatAmount(data()!.total_assets) }}</span>
              </div>
              <div class="flex items-center justify-between px-2">
                <span class="text-sm font-bold text-gray-800 dark:text-white/90">Total Pasivos + Patrimonio</span>
                <span class="font-mono text-base font-bold text-gray-800 dark:text-white/90">{{ formatAmount(data()!.total_liabilities + data()!.total_equity) }}</span>
              </div>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class BalanceSheetComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  data = signal<BalanceSheetData | null>(null);
  loading = signal(false);

  asOfDate = '';

  ngOnInit(): void {
    const now = new Date();
    this.asOfDate = this.toISODate(now);
    this.loadReport();
  }

  loadReport(): void {
    if (!this.asOfDate) return;

    this.loading.set(true);
    this.api.get<any>('/accounting/reports/balance-sheet', {
      as_of_date: this.asOfDate,
    }).subscribe({
      next: (raw) => {
        const parsed: BalanceSheetData = {
          assets: (raw.assets || []).map((a: any) => ({ ...a, total: Number(a.total) || 0 })),
          liabilities: (raw.liabilities || []).map((l: any) => ({ ...l, total: Number(l.total) || 0 })),
          equity: (raw.equity || []).map((e: any) => ({ ...e, total: Number(e.total) || 0 })),
          total_assets: Number(raw.total_assets) || 0,
          total_liabilities: Number(raw.total_liabilities) || 0,
          total_equity: Number(raw.total_equity) || 0,
        };
        this.data.set(parsed);
        this.loading.set(false);
      },
      error: () => {
        this.data.set(null);
        this.loading.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar el balance general' });
      },
    });
  }

  isBalanced(): boolean {
    const d = this.data();
    if (!d) return false;
    return Math.abs(d.total_assets - (d.total_liabilities + d.total_equity)) < 0.01;
  }

  formatAmount(value: number): string {
    return '$ ' + value.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  private toISODate(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}
