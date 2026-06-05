import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrEmployeeListItem,
  HrLeave,
  HrLeaveCreate,
  HrLeaveType,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-leaves',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Incapacidades y permisos</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">Incapacidades médicas, licencias y permisos no remunerados.</p>
        </div>
        <button (click)="openCreate()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Registrar
        </button>
      </header>

      <section class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Tipo</span>
          <select [(ngModel)]="filterType" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            @for (t of leaveTypes; track t.value) {
              <option [value]="t.value">{{ t.label }}</option>
            }
          </select>
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Estado</span>
          <select [(ngModel)]="filterStatus" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            <option value="active">Activa</option>
            <option value="completed">Completada</option>
            <option value="cancelled">Cancelada</option>
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
              <th class="text-left px-4 py-2 font-medium">Pago</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (leaves().length === 0) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin registros.</td></tr>
            } @else {
              @for (l of paginated(); track l.id) {
                <tr>
                  <td class="px-4 py-2 font-mono text-xs">{{ l.leave_number }}</td>
                  <td class="px-4 py-2 text-xs">{{ employeeName(l.employee_id) }}</td>
                  <td class="px-4 py-2 text-xs">{{ typeLabel(l.leave_type) }}</td>
                  <td class="px-4 py-2 text-xs">{{ l.start_date }}</td>
                  <td class="px-4 py-2 text-xs">{{ l.end_date }}</td>
                  <td class="px-4 py-2 text-right font-mono">{{ l.days_count }}</td>
                  <td class="px-4 py-2 text-xs">
                    @if (l.is_paid) {
                      <span class="text-emerald-700 dark:text-emerald-300">Pagado {{ l.paid_percentage ? '· ' + l.paid_percentage + '%' : '' }}</span>
                    } @else {
                      <span class="text-slate-500 dark:text-slate-400">No pagado</span>
                    }
                  </td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(l.status)">{{ statusLabel(l.status) }}</span>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="leaves().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Nueva incapacidad / licencia</h3>
            @if (formError()) { <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p> }
            <form (ngSubmit)="save()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block sm:col-span-2">
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
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo *</span>
                <select [(ngModel)]="form.leave_type" name="lt" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  @for (t of leaveTypes; track t.value) {
                    <option [value]="t.value">{{ t.label }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Subtipo</span>
                <input [(ngModel)]="form.subtype" name="sub" maxlength="40" placeholder="ej: EPS, ARL, COVID..."
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
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
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Días *</span>
                <input type="number" step="0.5" min="0" [(ngModel)]="form.days_count" name="dc" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" [(ngModel)]="form.is_paid" name="ip" />
                <span class="text-slate-700 dark:text-slate-300">Es pagada</span>
              </label>
              @if (form.is_paid) {
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">% pago</span>
                  <input type="number" step="0.01" min="0" max="100" [(ngModel)]="form.paid_percentage" name="pp"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Monto</span>
                  <input type="number" step="1000" min="0" [(ngModel)]="form.amount_paid" name="ap"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
              }
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">N° soporte</span>
                <input [(ngModel)]="form.supporting_doc_number" name="dn" maxlength="80"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Entidad (EPS/ARL/...)</span>
                <input [(ngModel)]="form.supporting_doc_issuer" name="iss" maxlength="150"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">URL del soporte</span>
                <input [(ngModel)]="form.supporting_doc_url" name="url" placeholder="https://..."
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">CIE-10 (diagnóstico)</span>
                <input [(ngModel)]="form.diagnosis_code" name="cie" maxlength="20"
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
export class HrLeavesComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  readonly leaveTypes: { value: HrLeaveType; label: string }[] = [
    { value: 'medical', label: 'Incapacidad médica' },
    { value: 'maternity', label: 'Licencia maternidad' },
    { value: 'paternity', label: 'Licencia paternidad' },
    { value: 'bereavement', label: 'Luto' },
    { value: 'unpaid', label: 'No remunerada' },
    { value: 'paid_other', label: 'Pagada (otros)' },
    { value: 'study', label: 'Estudio' },
    { value: 'remunerated_permit', label: 'Permiso remunerado' },
  ];

  loading = signal(true);
  leaves = signal<HrLeave[]>([]);
  employees = signal<HrEmployeeListItem[]>([]);

  filterType = '';
  filterStatus = '';

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.leaves().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: HrLeaveCreate = this.emptyForm();

  constructor() {
    effect(() => { this.leaves(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    this.hr.listEmployees().subscribe({ next: (r) => this.employees.set(r) });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const params: { leave_type?: string; status?: string } = {};
    if (this.filterType) params.leave_type = this.filterType;
    if (this.filterStatus) params.status = this.filterStatus;
    this.hr.listLeaves(params).subscribe({
      next: (r) => { this.leaves.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  emptyForm(): HrLeaveCreate {
    return {
      employee_id: '', leave_type: 'medical', subtype: null,
      start_date: new Date().toISOString().slice(0, 10),
      end_date: new Date().toISOString().slice(0, 10),
      days_count: '1', is_paid: true, paid_percentage: '66.67',
    };
  }

  updateDays(): void {
    if (!this.form.start_date || !this.form.end_date) return;
    const s = new Date(this.form.start_date);
    const e = new Date(this.form.end_date);
    const diff = Math.max(0, (e.getTime() - s.getTime()) / 86400000 + 1);
    this.form.days_count = String(diff);
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }
  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    if (!this.form.employee_id) { this.formError.set('Selecciona empleado.'); return; }
    this.saving.set(true);
    this.hr.createLeave(this.form).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Registrado', message: 'Incapacidad guardada' });
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

  employeeName(id: string): string {
    const e = this.employees().find((x) => x.id === id);
    if (!e) return id.slice(0, 8);
    return `${e.first_name} ${e.last_name || ''}`.trim();
  }

  typeLabel(t: HrLeaveType): string {
    return this.leaveTypes.find((x) => x.value === t)?.label || t;
  }
  statusLabel(s: string): string {
    const map: Record<string, string> = { active: 'Activa', completed: 'Completada', cancelled: 'Cancelada' };
    return map[s] || s;
  }
  statusClass(s: string): string {
    const map: Record<string, string> = {
      active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      cancelled: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    };
    return map[s] || '';
  }
}
