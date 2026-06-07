import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrPayrollPeriod,
  HrPayrollPeriodCreate,
  HrPayrollPeriodStatus,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-payroll-periods',
  imports: [CommonModule, FormsModule, RouterLink, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Períodos de nómina</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">
            Flujo: draft → calcular → aprobar → pagar → cerrar.
          </p>
        </div>
        <button (click)="openCreate()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Nuevo período
        </button>
      </header>

      <section class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Estado</span>
          <select [(ngModel)]="filterStatus" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            <option value="draft">Borrador</option>
            <option value="calculated">Calculado</option>
            <option value="approved">Aprobado</option>
            <option value="paid">Pagado</option>
            <option value="closed">Cerrado</option>
          </select>
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Año</span>
          <input type="number" min="2000" max="2100" [(ngModel)]="filterYear" (change)="load()"
            class="w-28 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
      </section>

      <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-2 font-medium">Código</th>
              <th class="text-left px-4 py-2 font-medium">Nombre</th>
              <th class="text-left px-4 py-2 font-medium">Período</th>
              <th class="text-right px-4 py-2 font-medium">Empleados</th>
              <th class="text-right px-4 py-2 font-medium">Devengado</th>
              <th class="text-right px-4 py-2 font-medium">Deducciones</th>
              <th class="text-right px-4 py-2 font-medium">Neto</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
              <th class="text-right px-4 py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="9" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (periods().length === 0) {
              <tr><td colspan="9" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin períodos.</td></tr>
            } @else {
              @for (p of paginated(); track p.id) {
                <tr>
                  <td class="px-4 py-2 font-mono text-xs">
                    <a [routerLink]="['/hr/payroll/periods', p.id]" class="text-brand-700 dark:text-brand-300 hover:underline">{{ p.code }}</a>
                  </td>
                  <td class="px-4 py-2">{{ p.name }}</td>
                  <td class="px-4 py-2 text-xs">{{ p.start_date }} → {{ p.end_date }}</td>
                  <td class="px-4 py-2 text-right">{{ p.employee_count }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs">$ {{ (+p.total_gross) | number:'1.0-0' }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs text-rose-600">$ {{ (+p.total_deductions) | number:'1.0-0' }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs font-semibold text-emerald-700 dark:text-emerald-300">$ {{ (+p.total_net) | number:'1.0-0' }}</td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(p.status)">{{ statusLabel(p.status) }}</span>
                  </td>
                  <td class="px-4 py-2 text-right whitespace-nowrap space-x-2">
                    @if (p.status === 'draft') {
                      <button (click)="calc(p)" type="button" class="text-xs text-brand-600 hover:underline">Calcular</button>
                      <button (click)="remove(p)" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                    }
                    @if (p.status === 'calculated') {
                      <button (click)="calc(p)" type="button" class="text-xs text-slate-600 dark:text-slate-400 hover:underline">Recalcular</button>
                      <button (click)="approve(p)" type="button" class="text-xs text-emerald-600 hover:underline">Aprobar</button>
                    }
                    @if (p.status === 'approved') {
                      <button (click)="pay(p)" type="button" class="text-xs text-emerald-600 hover:underline">Pagar</button>
                    }
                    @if (p.status === 'paid') {
                      <button (click)="close(p)" type="button" class="text-xs text-slate-600 dark:text-slate-400 hover:underline">Cerrar</button>
                    }
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="periods().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Nuevo período</h3>
            @if (formError()) { <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p> }
            <form (ngSubmit)="save()" class="space-y-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Código *</span>
                <input [(ngModel)]="form.code" name="code" required placeholder="PER-2026-06"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm uppercase" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombre *</span>
                <input [(ngModel)]="form.name" name="name" required placeholder="Junio 2026"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Frecuencia</span>
                <select [(ngModel)]="form.period_type" name="pt"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="monthly">Mensual</option>
                  <option value="biweekly">Quincenal</option>
                  <option value="weekly">Semanal</option>
                </select>
              </label>
              <div class="grid grid-cols-2 gap-3">
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Inicio *</span>
                  <input type="date" [(ngModel)]="form.start_date" name="sd" required
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Fin *</span>
                  <input type="date" [(ngModel)]="form.end_date" name="ed" required
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
              </div>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fecha de pago</span>
                <input type="date" [(ngModel)]="form.payment_date" name="pd"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <div class="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeForm(); $event.stopPropagation()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="saving()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ saving() ? 'Guardando...' : 'Crear período' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrPayrollPeriodsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  periods = signal<HrPayrollPeriod[]>([]);
  filterStatus = '';
  filterYear = new Date().getFullYear();

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.periods().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: HrPayrollPeriodCreate = this.emptyForm();

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    const params: { status?: string; year?: number } = { year: this.filterYear };
    if (this.filterStatus) params.status = this.filterStatus;
    this.hr.listPayrollPeriods(params).subscribe({
      next: (r) => { this.periods.set(r); this.page.set(0); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  emptyForm(): HrPayrollPeriodCreate {
    const today = new Date();
    const y = today.getFullYear();
    const m = today.getMonth() + 1;
    const monthName = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][m - 1];
    const start = new Date(y, m - 1, 1).toISOString().slice(0, 10);
    const end = new Date(y, m, 0).toISOString().slice(0, 10);
    return {
      code: `PER-${y}-${String(m).padStart(2, '0')}`,
      name: `${monthName} ${y}`,
      period_type: 'monthly',
      start_date: start,
      end_date: end,
      payment_date: end,
    };
  }

  openCreate(): void { this.form = this.emptyForm(); this.formError.set(''); this.formOpen.set(true); }
  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    this.saving.set(true);
    this.hr.createPayrollPeriod(this.form).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Creado', message: this.form.code });
        this.saving.set(false); this.formOpen.set(false); this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'No se pudo crear.');
      },
    });
  }

  calc(p: HrPayrollPeriod): void {
    if (!confirm(`¿Calcular nómina del período ${p.code}? Esto liquidará a todos los empleados activos.`)) return;
    this.hr.calculatePayroll(p.id).subscribe({
      next: (r) => {
        this.notify.show({ type: 'success', title: 'Calculado', message: `${r.employees_processed} empleados · Neto $ ${Math.round(+r.total_net).toLocaleString()}` });
        this.load();
      },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo calcular.' }),
    });
  }

  approve(p: HrPayrollPeriod): void {
    if (!confirm(`¿Aprobar la nómina ${p.code}?`)) return;
    this.hr.approvePayrollPeriod(p.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Aprobado', message: p.code }); this.load(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo aprobar.' }),
    });
  }

  pay(p: HrPayrollPeriod): void {
    const ref = prompt('Referencia de pago (opcional):') || undefined;
    this.hr.payPayrollPeriod(p.id, ref).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Pagado', message: p.code }); this.load(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo pagar.' }),
    });
  }

  close(p: HrPayrollPeriod): void {
    if (!confirm(`¿Cerrar definitivamente el período ${p.code}?`)) return;
    this.hr.closePayrollPeriod(p.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Cerrado', message: p.code }); this.load(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo cerrar.' }),
    });
  }

  remove(p: HrPayrollPeriod): void {
    if (!confirm(`¿Eliminar período ${p.code}?`)) return;
    this.hr.deletePayrollPeriod(p.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: p.code }); this.load(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo eliminar.' }),
    });
  }

  statusLabel(s: HrPayrollPeriodStatus): string {
    const map: Record<HrPayrollPeriodStatus, string> = {
      draft: 'Borrador', calculating: 'Calculando', calculated: 'Calculado',
      approved: 'Aprobado', paid: 'Pagado', closed: 'Cerrado', cancelled: 'Cancelado',
    };
    return map[s];
  }
  statusClass(s: HrPayrollPeriodStatus): string {
    const map: Record<HrPayrollPeriodStatus, string> = {
      draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      calculating: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      calculated: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      approved: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
      paid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      closed: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    };
    return map[s];
  }
}
