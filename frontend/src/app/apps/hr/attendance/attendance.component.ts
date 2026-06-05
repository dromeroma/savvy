import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrAttendanceCreate,
  HrAttendanceListItem,
  HrAttendanceStatus,
  HrEmployeeListItem,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-attendance',
  imports: [CommonModule, FormsModule, DatePipe, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Asistencia</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">Marcaciones diarias y horas extras. Único por (empleado, fecha).</p>
        </div>
        <button (click)="openCreate()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Registrar asistencia
        </button>
      </header>

      <!-- Filtros -->
      <section class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Empleado</span>
          <select [(ngModel)]="filterEmployee" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            @for (e of employees(); track e.id) {
              <option [value]="e.id">{{ e.first_name }} {{ e.last_name }} ({{ e.employee_code }})</option>
            }
          </select>
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Desde</span>
          <input type="date" [(ngModel)]="filterFrom" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Hasta</span>
          <input type="date" [(ngModel)]="filterTo" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Estado</span>
          <select [(ngModel)]="filterStatus" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            @for (s of statuses; track s.value) {
              <option [value]="s.value">{{ s.label }}</option>
            }
          </select>
        </label>
        <button (click)="load()" type="button"
          class="rounded-md border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-700 dark:text-slate-300">Refrescar</button>
      </section>

      <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-2 font-medium">Fecha</th>
              <th class="text-left px-4 py-2 font-medium">Empleado</th>
              <th class="text-left px-4 py-2 font-medium">Entrada</th>
              <th class="text-left px-4 py-2 font-medium">Salida</th>
              <th class="text-right px-4 py-2 font-medium">Horas</th>
              <th class="text-right px-4 py-2 font-medium">H. extra</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (records().length === 0) {
              <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin registros.</td></tr>
            } @else {
              @for (a of paginated(); track a.id) {
                <tr>
                  <td class="px-4 py-2 text-xs">{{ a.work_date }}</td>
                  <td class="px-4 py-2">
                    <div class="font-medium">{{ a.employee_name }}</div>
                    <div class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ a.employee_code }}</div>
                  </td>
                  <td class="px-4 py-2 text-xs">{{ a.check_in_at ? (a.check_in_at | date:'short') : '—' }}</td>
                  <td class="px-4 py-2 text-xs">{{ a.check_out_at ? (a.check_out_at | date:'short') : '—' }}</td>
                  <td class="px-4 py-2 text-right font-mono">{{ a.worked_hours || '—' }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs">{{ (+a.overtime_total) || 0 }}</td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(a.status)">{{ statusLabel(a.status) }}</span>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="records().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Registrar asistencia</h3>
            @if (formError()) { <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p> }
            <form (ngSubmit)="save()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Empleado *</span>
                <select [(ngModel)]="form.employee_id" name="eid" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="">— Selecciona —</option>
                  @for (e of employees(); track e.id) {
                    <option [value]="e.id">{{ e.first_name }} {{ e.last_name }} ({{ e.employee_code }})</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fecha *</span>
                <input type="date" [(ngModel)]="form.work_date" name="wd" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Estado</span>
                <select [(ngModel)]="form.status" name="ast"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  @for (s of statuses; track s.value) {
                    <option [value]="s.value">{{ s.label }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Entrada</span>
                <input type="datetime-local" [(ngModel)]="form.check_in_at" name="ci"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Salida</span>
                <input type="datetime-local" [(ngModel)]="form.check_out_at" name="co"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Hrs extra diurnas</span>
                <input type="number" step="0.25" min="0" max="24" [(ngModel)]="form.overtime_day_hours" name="otd"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Hrs extra nocturnas</span>
                <input type="number" step="0.25" min="0" max="24" [(ngModel)]="form.overtime_night_hours" name="otn"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Notas</span>
                <textarea [(ngModel)]="form.notes" name="not" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
              <div class="sm:col-span-2 flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeForm()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="saving()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ saving() ? 'Guardando...' : 'Guardar' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrAttendanceComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  readonly statuses: { value: HrAttendanceStatus; label: string }[] = [
    { value: 'present', label: 'Presente' },
    { value: 'absent', label: 'Ausente' },
    { value: 'late', label: 'Tarde' },
    { value: 'early_leave', label: 'Salida temprana' },
    { value: 'justified', label: 'Justificado' },
    { value: 'vacation', label: 'Vacaciones' },
    { value: 'sick_leave', label: 'Incapacidad' },
    { value: 'permit', label: 'Permiso' },
    { value: 'holiday', label: 'Festivo' },
  ];

  loading = signal(true);
  records = signal<HrAttendanceListItem[]>([]);
  employees = signal<HrEmployeeListItem[]>([]);

  filterEmployee = '';
  filterFrom = '';
  filterTo = '';
  filterStatus = '';

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.records().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: HrAttendanceCreate = this.emptyForm();

  constructor() {
    effect(() => { this.records(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    this.load();
    this.hr.listEmployees({ status: 'active' }).subscribe({ next: (r) => this.employees.set(r) });
  }

  load(): void {
    this.loading.set(true);
    const params: { employee_id?: string; date_from?: string; date_to?: string; status?: string; limit?: number } = { limit: 500 };
    if (this.filterEmployee) params.employee_id = this.filterEmployee;
    if (this.filterFrom) params.date_from = this.filterFrom;
    if (this.filterTo) params.date_to = this.filterTo;
    if (this.filterStatus) params.status = this.filterStatus;
    this.hr.listAttendance(params).subscribe({
      next: (r) => { this.records.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }); },
    });
  }

  emptyForm(): HrAttendanceCreate {
    return {
      employee_id: '', work_date: new Date().toISOString().slice(0, 10),
      check_in_at: null, check_out_at: null,
      overtime_day_hours: '0', overtime_night_hours: '0', overtime_holiday_hours: '0',
      status: 'present', notes: null,
    };
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }
  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    if (!this.form.employee_id) {
      this.formError.set('Selecciona un empleado.');
      return;
    }
    this.saving.set(true);
    const payload = { ...this.form };
    if (payload.check_in_at) payload.check_in_at = new Date(payload.check_in_at).toISOString();
    if (payload.check_out_at) payload.check_out_at = new Date(payload.check_out_at).toISOString();
    this.hr.upsertAttendance(payload).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Guardado', message: payload.work_date });
        this.saving.set(false);
        this.formOpen.set(false);
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'No se pudo guardar.');
      },
    });
  }

  statusLabel(s: HrAttendanceStatus): string {
    return this.statuses.find((x) => x.value === s)?.label || s;
  }
  statusClass(s: HrAttendanceStatus): string {
    const map: Record<HrAttendanceStatus, string> = {
      present: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      absent: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      late: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      early_leave: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      justified: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      vacation: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
      sick_leave: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
      permit: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      holiday: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    };
    return map[s];
  }
}
