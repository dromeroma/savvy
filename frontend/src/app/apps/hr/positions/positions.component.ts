import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import { HrDepartment, HrPosition, HrPositionCreate } from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-positions',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Cargos</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">Catálogo de cargos con escala salarial y vínculo opcional a departamento.</p>
        </div>
        <button (click)="openCreate()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Nuevo cargo
        </button>
      </header>

      <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-2 font-medium">Código</th>
              <th class="text-left px-4 py-2 font-medium">Nombre</th>
              <th class="text-left px-4 py-2 font-medium">Departamento</th>
              <th class="text-left px-4 py-2 font-medium">Nivel</th>
              <th class="text-right px-4 py-2 font-medium">Salario ref.</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
              <th class="text-right px-4 py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (positions().length === 0) {
              <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin cargos.</td></tr>
            } @else {
              @for (p of paginated(); track p.id) {
                <tr>
                  <td class="px-4 py-2 font-mono text-xs">{{ p.code }}</td>
                  <td class="px-4 py-2 font-medium">{{ p.name }}</td>
                  <td class="px-4 py-2 text-xs text-slate-600 dark:text-slate-400">{{ deptName(p.department_id) || '—' }}</td>
                  <td class="px-4 py-2 text-xs">{{ p.level ?? '—' }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs">
                    {{ p.reference_salary ? p.currency + ' ' + (+p.reference_salary | number:'1.0-0') : '—' }}
                  </td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md"
                      [class]="p.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
                      {{ p.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                  </td>
                  <td class="px-4 py-2 text-right space-x-2 whitespace-nowrap">
                    <button (click)="openEdit(p)" type="button" class="text-xs text-brand-600 hover:underline">Editar</button>
                    <button (click)="remove(p)" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="positions().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
              {{ editingId() ? 'Editar cargo' : 'Nuevo cargo' }}
            </h3>
            @if (formError()) {
              <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p>
            }
            <form (ngSubmit)="save()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Código *</span>
                <input [(ngModel)]="form.code" name="code" required maxlength="40" [disabled]="!!editingId()"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm disabled:opacity-60" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombre *</span>
                <input [(ngModel)]="form.name" name="name" required maxlength="150"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Departamento</span>
                <select [(ngModel)]="form.department_id" name="department_id"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option [ngValue]="null">— Sin asignar —</option>
                  @for (d of departments(); track d.id) {
                    <option [ngValue]="d.id">{{ d.code }} — {{ d.name }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nivel (1-20)</span>
                <input type="number" [(ngModel)]="form.level" name="level" min="1" max="20"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Salario mínimo</span>
                <input type="number" [(ngModel)]="form.min_salary" name="min_salary" min="0" step="1000"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Salario máximo</span>
                <input type="number" [(ngModel)]="form.max_salary" name="max_salary" min="0" step="1000"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Salario de referencia</span>
                <input type="number" [(ngModel)]="form.reference_salary" name="reference_salary" min="0" step="1000"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Moneda</span>
                <input [(ngModel)]="form.currency" name="currency" maxlength="3" placeholder="COP"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm uppercase" />
              </label>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Descripción</span>
                <textarea [(ngModel)]="form.description" name="description" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
              <label class="flex items-center gap-2 text-sm sm:col-span-2">
                <input type="checkbox" [(ngModel)]="form.is_active" name="is_active" />
                <span class="text-slate-700 dark:text-slate-300">Activo</span>
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
export class HrPositionsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  positions = signal<HrPosition[]>([]);
  departments = signal<HrDepartment[]>([]);

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.positions().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  editingId = signal<string | null>(null);
  saving = signal(false);
  formError = signal('');
  form: HrPositionCreate = this.emptyForm();

  constructor() {
    effect(() => { this.positions(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    this.load();
    this.hr.listDepartments(true).subscribe({ next: (r) => this.departments.set(r) });
  }

  load(): void {
    this.loading.set(true);
    this.hr.listPositions().subscribe({
      next: (r) => { this.positions.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }); },
    });
  }

  emptyForm(): HrPositionCreate {
    return {
      code: '', name: '', description: null, department_id: null,
      level: null, min_salary: null, max_salary: null, reference_salary: null,
      currency: 'COP', is_active: true,
    };
  }

  deptName(id: string | null): string | null {
    if (!id) return null;
    return this.departments().find((d) => d.id === id)?.name ?? null;
  }

  openCreate(): void {
    this.editingId.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(p: HrPosition): void {
    this.editingId.set(p.id);
    this.form = {
      code: p.code, name: p.name, description: p.description,
      department_id: p.department_id, level: p.level,
      min_salary: p.min_salary, max_salary: p.max_salary, reference_salary: p.reference_salary,
      currency: p.currency, headcount_budget: p.headcount_budget,
      is_active: p.is_active,
    };
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    this.saving.set(true);
    const id = this.editingId();
    const obs = id
      ? this.hr.updatePosition(id, this.form)
      : this.hr.createPosition(this.form);
    obs.subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: this.form.name });
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

  remove(p: HrPosition): void {
    if (!confirm(`¿Eliminar cargo ${p.code} — ${p.name}?`)) return;
    this.hr.deletePosition(p.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: p.name }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }
}
