import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-programs',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Programas Académicos</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Carreras, técnicos y diplomados</p>
        </div>
        <button (click)="showModal = true"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
          + Nuevo Programa
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="grid gap-4">
          @for (p of programs(); track p.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <div class="flex items-center justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ p.code }}</span>
                    <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ p.name }}</h4>
                  </div>
                  <div class="flex flex-wrap gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                    @if (p.degree_type) { <span>Nivel: {{ p.degree_type }}</span> }
                    @if (p.duration_periods) { <span>Duración: {{ p.duration_periods }} periodos</span> }
                    @if (p.credits_required) { <span>Créditos: {{ p.credits_required }}</span> }
                  </div>
                </div>
                <span class="px-2 py-1 text-xs font-medium rounded-full"
                  [class]="p.status === 'active'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400'">
                  {{ p.status === 'active' ? 'Activo' : 'Inactivo' }}
                </span>
              </div>
            </div>
          }
          @if (programs().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No hay programas registrados</p>
          }
        </div>
      }

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Programa</h3>
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
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nivel</label>
                  <select [(ngModel)]="form.degree_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option value="">--</option>
                    <option value="technical">Técnico</option>
                    <option value="diploma">Diplomado</option>
                    <option value="bachelor">Pregrado</option>
                    <option value="master">Maestría</option>
                    <option value="doctorate">Doctorado</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Periodos</label>
                  <input type="number" [(ngModel)]="form.duration_periods" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Créditos</label>
                  <input type="number" [(ngModel)]="form.credits_required" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
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
export class ProgramsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  programs = signal<any[]>([]);
  loading = signal(false);
  showModal = false;

  form: any = { code: '', name: '', degree_type: '', duration_periods: null, credits_required: null, description: '' };

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.get<any[]>('/edu/structure/programs').subscribe({
      next: (r) => { this.programs.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  save(): void {
    const payload = { ...this.form };
    if (!payload.degree_type) delete payload.degree_type;
    if (!payload.duration_periods) delete payload.duration_periods;
    if (!payload.credits_required) delete payload.credits_required;
    if (!payload.description) delete payload.description;

    this.api.post('/edu/structure/programs', payload).subscribe({
      next: () => {
        this.showModal = false;
        this.form = { code: '', name: '', degree_type: '', duration_periods: null, credits_required: null, description: '' };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Programa creado' });
        this.load();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el programa' }),
    });
  }
}
