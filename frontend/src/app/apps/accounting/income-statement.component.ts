import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';
import { DatePickerComponent } from '../../shared/components/form/date-picker/date-picker.component';

interface AccountLine {
  code: string;
  name: string;
  amount: number;
}

interface IncomeStatementData {
  revenues: AccountLine[];
  expenses: AccountLine[];
  total_revenue: number;
  total_expense: number;
  net_income: number;
}

@Component({
  selector: 'app-income-statement',
  imports: [CommonModule, FormsModule, DatePickerComponent],
  template: `
    <div>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Estado de Resultados</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Ingresos vs gastos del periodo</p>
        </div>
      </div>

      <!-- Date Range Selector -->
      <div class="flex flex-col sm:flex-row gap-3 mb-6">
        <div class="flex flex-col gap-1">
          <app-date-picker
            id="is_start_date"
            label="Fecha inicio"
            [defaultDate]="startDate"
            (dateChange)="startDate = $event"
          />
        </div>
        <div class="flex flex-col gap-1">
          <app-date-picker
            id="is_end_date"
            label="Fecha fin"
            [defaultDate]="endDate"
            (dateChange)="endDate = $event"
          />
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
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <div class="p-6 sm:p-8">
            <!-- Report Title -->
            <div class="text-center mb-8">
              <h3 class="text-lg font-bold text-gray-800 dark:text-white/90">Estado de Resultados</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">Del {{ startDate }} al {{ endDate }}</p>
            </div>

            <!-- Revenues Section -->
            <div class="mb-6">
              <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                Ingresos
              </h4>
              @for (item of data()!.revenues; track item.code) {
                <div class="flex items-center justify-between py-2 px-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded transition">
                  <div class="flex items-center gap-3">
                    <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ item.code }}</span>
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ item.name }}</span>
                  </div>
                  <span class="font-mono text-sm text-gray-800 dark:text-white/90">{{ formatAmount(item.amount) }}</span>
                </div>
              }
              @if (data()!.revenues.length === 0) {
                <p class="text-sm text-gray-400 dark:text-gray-500 py-2 px-2">Sin ingresos en este periodo</p>
              }
              <div class="flex items-center justify-between py-2 px-2 mt-1 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-semibold text-gray-800 dark:text-white/90">Total Ingresos</span>
                <span class="font-mono text-sm font-bold text-green-600 dark:text-green-400">{{ formatAmount(data()!.total_revenue) }}</span>
              </div>
            </div>

            <!-- Expenses Section -->
            <div class="mb-6">
              <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                Gastos
              </h4>
              @for (item of data()!.expenses; track item.code) {
                <div class="flex items-center justify-between py-2 px-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded transition">
                  <div class="flex items-center gap-3">
                    <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ item.code }}</span>
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ item.name }}</span>
                  </div>
                  <span class="font-mono text-sm text-gray-800 dark:text-white/90">{{ formatAmount(item.amount) }}</span>
                </div>
              }
              @if (data()!.expenses.length === 0) {
                <p class="text-sm text-gray-400 dark:text-gray-500 py-2 px-2">Sin gastos en este periodo</p>
              }
              <div class="flex items-center justify-between py-2 px-2 mt-1 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-semibold text-gray-800 dark:text-white/90">Total Gastos</span>
                <span class="font-mono text-sm font-bold text-red-600 dark:text-red-400">{{ formatAmount(data()!.total_expense) }}</span>
              </div>
            </div>

            <!-- Net Income -->
            <div class="border-t-2 border-gray-300 dark:border-gray-600 pt-4 mt-4">
              <div class="flex items-center justify-between px-2">
                <span class="text-base font-bold text-gray-800 dark:text-white/90">Utilidad / Perdida Neta</span>
                <span class="font-mono text-lg font-bold"
                  [ngClass]="data()!.net_income >= 0
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'">
                  {{ formatAmount(data()!.net_income) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class IncomeStatementComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  data = signal<IncomeStatementData | null>(null);
  loading = signal(false);

  startDate = '';
  endDate = '';

  ngOnInit(): void {
    const now = new Date();
    this.startDate = `${now.getFullYear()}-01-01`;
    this.endDate = this.toISODate(now);
    this.loadReport();
  }

  loadReport(): void {
    if (!this.startDate || !this.endDate) return;

    this.loading.set(true);
    this.api.get<any>('/accounting/reports/income-statement', {
      start_date: this.startDate,
      end_date: this.endDate,
    }).subscribe({
      next: (raw) => {
        const parsed: IncomeStatementData = {
          revenues: (raw.revenues || []).map((r: any) => ({ ...r, amount: Number(r.amount) || 0 })),
          expenses: (raw.expenses || []).map((e: any) => ({ ...e, amount: Number(e.amount) || 0 })),
          total_revenue: Number(raw.total_revenue) || 0,
          total_expense: Number(raw.total_expense) || 0,
          net_income: Number(raw.net_income) || 0,
        };
        this.data.set(parsed);
        this.loading.set(false);
      },
      error: () => {
        this.data.set(null);
        this.loading.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar el estado de resultados' });
      },
    });
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
