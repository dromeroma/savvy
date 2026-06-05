import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrPayrollCalcMethod,
  HrPayrollConcept,
  HrPayrollConceptCreate,
  HrPayrollConceptType,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-payroll-concepts',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Conceptos de nómina</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">
            Catálogo configurable. Carga el template del país de tu organización o crea conceptos manualmente.
          </p>
        </div>
        <div class="flex gap-2">
          <button (click)="seedColombia()" type="button" [disabled]="seeding()"
            class="rounded-md border border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 px-3 py-2 text-sm disabled:opacity-50">
            {{ seeding() ? '...' : 'Cargar template Colombia' }}
          </button>
          <button (click)="openCreate()" type="button"
            class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            + Concepto
          </button>
        </div>
      </header>

      <section class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Tipo</span>
          <select [(ngModel)]="filterType" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            @for (t of conceptTypes; track t.value) {
              <option [value]="t.value">{{ t.label }}</option>
            }
          </select>
        </label>
      </section>

      <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-2 font-medium">Código</th>
              <th class="text-left px-4 py-2 font-medium">Nombre</th>
              <th class="text-left px-4 py-2 font-medium">Tipo</th>
              <th class="text-left px-4 py-2 font-medium">Método</th>
              <th class="text-right px-4 py-2 font-medium">Valor</th>
              <th class="text-left px-4 py-2 font-medium">Base</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
              <th class="text-right px-4 py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (concepts().length === 0) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">
                Sin conceptos. Carga el template Colombia para empezar.
              </td></tr>
            } @else {
              @for (c of paginated(); track c.id) {
                <tr>
                  <td class="px-4 py-2 font-mono text-xs">{{ c.code }}</td>
                  <td class="px-4 py-2">{{ c.name }}</td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md" [class]="typeClass(c.concept_type)">{{ typeLabel(c.concept_type) }}</span>
                  </td>
                  <td class="px-4 py-2 text-xs">{{ methodLabel(c.calculation_method) }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs">
                    @if (c.calculation_method === 'percentage') {
                      {{ c.percentage_value }}%
                    } @else if (c.calculation_method === 'fixed') {
                      $ {{ c.fixed_value }}
                    } @else if (c.calculation_method === 'formula') {
                      <span class="text-slate-500 dark:text-slate-400 italic">fórmula</span>
                    } @else {
                      —
                    }
                  </td>
                  <td class="px-4 py-2 text-xs font-mono text-slate-500 dark:text-slate-400">{{ c.base_concept_code || '—' }}</td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md"
                      [class]="c.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
                      {{ c.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                  </td>
                  <td class="px-4 py-2 text-right space-x-2 whitespace-nowrap">
                    <button (click)="openEdit(c)" type="button" class="text-xs text-brand-600 hover:underline">Editar</button>
                    <button (click)="remove(c)" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="concepts().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
              {{ editingId() ? 'Editar concepto' : 'Nuevo concepto' }}
            </h3>
            @if (formError()) { <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p> }
            <form (ngSubmit)="save()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Código *</span>
                <input [(ngModel)]="form.code" name="code" required maxlength="40" [disabled]="!!editingId()"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm uppercase disabled:opacity-60" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombre *</span>
                <input [(ngModel)]="form.name" name="name" required maxlength="150"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo *</span>
                <select [(ngModel)]="form.concept_type" name="ct" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  @for (t of conceptTypes; track t.value) {
                    <option [value]="t.value">{{ t.label }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Categoría</span>
                <input [(ngModel)]="form.category" name="cat" maxlength="40" placeholder="salary, health, ..."
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Método de cálculo</span>
                <select [(ngModel)]="form.calculation_method" name="cm"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="fixed">Fijo</option>
                  <option value="percentage">Porcentaje sobre base</option>
                  <option value="formula">Fórmula</option>
                  <option value="quantity_rate">Cantidad × tasa</option>
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Orden</span>
                <input type="number" [(ngModel)]="form.sort_order" name="so" min="0" max="999"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              @if (form.calculation_method === 'fixed') {
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Valor fijo</span>
                  <input type="number" step="0.01" [(ngModel)]="form.fixed_value" name="fv"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
              }
              @if (form.calculation_method === 'percentage') {
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">% sobre base</span>
                  <input type="number" step="0.01" [(ngModel)]="form.percentage_value" name="pv"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Concepto base</span>
                  <input [(ngModel)]="form.base_concept_code" name="bcc" placeholder="SALARIO, base_salary, ..."
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm uppercase" />
                </label>
              }
              @if (form.calculation_method === 'formula') {
                <label class="block sm:col-span-2">
                  <span class="text-xs text-slate-600 dark:text-slate-400">
                    Fórmula (vars: base_salary, daily_base, worked_days, hourly_rate, overtime_day, overtime_night, transport_allowance, ...)
                  </span>
                  <input [(ngModel)]="form.formula" name="for" placeholder="base_salary * 0.04"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
                </label>
              }
              <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" [(ngModel)]="form.is_active" name="ia" />
                <span class="text-slate-700 dark:text-slate-300">Activo</span>
              </label>
              <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" [(ngModel)]="form.is_taxable" name="it" />
                <span class="text-slate-700 dark:text-slate-300">Gravado</span>
              </label>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Descripción</span>
                <textarea [(ngModel)]="form.description" name="desc" rows="2"
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
export class HrPayrollConceptsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  readonly conceptTypes: { value: HrPayrollConceptType; label: string }[] = [
    { value: 'earning', label: 'Devengado' },
    { value: 'deduction', label: 'Deducción' },
    { value: 'benefit', label: 'Prestación' },
    { value: 'employer_contribution', label: 'Aporte patronal' },
    { value: 'informative', label: 'Informativo' },
  ];

  loading = signal(true);
  concepts = signal<HrPayrollConcept[]>([]);
  seeding = signal(false);

  filterType = '';

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.concepts().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  editingId = signal<string | null>(null);
  saving = signal(false);
  formError = signal('');
  form: HrPayrollConceptCreate = this.emptyForm();

  constructor() {
    effect(() => { this.concepts(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    const params: { concept_type?: string } = {};
    if (this.filterType) params.concept_type = this.filterType;
    this.hr.listPayrollConcepts(params).subscribe({
      next: (r) => { this.concepts.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  emptyForm(): HrPayrollConceptCreate {
    return {
      code: '', name: '', description: null,
      concept_type: 'earning', category: 'salary',
      calculation_method: 'fixed', formula: null,
      percentage_value: null, fixed_value: null, base_concept_code: null,
      country_code: 'CO', is_taxable: true, is_active: true, sort_order: 100,
    };
  }

  seedColombia(): void {
    if (!confirm('¿Cargar template Colombia? Crea 19 conceptos (salud, pensión, retención, cesantías, prima, vacaciones, aportes patronales). No duplica los que ya existan.')) return;
    this.seeding.set(true);
    this.hr.seedPayrollCountryTemplate('CO').subscribe({
      next: (r) => {
        this.seeding.set(false);
        this.notify.show({ type: 'success', title: 'Template cargado', message: `${r.created} conceptos creados` });
        this.load();
      },
      error: () => { this.seeding.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }); },
    });
  }

  openCreate(): void {
    this.editingId.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(c: HrPayrollConcept): void {
    this.editingId.set(c.id);
    this.form = {
      code: c.code, name: c.name, description: c.description,
      concept_type: c.concept_type, category: c.category,
      calculation_method: c.calculation_method, formula: c.formula,
      percentage_value: c.percentage_value, fixed_value: c.fixed_value,
      base_concept_code: c.base_concept_code, country_code: c.country_code,
      is_taxable: c.is_taxable, is_active: c.is_active, sort_order: c.sort_order,
    };
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    this.saving.set(true);
    const id = this.editingId();
    const obs = id
      ? this.hr.updatePayrollConcept(id, this.form)
      : this.hr.createPayrollConcept(this.form);
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

  remove(c: HrPayrollConcept): void {
    if (!confirm(`¿Eliminar concepto ${c.code}?`)) return;
    this.hr.deletePayrollConcept(c.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: c.code }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }

  typeLabel(t: HrPayrollConceptType): string {
    return this.conceptTypes.find((x) => x.value === t)?.label || t;
  }
  typeClass(t: HrPayrollConceptType): string {
    const map: Record<HrPayrollConceptType, string> = {
      earning: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      deduction: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      benefit: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      employer_contribution: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
      informative: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    };
    return map[t];
  }
  methodLabel(m: HrPayrollCalcMethod): string {
    const map: Record<HrPayrollCalcMethod, string> = {
      fixed: 'Fijo', percentage: 'Porcentaje', formula: 'Fórmula', quantity_rate: 'Cant × tasa',
    };
    return map[m];
  }
}
