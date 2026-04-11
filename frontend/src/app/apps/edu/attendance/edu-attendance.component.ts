import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';
import { DatePickerComponent } from '../../../shared/components/form/date-picker/date-picker.component';

@Component({
  selector: 'app-edu-attendance',
  imports: [CommonModule, FormsModule, DatePickerComponent],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Asistencia</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Registro de asistencia por sección</p>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 mb-6">
        <select [(ngModel)]="selectedSection" (ngModelChange)="loadEnrollments()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">-- Seleccionar sección --</option>
          @for (s of sections(); track s.id) {
            <option [value]="s.id">{{ s.code }}</option>
          }
        </select>
        <div class="flex flex-col gap-1">
          <app-date-picker
            id="att_date"
            label="Fecha"
            [defaultDate]="selectedDate"
            (dateChange)="selectedDate = $event"
          />
        </div>
        <div class="flex items-end">
          <button (click)="loadAttendance()" [disabled]="!selectedSection"
            class="h-11 px-5 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition disabled:opacity-50 disabled:cursor-not-allowed">
            Cargar
          </button>
        </div>
      </div>

      @if (enrolledStudents().length > 0) {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Código</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estudiante</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
                </tr>
              </thead>
              <tbody>
                @for (st of enrolledStudents(); track st.student_id; let i = $index) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50">
                    <td class="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">{{ st.student_code }}</td>
                    <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ st.student_name }}</td>
                    <td class="px-4 py-3">
                      <select [(ngModel)]="attendanceRecords[i].status"
                        class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-2 py-1 text-xs">
                        <option value="present">Presente</option>
                        <option value="absent">Ausente</option>
                        <option value="late">Tarde</option>
                        <option value="excused">Excusado</option>
                      </select>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          <div class="p-4 border-t border-gray-200 dark:border-gray-700">
            <button (click)="saveAttendance()"
              class="px-5 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
              Guardar Asistencia
            </button>
          </div>
        </div>
      } @else if (selectedSection) {
        <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
          No hay estudiantes matriculados en esta sección
        </p>
      }
    </div>
  `,
})
export class EduAttendanceComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  sections = signal<any[]>([]);
  enrolledStudents = signal<any[]>([]);
  attendanceRecords: { student_id: string; status: string }[] = [];

  selectedSection = '';
  selectedDate = '';

  ngOnInit(): void {
    const now = new Date();
    this.selectedDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    this.api.get<any[]>('/edu/enrollment/sections').subscribe({ next: (r) => this.sections.set(r) });
  }

  loadEnrollments(): void {
    if (!this.selectedSection) return;

    this.api.get<any[]>(`/edu/enrollment/sections/${this.selectedSection}/students`).subscribe({
      next: (enrollments) => {
        // For each enrollment, load student info
        this.api.get<any>('/edu/students', { page_size: 500 }).subscribe({
          next: (studentsRes) => {
            const students = studentsRes.items || [];
            const mapped = enrollments
              .filter((e: any) => e.status === 'enrolled')
              .map((e: any) => {
                const st = students.find((s: any) => s.id === e.student_id);
                return {
                  student_id: e.student_id,
                  student_code: st?.student_code || '?',
                  student_name: st ? `${st.first_name} ${st.last_name}` : 'Desconocido',
                };
              });
            this.enrolledStudents.set(mapped);
            this.attendanceRecords = mapped.map((s: any) => ({ student_id: s.student_id, status: 'present' }));
          },
        });
      },
    });
  }

  loadAttendance(): void {
    this.loadEnrollments();
  }

  saveAttendance(): void {
    if (!this.selectedSection || !this.selectedDate) return;

    this.api.post('/edu/attendance/bulk', {
      section_id: this.selectedSection,
      date: this.selectedDate,
      records: this.attendanceRecords,
    }).subscribe({
      next: () => this.notify.show({ type: 'success', title: 'Listo', message: 'Asistencia registrada' }),
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo registrar la asistencia' }),
    });
  }
}
