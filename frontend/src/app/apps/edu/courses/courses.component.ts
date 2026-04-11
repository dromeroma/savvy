import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-courses',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Cursos / Materias</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Catálogo de asignaturas</p>
        </div>
        <button (click)="showModal = true"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
          + Nuevo Curso
        </button>
      </div>

      <!-- Search -->
      <div class="mb-4">
        <input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar por código o nombre..."
          class="w-full sm:w-80 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Código</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Nombre</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Créditos</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Horas/Sem</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Tipo</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
                </tr>
              </thead>
              <tbody>
                @for (c of courses(); track c.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                    <td class="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">{{ c.code }}</td>
                    <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ c.name }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ c.credits }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ c.weekly_hours }}</td>
                    <td class="px-4 py-3">
                      <span class="px-2 py-0.5 text-xs rounded-full"
                        [class]="c.is_elective
                          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'">
                        {{ c.is_elective ? 'Electiva' : 'Obligatoria' }}
                      </span>
                    </td>
                    <td class="px-4 py-3">
                      <span class="px-2 py-0.5 text-xs rounded-full"
                        [class]="c.status === 'active'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'">
                        {{ c.status === 'active' ? 'Activo' : 'Inactivo' }}
                      </span>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (courses().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No hay cursos registrados</p>
          }
          @if (total() > courses().length) {
            <div class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700">
              Mostrando {{ courses().length }} de {{ total() }}
            </div>
          }
        </div>
      }

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Curso</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código</label>
                  <input [(ngModel)]="form.code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                  <input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Créditos</label>
                  <input type="number" [(ngModel)]="form.credits" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Horas/Semana</label>
                  <input type="number" [(ngModel)]="form.weekly_hours" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div class="flex items-end">
                  <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 pb-2">
                    <input type="checkbox" [(ngModel)]="form.is_elective" class="rounded border-gray-300" />
                    Electiva
                  </label>
                </div>
              </div>
              @if (programs().length > 0) {
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Programa (opcional)</label>
                  <select [(ngModel)]="form.program_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option [ngValue]="null">-- Sin programa --</option>
                    @for (p of programs(); track p.id) {
                      <option [ngValue]="p.id">{{ p.code }} - {{ p.name }}</option>
                    }
                  </select>
                </div>
              }
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label>
                <textarea [(ngModel)]="form.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CoursesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  courses = signal<any[]>([]);
  programs = signal<any[]>([]);
  total = signal(0);
  loading = signal(false);
  showModal = false;
  search = '';

  form: any = { code: '', name: '', credits: 0, weekly_hours: 0, is_elective: false, program_id: null, description: '' };

  ngOnInit(): void {
    this.load();
    this.api.get<any[]>('/edu/structure/programs').subscribe({
      next: (r) => this.programs.set(r),
    });
  }

  load(): void {
    this.loading.set(true);
    const params: any = { page_size: 100 };
    if (this.search) params.search = this.search;

    this.api.get<any>('/edu/structure/courses', params).subscribe({
      next: (r) => { this.courses.set(r.items); this.total.set(r.total); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  save(): void {
    const payload = { ...this.form };
    if (!payload.program_id) delete payload.program_id;
    if (!payload.description) delete payload.description;

    this.api.post('/edu/structure/courses', payload).subscribe({
      next: () => {
        this.showModal = false;
        this.form = { code: '', name: '', credits: 0, weekly_hours: 0, is_elective: false, program_id: null, description: '' };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Curso creado' });
        this.load();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el curso' }),
    });
  }
}
