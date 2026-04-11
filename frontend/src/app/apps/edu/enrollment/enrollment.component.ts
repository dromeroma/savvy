import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-enrollment',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Secciones y Matrícula</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Secciones de cursos, matrícula de estudiantes</p>
        </div>
        <button (click)="showSectionModal = true"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
          + Nueva Sección
        </button>
      </div>

      <!-- Period Filter -->
      <div class="mb-4">
        <select [(ngModel)]="selectedPeriod" (ngModelChange)="loadSections()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos los periodos</option>
          @for (p of periods(); track p.id) {
            <option [value]="p.id">{{ p.name }}</option>
          }
        </select>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="grid gap-4">
          @for (s of sections(); track s.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ s.code }}</h4>
                  <div class="flex gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                    <span>Capacidad: {{ s.enrolled_count }} / {{ s.capacity }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="px-2 py-1 text-xs rounded-full"
                    [class]="s.status === 'open'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'">
                    {{ s.status === 'open' ? 'Abierta' : s.status === 'closed' ? 'Cerrada' : 'Cancelada' }}
                  </span>
                  <button (click)="openEnrollModal(s)"
                    class="px-3 py-1 text-xs font-medium rounded-lg border border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition">
                    Matricular
                  </button>
                </div>
              </div>
              <!-- Progress bar -->
              <div class="mt-3 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full bg-brand-500 rounded-full transition-all"
                  [style.width.%]="(s.enrolled_count / s.capacity) * 100"></div>
              </div>
            </div>
          }
          @if (sections().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No hay secciones registradas</p>
          }
        </div>
      }

      <!-- Section Modal -->
      @if (showSectionModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showSectionModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Sección</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código</label>
                <input [(ngModel)]="sectionForm.code" placeholder="MAT101-A" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Curso</label>
                <select [(ngModel)]="sectionForm.course_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">-- Seleccionar --</option>
                  @for (c of courses(); track c.id) {
                    <option [value]="c.id">{{ c.code }} - {{ c.name }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Periodo</label>
                <select [(ngModel)]="sectionForm.academic_period_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">-- Seleccionar --</option>
                  @for (p of periods(); track p.id) {
                    <option [value]="p.id">{{ p.name }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Docente (opcional)</label>
                <select [(ngModel)]="sectionForm.teacher_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">-- Sin asignar --</option>
                  @for (t of teachers(); track t.id) {
                    <option [value]="t.id">{{ t.first_name }} {{ t.last_name }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidad</label>
                <input type="number" [(ngModel)]="sectionForm.capacity" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showSectionModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="saveSection()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }

      <!-- Enroll Modal -->
      @if (showEnrollModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showEnrollModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Matricular en {{ enrollSection?.code }}</h3>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estudiante</label>
              <select [(ngModel)]="enrollStudentId" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                <option value="">-- Seleccionar --</option>
                @for (st of students(); track st.id) {
                  <option [value]="st.id">{{ st.student_code }} - {{ st.first_name }} {{ st.last_name }}</option>
                }
              </select>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showEnrollModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="enrollStudent()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Matricular</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class EnrollmentComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  sections = signal<any[]>([]);
  periods = signal<any[]>([]);
  courses = signal<any[]>([]);
  teachers = signal<any[]>([]);
  students = signal<any[]>([]);
  loading = signal(false);

  selectedPeriod = '';
  showSectionModal = false;
  showEnrollModal = false;
  enrollSection: any = null;
  enrollStudentId = '';

  sectionForm: any = { code: '', course_id: '', academic_period_id: '', teacher_id: '', capacity: 30 };

  ngOnInit(): void {
    this.api.get<any[]>('/edu/structure/periods').subscribe({ next: (r) => this.periods.set(r) });
    this.api.get<any>('/edu/structure/courses', { page_size: 200 }).subscribe({ next: (r) => this.courses.set(r.items || []) });
    this.api.get<any>('/edu/teachers', { page_size: 200 }).subscribe({ next: (r) => this.teachers.set(r.items || []) });
    this.api.get<any>('/edu/students', { page_size: 500 }).subscribe({ next: (r) => this.students.set(r.items || []) });
    this.loadSections();
  }

  loadSections(): void {
    this.loading.set(true);
    const params: any = {};
    if (this.selectedPeriod) params.period_id = this.selectedPeriod;

    this.api.get<any[]>('/edu/enrollment/sections', params).subscribe({
      next: (r) => { this.sections.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  saveSection(): void {
    const payload: any = {
      code: this.sectionForm.code,
      course_id: this.sectionForm.course_id,
      academic_period_id: this.sectionForm.academic_period_id,
      capacity: this.sectionForm.capacity,
    };
    if (this.sectionForm.teacher_id) payload.teacher_id = this.sectionForm.teacher_id;

    this.api.post('/edu/enrollment/sections', payload).subscribe({
      next: () => {
        this.showSectionModal = false;
        this.sectionForm = { code: '', course_id: '', academic_period_id: '', teacher_id: '', capacity: 30 };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Sección creada' });
        this.loadSections();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear la sección' }),
    });
  }

  openEnrollModal(section: any): void {
    this.enrollSection = section;
    this.enrollStudentId = '';
    this.showEnrollModal = true;
  }

  enrollStudent(): void {
    if (!this.enrollStudentId || !this.enrollSection) return;

    this.api.post('/edu/enrollment/enroll', {
      student_id: this.enrollStudentId,
      section_id: this.enrollSection.id,
    }).subscribe({
      next: (r: any) => {
        this.showEnrollModal = false;
        if (r.type === 'waitlist') {
          this.notify.show({ type: 'warning', title: 'En lista de espera', message: `Posición: ${r.position}` });
        } else {
          this.notify.show({ type: 'success', title: 'Listo', message: 'Estudiante matriculado' });
        }
        this.loadSections();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo matricular' }),
    });
  }
}
