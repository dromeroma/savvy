import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import { HrShift, HrShiftCreate, HrShiftType } from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-shifts',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Turnos</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">Configura los turnos de tu organización (mañana, tarde, noche, rotativo, flexible).</p>
        </div>
        <button (click)="openCreate()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Nuevo turno
        </button>
      </header>

      <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-2 font-medium">Código</th>
              <th class="text-left px-4 py-2 font-medium">Nombre</th>
              <th class="text-left px-4 py-2 font-medium">Tipo</th>
              <th class="text-left px-4 py-2 font-medium">Horario</th>
              <th class="text-left px-4 py-2 font-medium">Días</th>
              <th class="text-right px-4 py-2 font-medium">Hrs/sem</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
              <th class="text-right px-4 py-2 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (shifts().length === 0) {
              <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin turnos.</td></tr>
            } @else {
              @for (s of paginated(); track s.id) {
                <tr>
                  <td class="px-4 py-2 font-mono text-xs">{{ s.code }}</td>
                  <td class="px-4 py-2 font-medium">{{ s.name }}</td>
                  <td class="px-4 py-2 text-xs">{{ typeLabel(s.shift_type) }}</td>
                  <td class="px-4 py-2 text-xs font-mono">{{ s.start_time || '—' }} → {{ s.end_time || '—' }}</td>
                  <td class="px-4 py-2 text-xs">{{ daysLabel(s.days_of_week) }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs">{{ s.weekly_hours || '—' }}</td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md"
                      [class]="s.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
                      {{ s.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                  </td>
                  <td class="px-4 py-2 text-right space-x-2 whitespace-nowrap">
                    <button (click)="openEdit(s)" type="button" class="text-xs text-brand-600 hover:underline">Editar</button>
                    <button (click)="remove(s)" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="shifts().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>

      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
              {{ editingId() ? 'Editar turno' : 'Nuevo turno' }}
            </h3>
            @if (formError()) { <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p> }
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
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo</span>
                <select [(ngModel)]="form.shift_type" name="st"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="morning">Mañana</option>
                  <option value="afternoon">Tarde</option>
                  <option value="night">Noche</option>
                  <option value="rotating">Rotativo</option>
                  <option value="flexible">Flexible</option>
                  <option value="administrative">Administrativo</option>
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Horas/semana</span>
                <input type="number" [(ngModel)]="form.weekly_hours" name="wh" min="0" max="168" step="0.5"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Hora inicio</span>
                <input type="time" [(ngModel)]="form.start_time" name="sti"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Hora fin</span>
                <input type="time" [(ngModel)]="form.end_time" name="etm"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Descanso (min)</span>
                <input type="number" [(ngModel)]="form.break_minutes" name="bm" min="0" max="480"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <div class="sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Días laborables</span>
                <div class="mt-1 flex flex-wrap gap-2">
                  @for (d of dayOptions; track d.value) {
                    <label class="inline-flex items-center gap-1 text-xs">
                      <input type="checkbox" [checked]="form.days_of_week?.includes(d.value)" (change)="toggleDay(d.value)" />
                      <span class="text-slate-700 dark:text-slate-300">{{ d.label }}</span>
                    </label>
                  }
                </div>
              </div>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Descripción</span>
                <textarea [(ngModel)]="form.description" name="desc" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
              <label class="flex items-center gap-2 text-sm sm:col-span-2">
                <input type="checkbox" [(ngModel)]="form.is_active" name="ia" />
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
export class HrShiftsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  readonly dayOptions = [
    { value: 1, label: 'Lun' }, { value: 2, label: 'Mar' }, { value: 3, label: 'Mié' },
    { value: 4, label: 'Jue' }, { value: 5, label: 'Vie' }, { value: 6, label: 'Sáb' }, { value: 0, label: 'Dom' },
  ];

  loading = signal(true);
  shifts = signal<HrShift[]>([]);
  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.shifts().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  editingId = signal<string | null>(null);
  saving = signal(false);
  formError = signal('');
  form: HrShiftCreate = this.emptyForm();

  constructor() {
    effect(() => { this.shifts(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.hr.listShifts().subscribe({
      next: (r) => { this.shifts.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }); },
    });
  }

  emptyForm(): HrShiftCreate {
    return {
      code: '', name: '', description: null, shift_type: 'morning',
      start_time: '08:00', end_time: '17:00', break_minutes: 60,
      days_of_week: [1, 2, 3, 4, 5], weekly_hours: '40', is_active: true,
    };
  }

  toggleDay(d: number): void {
    const arr = this.form.days_of_week || [];
    if (arr.includes(d)) {
      this.form.days_of_week = arr.filter((x) => x !== d);
    } else {
      this.form.days_of_week = [...arr, d].sort((a, b) => a - b);
    }
  }

  openCreate(): void {
    this.editingId.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(s: HrShift): void {
    this.editingId.set(s.id);
    this.form = {
      code: s.code, name: s.name, description: s.description, shift_type: s.shift_type,
      start_time: s.start_time, end_time: s.end_time, break_minutes: s.break_minutes,
      days_of_week: [...s.days_of_week], weekly_hours: s.weekly_hours, is_active: s.is_active,
    };
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    this.saving.set(true);
    const id = this.editingId();
    const obs = id ? this.hr.updateShift(id, this.form) : this.hr.createShift(this.form);
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

  remove(s: HrShift): void {
    if (!confirm(`¿Eliminar turno ${s.code}?`)) return;
    this.hr.deleteShift(s.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: s.name }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }

  typeLabel(t: HrShiftType): string {
    const map: Record<HrShiftType, string> = {
      morning: 'Mañana', afternoon: 'Tarde', night: 'Noche',
      rotating: 'Rotativo', flexible: 'Flexible', administrative: 'Administrativo',
    };
    return map[t];
  }
  daysLabel(days: number[]): string {
    const map = ['D', 'L', 'M', 'X', 'J', 'V', 'S'];
    return days.map((d) => map[d]).join(' ');
  }
}
