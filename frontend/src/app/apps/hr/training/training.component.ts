import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrDeliveryMode,
  HrEmployeeListItem,
  HrEnrollmentStatus,
  HrTrainingCourse,
  HrTrainingCourseCreate,
  HrTrainingEnrollment,
  HrTrainingEnrollmentCreate,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

type Tab = 'courses' | 'enrollments';

@Component({
  selector: 'app-hr-training',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Capacitaciones</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">
            Catálogo de cursos + inscripciones con seguimiento de avance y certificados.
          </p>
        </div>
        @if (tab() === 'courses') {
          <button (click)="openCourseForm()" type="button"
            class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            + Nuevo curso
          </button>
        } @else {
          <button (click)="openEnrollForm()" type="button"
            class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            + Inscribir empleado
          </button>
        }
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

        @case ('courses') {
          <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-4 py-2 font-medium">Código</th>
                  <th class="text-left px-4 py-2 font-medium">Nombre</th>
                  <th class="text-left px-4 py-2 font-medium">Categoría</th>
                  <th class="text-right px-4 py-2 font-medium">Horas</th>
                  <th class="text-left px-4 py-2 font-medium">Modalidad</th>
                  <th class="text-right px-4 py-2 font-medium">Costo</th>
                  <th class="text-left px-4 py-2 font-medium">Estado</th>
                  <th class="text-right px-4 py-2 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @if (loadingCourses()) {
                  <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
                } @else if (courses().length === 0) {
                  <tr><td colspan="8" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin cursos.</td></tr>
                } @else {
                  @for (c of paginatedCourses(); track c.id) {
                    <tr>
                      <td class="px-4 py-2 font-mono text-xs">{{ c.code }}</td>
                      <td class="px-4 py-2 font-medium">
                        {{ c.name }}
                        @if (c.is_mandatory) { <span class="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300">OBLIGATORIO</span> }
                      </td>
                      <td class="px-4 py-2 text-xs">{{ c.category }}</td>
                      <td class="px-4 py-2 text-right">{{ c.duration_hours || '—' }}</td>
                      <td class="px-4 py-2 text-xs">{{ modeLabel(c.delivery_mode) }}</td>
                      <td class="px-4 py-2 text-right font-mono text-xs">{{ c.cost_per_seat ? '$ ' + ((+c.cost_per_seat) | number:'1.0-0') : '—' }}</td>
                      <td class="px-4 py-2">
                        <span class="text-xs px-2 py-0.5 rounded-md"
                          [class]="c.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
                          {{ c.is_active ? 'Activo' : 'Inactivo' }}
                        </span>
                      </td>
                      <td class="px-4 py-2 text-right space-x-2 whitespace-nowrap">
                        <button (click)="openCourseEdit(c)" type="button" class="text-xs text-brand-600 hover:underline">Editar</button>
                        <button (click)="removeCourse(c)" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                      </td>
                    </tr>
                  }
                }
              </tbody>
            </table>
            <app-pagination [totalItems]="courses().length" [(page)]="pageCourses" [(pageSize)]="pageSize" />
          </section>
        }

        @case ('enrollments') {
          <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-4 py-2 font-medium">Curso</th>
                  <th class="text-left px-4 py-2 font-medium">Empleado</th>
                  <th class="text-left px-4 py-2 font-medium">Programado</th>
                  <th class="text-left px-4 py-2 font-medium">Completado</th>
                  <th class="text-right px-4 py-2 font-medium">Puntaje</th>
                  <th class="text-left px-4 py-2 font-medium">Estado</th>
                  <th class="text-right px-4 py-2 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @if (loadingEnrolls()) {
                  <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
                } @else if (enrollments().length === 0) {
                  <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin inscripciones.</td></tr>
                } @else {
                  @for (e of paginatedEnrollments(); track e.id) {
                    <tr>
                      <td class="px-4 py-2 text-xs">{{ courseName(e.course_id) }}</td>
                      <td class="px-4 py-2 text-xs">{{ employeeName(e.employee_id) }}</td>
                      <td class="px-4 py-2 text-xs">{{ e.scheduled_date || '—' }}</td>
                      <td class="px-4 py-2 text-xs">{{ e.completed_date || '—' }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ e.score || '—' }}</td>
                      <td class="px-4 py-2">
                        <span class="text-xs px-2 py-0.5 rounded-md" [class]="enrollStatusClass(e.completion_status)">{{ enrollStatusLabel(e.completion_status) }}</span>
                      </td>
                      <td class="px-4 py-2 text-right space-x-2 whitespace-nowrap">
                        @if (e.completion_status === 'enrolled' || e.completion_status === 'in_progress') {
                          <button (click)="markComplete(e)" type="button" class="text-xs text-emerald-600 hover:underline">Completar</button>
                        }
                        <button (click)="removeEnroll(e)" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                      </td>
                    </tr>
                  }
                }
              </tbody>
            </table>
            <app-pagination [totalItems]="enrollments().length" [(page)]="pageEnrolls" [(pageSize)]="pageSize" />
          </section>
        }
      }

      <!-- Modal curso -->
      @if (courseFormOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeCourseForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
              {{ editingCourseId() ? 'Editar curso' : 'Nuevo curso' }}
            </h3>
            @if (courseFormError()) { <p class="text-sm text-rose-600 mb-3">{{ courseFormError() }}</p> }
            <form (ngSubmit)="saveCourse()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Código *</span>
                <input [(ngModel)]="courseForm.code" name="cc" required [disabled]="!!editingCourseId()"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm disabled:opacity-60" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombre *</span>
                <input [(ngModel)]="courseForm.name" name="cn" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Categoría</span>
                <input [(ngModel)]="courseForm.category" name="cat"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Duración (h)</span>
                <input type="number" step="0.5" [(ngModel)]="courseForm.duration_hours" name="dh"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Modalidad</span>
                <select [(ngModel)]="courseForm.delivery_mode" name="dm"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="in_person">Presencial</option>
                  <option value="virtual_live">Virtual sincrónica</option>
                  <option value="virtual_async">Virtual asincrónica</option>
                  <option value="hybrid">Híbrida</option>
                  <option value="external">Externa</option>
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Costo por cupo</span>
                <input type="number" step="1000" [(ngModel)]="courseForm.cost_per_seat" name="cs"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Proveedor</span>
                <input [(ngModel)]="courseForm.provider" name="pr"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block sm:col-span-2">
                <span class="text-xs text-slate-600 dark:text-slate-400">Descripción</span>
                <textarea [(ngModel)]="courseForm.description" name="desc" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
              <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" [(ngModel)]="courseForm.is_mandatory" name="im" />
                <span class="text-slate-700 dark:text-slate-300">Obligatorio</span>
              </label>
              <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" [(ngModel)]="courseForm.is_active" name="ia" />
                <span class="text-slate-700 dark:text-slate-300">Activo</span>
              </label>
              <div class="sm:col-span-2 flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeCourseForm()" class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="savingCourse()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ savingCourse() ? '...' : 'Guardar' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }

      <!-- Modal inscripción -->
      @if (enrollFormOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeEnrollForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Inscribir empleado</h3>
            @if (enrollFormError()) { <p class="text-sm text-rose-600 mb-3">{{ enrollFormError() }}</p> }
            <form (ngSubmit)="saveEnroll()" class="space-y-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Curso *</span>
                <select [(ngModel)]="enrollForm.course_id" name="ec" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="">— Selecciona —</option>
                  @for (c of courses(); track c.id) {
                    <option [value]="c.id">{{ c.name }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Empleado *</span>
                <select [(ngModel)]="enrollForm.employee_id" name="ee" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="">— Selecciona —</option>
                  @for (em of employees(); track em.id) {
                    <option [value]="em.id">{{ em.first_name }} {{ em.last_name }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fecha programada</span>
                <input type="date" [(ngModel)]="enrollForm.scheduled_date" name="esd"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <div class="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeEnrollForm()" class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="savingEnroll()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ savingEnroll() ? '...' : 'Inscribir' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrTrainingComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  readonly tabs: { value: Tab; label: string }[] = [
    { value: 'courses', label: 'Catálogo' },
    { value: 'enrollments', label: 'Inscripciones' },
  ];

  tab = signal<Tab>('courses');
  loadingCourses = signal(true);
  loadingEnrolls = signal(true);

  courses = signal<HrTrainingCourse[]>([]);
  enrollments = signal<HrTrainingEnrollment[]>([]);
  employees = signal<HrEmployeeListItem[]>([]);

  pageSize = signal(20);
  pageCourses = signal(0);
  pageEnrolls = signal(0);
  paginatedCourses = computed(() => {
    const s = this.pageCourses() * this.pageSize();
    return this.courses().slice(s, s + this.pageSize());
  });
  paginatedEnrollments = computed(() => {
    const s = this.pageEnrolls() * this.pageSize();
    return this.enrollments().slice(s, s + this.pageSize());
  });

  courseFormOpen = signal(false);
  editingCourseId = signal<string | null>(null);
  savingCourse = signal(false);
  courseFormError = signal('');
  courseForm: HrTrainingCourseCreate = this.emptyCourseForm();

  enrollFormOpen = signal(false);
  savingEnroll = signal(false);
  enrollFormError = signal('');
  enrollForm: HrTrainingEnrollmentCreate = this.emptyEnrollForm();

  constructor() {
    effect(() => { this.courses(); this.pageCourses.set(0); }, { allowSignalWrites: true });
    effect(() => { this.enrollments(); this.pageEnrolls.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    this.loadCourses();
    this.loadEnrollments();
    this.hr.listEmployees({ status: 'active' }).subscribe({ next: (r) => this.employees.set(r) });
  }

  loadCourses(): void {
    this.loadingCourses.set(true);
    this.hr.listTrainingCourses().subscribe({
      next: (r) => { this.courses.set(r); this.loadingCourses.set(false); },
      error: () => { this.loadingCourses.set(false); },
    });
  }

  loadEnrollments(): void {
    this.loadingEnrolls.set(true);
    this.hr.listTrainingEnrollments().subscribe({
      next: (r) => { this.enrollments.set(r); this.loadingEnrolls.set(false); },
      error: () => { this.loadingEnrolls.set(false); },
    });
  }

  emptyCourseForm(): HrTrainingCourseCreate {
    return {
      code: '', name: '', description: null,
      category: 'general', duration_hours: null,
      delivery_mode: 'in_person', is_mandatory: false,
      provider: null, cost_per_seat: null, is_active: true,
    };
  }
  emptyEnrollForm(): HrTrainingEnrollmentCreate {
    return { course_id: '', employee_id: '', scheduled_date: null, notes: null };
  }

  openCourseForm(): void { this.editingCourseId.set(null); this.courseForm = this.emptyCourseForm(); this.courseFormError.set(''); this.courseFormOpen.set(true); }
  openCourseEdit(c: HrTrainingCourse): void {
    this.editingCourseId.set(c.id);
    this.courseForm = {
      code: c.code, name: c.name, description: c.description, category: c.category,
      duration_hours: c.duration_hours, delivery_mode: c.delivery_mode,
      is_mandatory: c.is_mandatory, provider: c.provider, cost_per_seat: c.cost_per_seat,
      is_active: c.is_active,
    };
    this.courseFormError.set(''); this.courseFormOpen.set(true);
  }
  closeCourseForm(): void { this.courseFormOpen.set(false); }

  saveCourse(): void {
    this.savingCourse.set(true);
    const id = this.editingCourseId();
    const obs = id ? this.hr.updateTrainingCourse(id, this.courseForm) : this.hr.createTrainingCourse(this.courseForm);
    obs.subscribe({
      next: () => { this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: this.courseForm.name }); this.savingCourse.set(false); this.courseFormOpen.set(false); this.loadCourses(); },
      error: (err) => { this.savingCourse.set(false); this.courseFormError.set(err?.error?.detail || 'No se pudo guardar.'); },
    });
  }
  removeCourse(c: HrTrainingCourse): void {
    if (!confirm(`¿Eliminar ${c.name}?`)) return;
    this.hr.deleteTrainingCourse(c.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: c.name }); this.loadCourses(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }

  openEnrollForm(): void { this.enrollForm = this.emptyEnrollForm(); this.enrollFormError.set(''); this.enrollFormOpen.set(true); }
  closeEnrollForm(): void { this.enrollFormOpen.set(false); }

  saveEnroll(): void {
    this.savingEnroll.set(true);
    this.hr.createTrainingEnrollment(this.enrollForm).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Inscrito', message: 'Inscripción creada' }); this.savingEnroll.set(false); this.enrollFormOpen.set(false); this.loadEnrollments(); },
      error: (err) => { this.savingEnroll.set(false); this.enrollFormError.set(err?.error?.detail || 'No se pudo inscribir.'); },
    });
  }

  markComplete(e: HrTrainingEnrollment): void {
    const scoreStr = prompt('Puntaje obtenido (opcional):');
    const payload: { completion_status: HrEnrollmentStatus; completed_date: string; score?: string } = {
      completion_status: 'completed',
      completed_date: new Date().toISOString().slice(0, 10),
    };
    if (scoreStr && !isNaN(+scoreStr)) payload.score = scoreStr;
    this.hr.updateTrainingEnrollment(e.id, payload).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Completado', message: this.courseName(e.course_id) }); this.loadEnrollments(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'Error.' }),
    });
  }

  removeEnroll(e: HrTrainingEnrollment): void {
    if (!confirm('¿Eliminar inscripción?')) return;
    this.hr.deleteTrainingEnrollment(e.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminada', message: '' }); this.loadEnrollments(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }

  courseName(id: string): string { return this.courses().find((x) => x.id === id)?.name ?? id.slice(0, 8); }
  employeeName(id: string): string {
    const e = this.employees().find((x) => x.id === id);
    return e ? `${e.first_name} ${e.last_name || ''}`.trim() : id.slice(0, 8);
  }

  modeLabel(m: HrDeliveryMode): string {
    const map: Record<HrDeliveryMode, string> = {
      in_person: 'Presencial', virtual_live: 'Virtual sync', virtual_async: 'Virtual async',
      hybrid: 'Híbrida', external: 'Externa',
    };
    return map[m];
  }
  enrollStatusLabel(s: HrEnrollmentStatus): string {
    const map: Record<HrEnrollmentStatus, string> = {
      enrolled: 'Inscrito', in_progress: 'En curso', completed: 'Completado',
      failed: 'No aprobado', cancelled: 'Cancelado',
    };
    return map[s];
  }
  enrollStatusClass(s: HrEnrollmentStatus): string {
    const map: Record<HrEnrollmentStatus, string> = {
      enrolled: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      failed: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      cancelled: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    };
    return map[s];
  }
}
