import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-grading',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Calificaciones</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Evaluaciones, notas y calificaciones finales</p>
      </div>

      <!-- Section selector -->
      <div class="flex flex-col sm:flex-row gap-3 mb-6">
        <select [(ngModel)]="selectedSection" (ngModelChange)="loadEvaluations()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">-- Seleccionar sección --</option>
          @for (s of sections(); track s.id) {
            <option [value]="s.id">{{ s.code }}</option>
          }
        </select>
        @if (selectedSection) {
          <button (click)="showEvalModal = true"
            class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
            + Nueva Evaluación
          </button>
          <button (click)="calculateFinals()"
            class="px-4 py-2 text-sm font-medium rounded-lg border border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition">
            Calcular Nota Final
          </button>
        }
      </div>

      @if (selectedSection) {
        <!-- Evaluations -->
        <div class="space-y-4 mb-8">
          @for (ev of evaluations(); track ev.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ ev.name }}</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    Tipo: {{ typeLabel(ev.type) }} | Peso: {{ (ev.weight * 100).toFixed(0) }}% | Máx: {{ ev.max_score }}
                    @if (ev.due_date) { | Fecha: {{ ev.due_date }} }
                  </p>
                </div>
                <button (click)="openGradeModal(ev)"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
                  Calificar
                </button>
              </div>
            </div>
          }
          @if (evaluations().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-6">No hay evaluaciones para esta sección</p>
          }
        </div>

        <!-- Final Grades -->
        @if (finalGrades().length > 0) {
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Notas Finales</h3>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div class="overflow-x-auto custom-scrollbar">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estudiante</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Nota</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Letra</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">GPA</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  @for (fg of finalGrades(); track fg.id) {
                    <tr class="border-b border-gray-100 dark:border-gray-700/50">
                      <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ getStudentName(fg.student_id) }}</td>
                      <td class="px-4 py-3 font-mono text-gray-800 dark:text-white/90">{{ fg.numeric_grade }}</td>
                      <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ fg.letter_grade || '-' }}</td>
                      <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">{{ fg.gpa_points ?? '-' }}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 text-xs rounded-full"
                          [class]="fg.status === 'approved'
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'">
                          {{ fg.status === 'approved' ? 'Aprobado' : 'Reprobado' }}
                        </span>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>
        }
      }

      <!-- Evaluation Modal -->
      @if (showEvalModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showEvalModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Evaluación</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                <input [(ngModel)]="evalForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
                  <select [(ngModel)]="evalForm.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option value="exam">Examen</option>
                    <option value="quiz">Quiz</option>
                    <option value="assignment">Tarea</option>
                    <option value="project">Proyecto</option>
                    <option value="participation">Participación</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Peso (0-1)</label>
                  <input type="number" [(ngModel)]="evalForm.weight" step="0.05" min="0" max="1" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Puntaje máximo</label>
                <input type="number" [(ngModel)]="evalForm.max_score" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showEvalModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="saveEvaluation()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }

      <!-- Grade Modal -->
      @if (showGradeModal && gradeEval) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showGradeModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto custom-scrollbar p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-1">Calificar: {{ gradeEval.name }}</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">Máximo: {{ gradeEval.max_score }}</p>
            <div class="space-y-2">
              @for (g of gradeEntries; track g.student_id; let i = $index) {
                <div class="flex items-center gap-3">
                  <span class="text-sm text-gray-700 dark:text-gray-300 flex-1">{{ g.student_name }}</span>
                  <input type="number" [(ngModel)]="gradeEntries[i].score" [max]="gradeEval.max_score" min="0"
                    class="w-20 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-2 py-1 text-sm text-center" />
                </div>
              }
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showGradeModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="saveGrades()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar Notas</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class GradingComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  sections = signal<any[]>([]);
  evaluations = signal<any[]>([]);
  finalGrades = signal<any[]>([]);
  enrolledStudents = signal<any[]>([]);

  selectedSection = '';
  showEvalModal = false;
  showGradeModal = false;
  gradeEval: any = null;
  gradeEntries: { student_id: string; student_name: string; score: number }[] = [];

  evalForm: any = { name: '', type: 'exam', weight: 0.2, max_score: 100 };

  ngOnInit(): void {
    this.api.get<any[]>('/edu/enrollment/sections').subscribe({ next: (r) => this.sections.set(r) });
  }

  loadEvaluations(): void {
    if (!this.selectedSection) return;

    this.api.get<any[]>('/edu/grading/evaluations', { section_id: this.selectedSection }).subscribe({
      next: (r) => this.evaluations.set(r),
    });
    this.api.get<any[]>(`/edu/grading/final-grades/${this.selectedSection}`).subscribe({
      next: (r) => this.finalGrades.set(r),
    });

    // Load enrolled students for grading
    this.api.get<any[]>(`/edu/enrollment/sections/${this.selectedSection}/students`).subscribe({
      next: (enrollments) => {
        this.api.get<any>('/edu/students', { page_size: 500 }).subscribe({
          next: (res) => {
            const students = res.items || [];
            const mapped = enrollments
              .filter((e: any) => e.status === 'enrolled')
              .map((e: any) => {
                const st = students.find((s: any) => s.id === e.student_id);
                return { student_id: e.student_id, student_name: st ? `${st.first_name} ${st.last_name}` : 'Desconocido', student_code: st?.student_code };
              });
            this.enrolledStudents.set(mapped);
          },
        });
      },
    });
  }

  saveEvaluation(): void {
    this.api.post('/edu/grading/evaluations', {
      section_id: this.selectedSection,
      ...this.evalForm,
    }).subscribe({
      next: () => {
        this.showEvalModal = false;
        this.evalForm = { name: '', type: 'exam', weight: 0.2, max_score: 100 };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Evaluación creada' });
        this.loadEvaluations();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear la evaluación' }),
    });
  }

  openGradeModal(ev: any): void {
    this.gradeEval = ev;
    this.gradeEntries = this.enrolledStudents().map((s) => ({
      student_id: s.student_id,
      student_name: s.student_name,
      score: 0,
    }));
    this.showGradeModal = true;
  }

  saveGrades(): void {
    this.api.post('/edu/grading/grades/bulk', {
      evaluation_id: this.gradeEval.id,
      grades: this.gradeEntries.map((g) => ({
        evaluation_id: this.gradeEval.id,
        student_id: g.student_id,
        score: g.score,
      })),
    }).subscribe({
      next: () => {
        this.showGradeModal = false;
        this.notify.show({ type: 'success', title: 'Listo', message: 'Notas guardadas' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo guardar notas' }),
    });
  }

  calculateFinals(): void {
    this.api.post<any[]>(`/edu/grading/final-grades/${this.selectedSection}/calculate`, {}).subscribe({
      next: (r) => {
        this.finalGrades.set(r);
        this.notify.show({ type: 'success', title: 'Listo', message: 'Notas finales calculadas' });
      },
      error: (err: any) => {
        const msg = err?.error?.detail || 'No se pudo calcular las notas finales';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
      },
    });
  }

  getStudentName(id: string): string {
    return this.enrolledStudents().find((s) => s.student_id === id)?.student_name || id;
  }

  typeLabel(t: string): string {
    return { exam: 'Examen', quiz: 'Quiz', assignment: 'Tarea', project: 'Proyecto', participation: 'Participación' }[t] || t;
  }
}
