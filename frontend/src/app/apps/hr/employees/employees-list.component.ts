import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrDepartment,
  HrEmployeeCreate,
  HrEmployeeListItem,
  HrEmployeeStatus,
  HrEmploymentType,
  HrPosition,
  HrWorkLocation,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';
import { ScanPrefillComponent } from '../../../shared/components/ai/scan-prefill.component';

@Component({
  selector: 'app-hr-employees-list',
  imports: [CommonModule, FormsModule, RouterLink, PaginationComponent, ScanPrefillComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Empleados</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">Talento humano de tu organización.</p>
        </div>
        <button (click)="openCreate()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Nuevo empleado
        </button>
      </header>

      <!-- Filtros -->
      <section class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Buscar</span>
          <input [(ngModel)]="search" (keyup.enter)="load()" placeholder="Nombre, código, doc, email..."
            class="w-64 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Estado</span>
          <select [(ngModel)]="filterStatus" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            <option value="active">Activo</option>
            <option value="on_leave">En licencia</option>
            <option value="suspended">Suspendido</option>
            <option value="terminated">Terminado</option>
          </select>
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Departamento</span>
          <select [(ngModel)]="filterDept" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            @for (d of departments(); track d.id) {
              <option [value]="d.id">{{ d.name }}</option>
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
              <th class="text-left px-4 py-2 font-medium">Código</th>
              <th class="text-left px-4 py-2 font-medium">Nombre</th>
              <th class="text-left px-4 py-2 font-medium">Documento</th>
              <th class="text-left px-4 py-2 font-medium">Departamento</th>
              <th class="text-left px-4 py-2 font-medium">Cargo</th>
              <th class="text-left px-4 py-2 font-medium">Contacto</th>
              <th class="text-left px-4 py-2 font-medium">Tipo</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (employees().length === 0) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin empleados.</td></tr>
            } @else {
              @for (e of paginated(); track e.id) {
                <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                  <td class="px-4 py-2 font-mono text-xs">{{ e.employee_code }}</td>
                  <td class="px-4 py-2">
                    <a [routerLink]="['/hr/employees', e.id]" class="font-medium text-brand-700 dark:text-brand-300 hover:underline">
                      {{ e.first_name }} {{ e.last_name }}
                    </a>
                  </td>
                  <td class="px-4 py-2 font-mono text-xs text-slate-600 dark:text-slate-400">{{ e.document_number || '—' }}</td>
                  <td class="px-4 py-2 text-xs">{{ e.department_name || '—' }}</td>
                  <td class="px-4 py-2 text-xs">{{ e.position_name || '—' }}</td>
                  <td class="px-4 py-2 text-xs text-slate-600 dark:text-slate-400">
                    @if (e.email) { <div>{{ e.email }}</div> }
                    @if (e.mobile) { <div>{{ e.mobile }}</div> }
                  </td>
                  <td class="px-4 py-2 text-xs">{{ employmentLabel(e.employment_type) }}</td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(e.status)">
                      {{ statusLabel(e.status) }}
                    </span>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="employees().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-3xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Nuevo empleado</h3>
              <app-scan-prefill prompt-key="extraction.id_card" target-app="hr"
                document-type="id_card" label="Escanear documento"
                (prefill)="applyCedula($event)" />
            </div>
            @if (formError()) {
              <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p>
            }
            <form (ngSubmit)="save()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Código *</span>
                <input [(ngModel)]="form.employee_code" name="employee_code" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo doc.</span>
                <input [(ngModel)]="form.document_type" name="document_type" maxlength="10" placeholder="CC, CE, TI, NIT"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombres *</span>
                <input [(ngModel)]="form.first_name" name="first_name" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Apellidos</span>
                <input [(ngModel)]="form.last_name" name="last_name"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Número documento</span>
                <input [(ngModel)]="form.document_number" name="document_number"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fecha nacimiento</span>
                <input type="date" [(ngModel)]="form.birth_date" name="birth_date"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Email</span>
                <input type="email" [(ngModel)]="form.email" name="email"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Celular</span>
                <input [(ngModel)]="form.mobile" name="mobile"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Dirección</span>
                <input [(ngModel)]="form.address" name="address"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>

              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Departamento</span>
                <select [(ngModel)]="form.department_id" name="department_id"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option [ngValue]="null">— Sin asignar —</option>
                  @for (d of departments(); track d.id) {
                    <option [ngValue]="d.id">{{ d.name }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Cargo</span>
                <select [(ngModel)]="form.position_id" name="position_id"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option [ngValue]="null">— Sin asignar —</option>
                  @for (p of positions(); track p.id) {
                    <option [ngValue]="p.id">{{ p.name }}</option>
                  }
                </select>
              </label>

              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fecha de ingreso *</span>
                <input type="date" [(ngModel)]="form.hire_date" name="hire_date" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo de empleo</span>
                <select [(ngModel)]="form.employment_type" name="employment_type"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="full_time">Tiempo completo</option>
                  <option value="part_time">Medio tiempo</option>
                  <option value="intern">Practicante</option>
                  <option value="contractor">Contratista</option>
                  <option value="temporary">Temporal</option>
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Modalidad</span>
                <select [(ngModel)]="form.work_location" name="work_location"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="onsite">Presencial</option>
                  <option value="remote">Remoto</option>
                  <option value="hybrid">Híbrido</option>
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">País (ISO)</span>
                <input [(ngModel)]="form.country_code" name="country_code" maxlength="3" placeholder="CO"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm uppercase" />
              </label>

              <div class="sm:col-span-2 border-t border-slate-200 dark:border-slate-700 pt-3 mt-2">
                <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">Contacto de emergencia</h4>
              </div>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombre</span>
                <input [(ngModel)]="form.emergency_contact_name" name="ec_name"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Teléfono</span>
                <input [(ngModel)]="form.emergency_contact_phone" name="ec_phone"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>

              <div class="sm:col-span-2 flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeForm()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="saving()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ saving() ? 'Guardando...' : 'Crear empleado' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrEmployeesListComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  employees = signal<HrEmployeeListItem[]>([]);
  departments = signal<HrDepartment[]>([]);
  positions = signal<HrPosition[]>([]);

  search = '';
  filterStatus = '';
  filterDept = '';

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.employees().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: HrEmployeeCreate = this.emptyForm();

  constructor() {
    effect(() => { this.employees(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    this.load();
    this.hr.listDepartments(true).subscribe({ next: (r) => this.departments.set(r) });
    this.hr.listPositions({ active_only: true }).subscribe({ next: (r) => this.positions.set(r) });
  }

  load(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.search) params['search'] = this.search;
    if (this.filterStatus) params['status'] = this.filterStatus;
    if (this.filterDept) params['department_id'] = this.filterDept;
    this.hr.listEmployees(params).subscribe({
      next: (r) => { this.employees.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }); },
    });
  }

  emptyForm(): HrEmployeeCreate {
    return {
      employee_code: '', first_name: '', last_name: null,
      document_type: 'CC', document_number: null, birth_date: null,
      email: null, mobile: null, address: null, city: null, country_code: 'CO',
      department_id: null, position_id: null,
      hire_date: new Date().toISOString().slice(0, 10),
      employment_type: 'full_time', work_location: 'onsite',
      emergency_contact_name: null, emergency_contact_phone: null,
    };
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  /** Prellena los datos personales del empleado desde la cédula (SavvyScan). */
  applyCedula(data: Record<string, unknown>): void {
    const v = (k: string) => (data[k] == null ? '' : String(data[k]));
    if (v('first_name')) this.form.first_name = v('first_name');
    if (v('last_name')) this.form.last_name = v('last_name');
    if (v('document_number')) this.form.document_number = v('document_number');
    if (v('document_type')) this.form.document_type = v('document_type');
    if (v('birth_date')) this.form.birth_date = v('birth_date');
    if (v('gender')) this.form.gender = v('gender');
    this.notify.show({ type: 'success', title: 'Cédula leída', message: 'Revisa y completa los datos.' });
  }

  save(): void {
    this.saving.set(true);
    this.hr.createEmployee(this.form).subscribe({
      next: (r) => {
        this.notify.show({ type: 'success', title: 'Creado', message: `${r.first_name} ${r.last_name || ''}`.trim() });
        this.saving.set(false);
        this.formOpen.set(false);
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'No se pudo crear.');
      },
    });
  }

  statusLabel(s: HrEmployeeStatus): string {
    const map = { active: 'Activo', on_leave: 'Licencia', suspended: 'Suspendido', terminated: 'Terminado' };
    return map[s];
  }
  statusClass(s: HrEmployeeStatus): string {
    const map = {
      active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      on_leave: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      suspended: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      terminated: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    };
    return map[s];
  }
  employmentLabel(t: HrEmploymentType): string {
    const map = {
      full_time: 'Tiempo completo', part_time: 'Medio tiempo',
      intern: 'Practicante', contractor: 'Contratista', temporary: 'Temporal',
    };
    return map[t];
  }
}
