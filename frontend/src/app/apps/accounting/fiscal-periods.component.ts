import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface FiscalPeriod {
  id: string;
  year: number;
  month: number;
  app_code: string | null;
  start_date: string;
  end_date: string;
  status: string;
  closed_at: string | null;
}

@Component({
  selector: 'app-fiscal-periods',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Periodos Fiscales</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Gestion de periodos contables mensuales</p>
        </div>
      </div>

      <!-- Loading -->
      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          @if (periods().length > 0) {
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Año</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Mes</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">App</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Estado</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden sm:table-cell">Fecha cierre</th>
                    <th class="text-right px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  @for (period of periods(); track period.id) {
                    <tr class="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                      <td class="px-6 py-4 font-mono text-gray-800 dark:text-white/90 font-medium">{{ period.year }}</td>
                      <td class="px-6 py-4 text-gray-800 dark:text-white/90">{{ getMonthName(period.month) }}</td>
                      <td class="px-6 py-4">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                          [ngClass]="{
                            'bg-purple-50 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400': period.app_code === 'church',
                            'bg-blue-50 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400': period.app_code === 'pos',
                            'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400': !period.app_code
                          }">
                          {{ period.app_code || 'Global' }}
                        </span>
                      </td>
                      <td class="px-6 py-4">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                          [ngClass]="period.status === 'open'
                            ? 'bg-green-50 text-green-700 dark:bg-green-500/20 dark:text-green-400'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400'">
                          {{ period.status === 'open' ? 'Abierto' : 'Cerrado' }}
                        </span>
                      </td>
                      <td class="px-6 py-4 text-gray-600 dark:text-gray-300 hidden sm:table-cell">
                        {{ period.closed_at ? (period.closed_at | date:'dd/MM/yyyy HH:mm') : '-' }}
                      </td>
                      <td class="px-6 py-4 text-right">
                        @if (period.status === 'open') {
                          <button (click)="confirmClose(period)"
                            [disabled]="closing()"
                            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg
                              bg-amber-50 text-amber-700 hover:bg-amber-100
                              dark:bg-amber-500/20 dark:text-amber-400 dark:hover:bg-amber-500/30
                              transition disabled:opacity-50 disabled:cursor-not-allowed">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                            </svg>
                            Cerrar periodo
                          </button>
                        }
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          } @else {
            <div class="px-6 py-12 text-center">
              <svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p class="text-gray-400 dark:text-gray-500 text-sm">No hay periodos fiscales registrados.</p>
            </div>
          }
        </div>
      }

      <!-- Confirmation Modal -->
      @if (showConfirm()) {
        <div class="fixed inset-0 z-9999 flex items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50 dark:bg-black/70" (click)="cancelClose()"></div>
          <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md p-6">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90 mb-2">Cerrar periodo</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Esta a punto de cerrar el periodo
              <span class="font-semibold text-gray-800 dark:text-white/90">{{ getMonthName(periodToClose()?.month ?? 0) }} {{ periodToClose()?.year }}</span>.
              Esta accion no se puede deshacer.
            </p>
            <div class="flex justify-end gap-3">
              <button (click)="cancelClose()"
                class="px-4 py-2 text-sm font-medium rounded-lg border border-gray-200 dark:border-gray-600
                  text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                Cancelar
              </button>
              <button (click)="closePeriod()"
                [disabled]="closing()"
                class="px-4 py-2 text-sm font-medium rounded-lg
                  bg-amber-600 text-white hover:bg-amber-700
                  dark:bg-amber-500 dark:hover:bg-amber-600
                  transition disabled:opacity-50 disabled:cursor-not-allowed">
                @if (closing()) {
                  <div class="flex items-center gap-2">
                    <div class="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>
                    Cerrando...
                  </div>
                } @else {
                  Confirmar cierre
                }
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class FiscalPeriodsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  periods = signal<FiscalPeriod[]>([]);
  loading = signal(true);
  closing = signal(false);
  showConfirm = signal(false);
  periodToClose = signal<FiscalPeriod | null>(null);

  private readonly monthNames = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  ngOnInit(): void {
    this.loadPeriods();
  }

  loadPeriods(): void {
    this.loading.set(true);
    this.api.get<FiscalPeriod[]>('/accounting/fiscal-periods').subscribe({
      next: (data) => {
        this.periods.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.periods.set([]);
        this.loading.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudieron cargar los periodos fiscales' });
      },
    });
  }

  getMonthName(month: number): string {
    return this.monthNames[month] || '';
  }

  confirmClose(period: FiscalPeriod): void {
    this.periodToClose.set(period);
    this.showConfirm.set(true);
  }

  cancelClose(): void {
    this.showConfirm.set(false);
    this.periodToClose.set(null);
  }

  closePeriod(): void {
    const period = this.periodToClose();
    if (!period) return;

    this.closing.set(true);
    this.api.post<FiscalPeriod>(`/accounting/fiscal-periods/${period.id}/close`, {}).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Periodo cerrado', message: `${this.getMonthName(period.month)} ${period.year} cerrado exitosamente` });
        this.closing.set(false);
        this.showConfirm.set(false);
        this.periodToClose.set(null);
        this.loadPeriods();
      },
      error: (err) => {
        const msg = err?.error?.detail || 'No se pudo cerrar el periodo';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
        this.closing.set(false);
      },
    });
  }
}
