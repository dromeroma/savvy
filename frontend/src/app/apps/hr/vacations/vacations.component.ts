import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrEmployeeListItem,
  HrVacationBalance,
  HrVacationRequest,
  HrVacationRequestCreate,
  HrVacationStatus,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

type Tab = 'requests' | 'balances';

@Component({
  selector: 'app-hr-vacations',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Vacaciones</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">Solicitudes con aprobación + saldos por empleado y año.</p>
        </div>
        <div class="flex gap-2">
          <button (click)="accrueMonthly()" type="button" [disabled]="accruing()"
            class="rounded-md border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 disabled:opacity-50">
            {{ accruing() ? '...' : 'Causar mes' }}
          </button>
          <button (click)="openCreate()" type="button"
            class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            + Solicitud
          </button>
        </div>
      </header>

      <nav class="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        @for (t of tabs; track t.value) {
          <button type="button" (click)="tab.set(t.value)"
            class="px-4 py-2 text-sm border-b-2 -mb-px"
            [class.border-brand-600]="tab() === t.value"
            [class.text-brand-700]="tab() === t.value"
            [class.dark:text-brand-300]="tab() === t.value"
            [class.border-transparent]="tab() !== t.value"
            [class.text-slate-600]="tab() !== t.value"
            [class.dark:text-slate-400]="tab() !== t.value">
            {{ t.label }}
          </button>
        }
      </nav>

      @switch (tab()) {
        @case ('requests') {
          <section class="flex flex-wrap items-end gap-3">
            <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
              <span class="mb-1">Estado</span>
              <select [(ngModel)]="filterStatus" (change)="load()"
                class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                <option value="">— Todos —</option>
                <option value="pending">Pendiente</option>
                <option value="approved">Aprobado</option>
                <option value="rejected">Rechazado</option>
                <option value="cancelled">Cancelado</option>
                <option value="completed">Completado</option>
              </select>
            </label>
            <button (click)="load()" type="button"
              class="rounded-md border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-700 dark:text-slate-300">Refrescar</button>
          </section>

          <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-4 py-2 font-medium">N°</th>
                  <th class="text-left px-4 py-2 font-medium">Empleado</th>
                  <th class="text-left px-4 py-2 font-medium">Tipo</th>
                  <th class="text-left px-4 py-2 font-medium">Inicio</th>
                  <th class="text-left px-4 py-2 font-medium">Fin</th>
                  <th class="text-right px-4 py-2 font-medium">Días</th>
                  <th class="text-left px-4 py-2 font-medium">Estado</th>
                  <th class="text-right px-4 py-2 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @if (loading()) {
                  <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
                } @else if (requests().length === 0) {
                  <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin solicitudes.</td></tr>
                } @else {
                  @for (r of paginatedRequests(); track r.id) {
                    <tr>
                      <td class="px-4 py-2 font-mono text-xs">{{ r.request_number }}</td>
                      <td class="px-4 py-2 text-xs">{{ employeeName(r.employee_id) }}</td>
                      <td class="px-4 py-2 text-xs">{{ typeLabel(r.request_type) }}</td>
                      <td class="px-4 py-2 text-xs">{{ r.start_date }}</td>
                      <td class="px-4 py-2 text-xs">{{ r.end_date }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ r.days_count }}</td>
                      <td class="px-4 py-2">
                        <span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(r.status)">{{ statusLabel(r.status) }}</span>
                      </td>
                      <td class="px-4 py-2 text-right whitespace-nowrap space-x-2">
                        @if (r.status === 'pending') {
                          <button (click)="approve(r)" type="button" class="text-xs text-emerald-600 hover:underline">Aprobar</button>
                          <button (click)="reject(r)" type="button" class="text-xs text-rose-600 hover:underline">Rechazar</button>
                        }
                        @if (r.status === 'pending' || r.status === 'approved') {
                          <button (click)="cancel(r)" type="button" class="text-xs text-slate-600 dark:text-slate-400 hover:underline">Cancelar</button>
                        }
                      </td>
                    </tr>
                  }
                }
              </tbody>
            </table>
            <app-pagination [totalItems]="requests().length" [(page)]="pageReq" [(pageSize)]="pageSize" />
          </section>
        }

        @case ('balances') {
          <section class="flex flex-wrap items-end gap-3">
            <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
              <span class="mb-1">Año</span>
              <input type="number" min="2000" max="2100" [(ngModel)]="filterYear" (change)="loadBalances()"
                class="w-28 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
            </label>
            <button (click)="loadBalances()" type="button"
              class="rounded-md border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-700 dark:text-slate-300">Refrescar</button>
          </section>

          <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-4 py-2 font-medium">Empleado</th>
                  <th class="text-right px-4 py-2 font-medium">Año</th>
                  <th class="text-right px-4 py-2 font-medium">Causados</th>
                  <th class="text-right px-4 py-2 font-medium">Disfrutados</th>
                  <th class="text-right px-4 py-2 font-medium">Pendientes</th>
                  <th class="text-right px-4 py-2 font-medium">Compensados</th>
                  <th class="text-right px-4 py-2 font-medium">Disponibles</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @if (loadingBal()) {
                  <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
                } @else if (balances().length === 0) {
                  <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin saldos para este año.</td></tr>
                } @else {
                  @for (b of paginatedBalances(); track b.id) {
                    <tr>
                      <td class="px-4 py-2 text-xs">{{ employeeName(b.employee_id) }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ b.period_year }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ b.days_accrued }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ b.days_taken }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ b.days_pending }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ b.days_compensated }}</td>
                      <td class="px-4 py-2 text-right font-mono font-semibold text-emerald-700 dark:text-emerald-300">
                        {{ available(b) }}
                      </td>
                    </tr>
                  }
                }
              </tbody>
            </table>
            <app-pagination [totalItems]="balances().length" [(page)]="pageBal" [(pageSize)]="pageSize" />
          </section>
        }
      }

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Nueva solicitud</h3>
            @if (formError()) { <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p> }
            <form (ngSubmit)="save()" class="space-y-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Empleado *</span>
                <select [(ngModel)]="form.employee_id" name="eid" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="">— Selecciona —</option>
                  @for (e of employees(); track e.id) {
                    <option [value]="e.id">{{ e.first_name }} {{ e.last_name }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo</span>
                <select [(ngModel)]="form.request_type" name="rt"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="paid">Disfrutadas (pagadas)</option>
                  <option value="compensation">Compensadas en dinero</option>
                  <option value="unpaid">Sin pago</option>
                </select>
              </label>
              <div class="grid grid-cols-2 gap-3">
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Inicio *</span>
                  <input type="date" [(ngModel)]="form.start_date" name="sd" required (change)="updateDays()"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Fin *</span>
                  <input type="date" [(ngModel)]="form.end_date" name="ed" required (change)="updateDays()"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
              </div>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Días *</span>
                <input type="number" step="0.5" min="0" [(ngModel)]="form.days_count" name="dc" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              @if (form.request_type === 'compensation') {
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Monto compensación</span>
                  <input type="number" step="1000" min="0" [(ngModel)]="form.compensation_amount" name="ca"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
              }
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Motivo</span>
                <textarea [(ngModel)]="form.request_reason" name="rr" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
              <div class="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeForm()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="saving()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ saving() ? 'Guardando...' : 'Crear solicitud' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrVacationsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  readonly tabs: { value: Tab; label: string }[] = [
    { value: 'requests', label: 'Solicitudes' },
    { value: 'balances', label: 'Saldos' },
  ];

  tab = signal<Tab>('requests');
  loading = signal(true);
  loadingBal = signal(true);
  accruing = signal(false);

  requests = signal<HrVacationRequest[]>([]);
  balances = signal<HrVacationBalance[]>([]);
  employees = signal<HrEmployeeListItem[]>([]);

  filterStatus = '';
  filterYear = new Date().getFullYear();

  pageSize = signal(20);
  pageReq = signal(0);
  pageBal = signal(0);
  paginatedRequests = computed(() => {
    const s = this.pageReq() * this.pageSize();
    return this.requests().slice(s, s + this.pageSize());
  });
  paginatedBalances = computed(() => {
    const s = this.pageBal() * this.pageSize();
    return this.balances().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: HrVacationRequestCreate = this.emptyForm();

  constructor() {
    effect(() => { this.requests(); this.pageReq.set(0); }, { allowSignalWrites: true });
    effect(() => { this.balances(); this.pageBal.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    this.hr.listEmployees().subscribe({ next: (r) => this.employees.set(r) });
    this.load();
    this.loadBalances();
  }

  load(): void {
    this.loading.set(true);
    const params: { status?: string } = {};
    if (this.filterStatus) params.status = this.filterStatus;
    this.hr.listVacationRequests(params).subscribe({
      next: (r) => { this.requests.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  loadBalances(): void {
    this.loadingBal.set(true);
    this.hr.listVacationBalances(this.filterYear).subscribe({
      next: (r) => { this.balances.set(r); this.loadingBal.set(false); },
      error: () => { this.loadingBal.set(false); },
    });
  }

  accrueMonthly(): void {
    this.accruing.set(true);
    this.hr.runMonthlyAccrual(1.25).subscribe({
      next: (r) => {
        this.accruing.set(false);
        this.notify.show({ type: 'success', title: 'Causado', message: `${r.accrued_employees} empleados` });
        this.loadBalances();
      },
      error: () => { this.accruing.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo causar.' }); },
    });
  }

  emptyForm(): HrVacationRequestCreate {
    return {
      employee_id: '', request_type: 'paid',
      start_date: new Date().toISOString().slice(0, 10),
      end_date: new Date().toISOString().slice(0, 10),
      days_count: '1', request_reason: null,
    };
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }
  closeForm(): void { this.formOpen.set(false); }

  updateDays(): void {
    if (!this.form.start_date || !this.form.end_date) return;
    const s = new Date(this.form.start_date);
    const e = new Date(this.form.end_date);
    const diff = Math.max(0, (e.getTime() - s.getTime()) / 86400000 + 1);
    this.form.days_count = String(diff);
  }

  save(): void {
    if (!this.form.employee_id) { this.formError.set('Selecciona empleado.'); return; }
    this.saving.set(true);
    this.hr.createVacationRequest(this.form).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Creada', message: 'Solicitud registrada' });
        this.saving.set(false);
        this.formOpen.set(false);
        this.load();
        this.loadBalances();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'No se pudo crear.');
      },
    });
  }

  approve(r: HrVacationRequest): void {
    const notes = prompt('Notas de aprobación (opcional):') || undefined;
    this.hr.approveVacation(r.id, notes).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Aprobada', message: r.request_number }); this.load(); this.loadBalances(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo aprobar.' }),
    });
  }

  reject(r: HrVacationRequest): void {
    const reason = prompt('Motivo del rechazo:');
    if (!reason) return;
    this.hr.rejectVacation(r.id, reason).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Rechazada', message: r.request_number }); this.load(); this.loadBalances(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo rechazar.' }),
    });
  }

  cancel(r: HrVacationRequest): void {
    if (!confirm(`¿Cancelar solicitud ${r.request_number}?`)) return;
    this.hr.cancelVacation(r.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Cancelada', message: r.request_number }); this.load(); this.loadBalances(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo cancelar.' }),
    });
  }

  employeeName(id: string): string {
    const e = this.employees().find((x) => x.id === id);
    if (!e) return id.slice(0, 8);
    return `${e.first_name} ${e.last_name || ''}`.trim();
  }

  available(b: HrVacationBalance): string {
    const v = (+b.days_accrued) - (+b.days_taken) - (+b.days_pending) - (+b.days_compensated);
    return v.toFixed(2);
  }

  typeLabel(t: string): string {
    const map: Record<string, string> = { paid: 'Disfrutadas', compensation: 'Compensadas', unpaid: 'Sin pago' };
    return map[t] || t;
  }
  statusLabel(s: HrVacationStatus): string {
    const map: Record<HrVacationStatus, string> = {
      pending: 'Pendiente', approved: 'Aprobada', rejected: 'Rechazada',
      cancelled: 'Cancelada', completed: 'Completada',
    };
    return map[s];
  }
  statusClass(s: HrVacationStatus): string {
    const map: Record<HrVacationStatus, string> = {
      pending: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      cancelled: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
    };
    return map[s];
  }
}
