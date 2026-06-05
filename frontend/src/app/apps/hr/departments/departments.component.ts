import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import { HrDepartment, HrDepartmentCreate } from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-departments',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Departamentos</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">Unidades organizacionales · jerarquía vía departamento padre.</p>
        </div>
        <button (click)="openCreate()" type="button"
          class="inline-flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Nuevo departamento
        </button>
      </header>

      <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-2 font-medium">Código</th>
              <th class="text-left px-4 py-2 font-medium">Nombre</th>
              <th class="text-left px-4 py-2 font-medium">Padre</th>
              <th class="text-left px-4 py-2 font-medium">Centro de costo</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
              <th class="text-right px-4 py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="6" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (departments().length === 0) {
              <tr><td colspan="6" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin departamentos.</td></tr>
            } @else {
              @for (d of paginated(); track d.id) {
                <tr>
                  <td class="px-4 py-2 font-mono text-xs">{{ d.code }}</td>
                  <td class="px-4 py-2 font-medium">{{ d.name }}</td>
                  <td class="px-4 py-2 text-xs text-slate-600 dark:text-slate-400">{{ parentName(d.parent_id) || '—' }}</td>
                  <td class="px-4 py-2 text-xs text-slate-600 dark:text-slate-400">{{ d.cost_center || '—' }}</td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md"
                      [class]="d.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
                      {{ d.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                  </td>
                  <td class="px-4 py-2 text-right space-x-2 whitespace-nowrap">
                    <button (click)="openEdit(d)" type="button" class="text-xs text-brand-600 hover:underline">Editar</button>
                    <button (click)="remove(d)" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="departments().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
              {{ editingId() ? 'Editar departamento' : 'Nuevo departamento' }}
            </h3>
            @if (formError()) {
              <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p>
            }
            <form (ngSubmit)="save()" class="space-y-3">
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
                <span class="text-xs text-slate-600 dark:text-slate-400">Departamento padre</span>
                <select [(ngModel)]="form.parent_id" name="parent_id"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option [ngValue]="null">— Ninguno (raíz) —</option>
                  @for (d of departments(); track d.id) {
                    @if (d.id !== editingId()) {
                      <option [ngValue]="d.id">{{ d.code }} — {{ d.name }}</option>
                    }
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Centro de costo</span>
                <input [(ngModel)]="form.cost_center" name="cost_center" maxlength="40"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Descripción</span>
                <textarea [(ngModel)]="form.description" name="description" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
              <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" [(ngModel)]="form.is_active" name="is_active" />
                <span class="text-slate-700 dark:text-slate-300">Activo</span>
              </label>
              <div class="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
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
export class HrDepartmentsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  departments = signal<HrDepartment[]>([]);

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.departments().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  editingId = signal<string | null>(null);
  saving = signal(false);
  formError = signal('');
  form: HrDepartmentCreate = this.emptyForm();

  constructor() {
    effect(() => { this.departments(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.hr.listDepartments().subscribe({
      next: (r) => { this.departments.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }); },
    });
  }

  emptyForm(): HrDepartmentCreate {
    return { code: '', name: '', description: null, cost_center: null, parent_id: null, is_active: true };
  }

  parentName(parentId: string | null): string | null {
    if (!parentId) return null;
    return this.departments().find((d) => d.id === parentId)?.name ?? null;
  }

  openCreate(): void {
    this.editingId.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(d: HrDepartment): void {
    this.editingId.set(d.id);
    this.form = {
      code: d.code, name: d.name, description: d.description,
      cost_center: d.cost_center, parent_id: d.parent_id, is_active: d.is_active,
    };
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    this.saving.set(true);
    const id = this.editingId();
    const obs = id
      ? this.hr.updateDepartment(id, this.form)
      : this.hr.createDepartment(this.form);
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

  remove(d: HrDepartment): void {
    if (!confirm(`¿Eliminar departamento ${d.code} — ${d.name}?`)) return;
    this.hr.deleteDepartment(d.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: d.name }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }
}
