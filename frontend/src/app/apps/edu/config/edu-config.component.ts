import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-edu-config',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Configuración Académica</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Sistemas de calificación, tipos de periodo y modelos de evaluación
          </p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-6 border-b border-gray-200 dark:border-gray-700">
        @for (tab of tabs; track tab.key) {
          <button (click)="activeTab = tab.key"
            class="px-4 py-2.5 text-sm font-medium transition rounded-t-lg"
            [class]="activeTab === tab.key
              ? 'text-brand-600 dark:text-brand-400 border-b-2 border-brand-600 dark:border-brand-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'">
            {{ tab.label }}
          </button>
        }
      </div>

      <!-- Grading Systems Tab -->
      @if (activeTab === 'grading') {
        <div class="space-y-4">
          <div class="flex justify-end">
            <button (click)="showGradingModal = true"
              class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
              + Nuevo Sistema
            </button>
          </div>
          @for (gs of gradingSystems(); track gs.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ gs.name }}</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    Tipo: {{ gs.type }} | Rango: {{ gs.scale_min }} - {{ gs.scale_max }} | Aprobación: {{ gs.passing_grade }}
                  </p>
                </div>
                @if (gs.is_default) {
                  <span class="px-2 py-1 text-xs font-medium rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
                    Predeterminado
                  </span>
                }
              </div>
              @if (gs.scales && gs.scales.length > 0) {
                <div class="flex flex-wrap gap-2">
                  @for (scale of gs.scales; track scale.id) {
                    <span class="px-2 py-1 text-xs rounded border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400"
                      [class.bg-green-50]="scale.is_passing" [class.dark:bg-green-900/20]="scale.is_passing"
                      [class.bg-red-50]="!scale.is_passing" [class.dark:bg-red-900/20]="!scale.is_passing">
                      {{ scale.label }} ({{ scale.min_value }}-{{ scale.max_value }})
                    </span>
                  }
                </div>
              }
            </div>
          }
          @if (gradingSystems().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
              No hay sistemas de calificación configurados
            </p>
          }
        </div>
      }

      <!-- Period Types Tab -->
      @if (activeTab === 'periods') {
        <div class="space-y-4">
          <div class="flex justify-end">
            <button (click)="showPeriodModal = true"
              class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
              + Nuevo Tipo
            </button>
          </div>
          @for (pt of periodTypes(); track pt.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 flex items-center justify-between">
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ pt.name }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Código: {{ pt.code }} | Duración: {{ pt.default_duration_weeks }} semanas
                </p>
              </div>
            </div>
          }
          @if (periodTypes().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
              No hay tipos de periodo configurados
            </p>
          }
        </div>
      }

      <!-- Evaluation Templates Tab -->
      @if (activeTab === 'evaluation') {
        <div class="space-y-4">
          <div class="flex justify-end">
            <button (click)="showEvalModal = true"
              class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
              + Nueva Plantilla
            </button>
          </div>
          @for (et of evalTemplates(); track et.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ et.name }}</h4>
                  @if (et.description) {
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ et.description }}</p>
                  }
                </div>
                @if (et.is_default) {
                  <span class="px-2 py-1 text-xs font-medium rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
                    Predeterminada
                  </span>
                }
              </div>
              <div class="flex flex-wrap gap-2">
                @for (comp of et.components; track comp.name) {
                  <span class="px-2 py-1 text-xs rounded border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400">
                    {{ comp.name }}: {{ (comp.weight * 100).toFixed(0) }}%
                  </span>
                }
              </div>
            </div>
          }
          @if (evalTemplates().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
              No hay plantillas de evaluación configuradas
            </p>
          }
        </div>
      }

      <!-- Grading System Modal -->
      @if (showGradingModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showGradingModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Sistema de Calificación</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                <input [(ngModel)]="gsForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
                  <select [(ngModel)]="gsForm.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option value="numeric">Numérico</option>
                    <option value="letter">Letras</option>
                    <option value="percentage">Porcentaje</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mínimo</label>
                  <input type="number" [(ngModel)]="gsForm.scale_min" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Máximo</label>
                  <input type="number" [(ngModel)]="gsForm.scale_max" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nota de aprobación</label>
                  <input type="number" [(ngModel)]="gsForm.passing_grade" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div class="flex items-end">
                  <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input type="checkbox" [(ngModel)]="gsForm.is_default" class="rounded border-gray-300" />
                    Predeterminado
                  </label>
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showGradingModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="saveGradingSystem()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }

      <!-- Period Type Modal -->
      @if (showPeriodModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showPeriodModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Tipo de Periodo</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código</label>
                <input [(ngModel)]="ptForm.code" placeholder="semester" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                <input [(ngModel)]="ptForm.name" placeholder="Semestre" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duración (semanas)</label>
                <input type="number" [(ngModel)]="ptForm.default_duration_weeks" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showPeriodModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="savePeriodType()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }

      <!-- Evaluation Template Modal -->
      @if (showEvalModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showEvalModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Plantilla de Evaluación</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                <input [(ngModel)]="etForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label>
                <input [(ngModel)]="etForm.description" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Componentes</label>
                @for (comp of etForm.components; track $index) {
                  <div class="flex gap-2 mb-2">
                    <input [(ngModel)]="comp.name" placeholder="Nombre" class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                    <input type="number" [(ngModel)]="comp.weight" placeholder="Peso (0-1)" step="0.05" min="0" max="1"
                      class="w-24 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                    <select [(ngModel)]="comp.type" class="w-28 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-2 py-2 text-sm">
                      <option value="exam">Examen</option>
                      <option value="quiz">Quiz</option>
                      <option value="assignment">Tarea</option>
                      <option value="project">Proyecto</option>
                      <option value="participation">Participación</option>
                    </select>
                    <button (click)="etForm.components.splice($index, 1)" class="text-red-500 hover:text-red-700 px-2">✕</button>
                  </div>
                }
                <button (click)="etForm.components.push({ name: '', weight: 0, type: 'exam' })"
                  class="text-sm text-brand-600 dark:text-brand-400 hover:underline">+ Agregar componente</button>
              </div>
              <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input type="checkbox" [(ngModel)]="etForm.is_default" class="rounded border-gray-300" />
                Predeterminada
              </label>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showEvalModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="saveEvalTemplate()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class EduConfigComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  gradingSystems = signal<any[]>([]);
  periodTypes = signal<any[]>([]);
  evalTemplates = signal<any[]>([]);

  activeTab = 'grading';
  tabs = [
    { key: 'grading', label: 'Calificaciones' },
    { key: 'periods', label: 'Tipos de Periodo' },
    { key: 'evaluation', label: 'Evaluación' },
  ];

  showGradingModal = false;
  showPeriodModal = false;
  showEvalModal = false;

  gsForm = { name: '', type: 'numeric', scale_min: 0, scale_max: 5, passing_grade: 3, is_default: false };
  ptForm = { code: '', name: '', default_duration_weeks: 16 };
  etForm: { name: string; description: string; components: { name: string; weight: number; type: string }[]; is_default: boolean } = {
    name: '',
    description: '',
    components: [{ name: '', weight: 0, type: 'exam' }],
    is_default: false,
  };

  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.api.get<any[]>('/edu/config/grading-systems').subscribe({
      next: (r) => this.gradingSystems.set(r),
    });
    this.api.get<any[]>('/edu/config/period-types').subscribe({
      next: (r) => this.periodTypes.set(r),
    });
    this.api.get<any[]>('/edu/config/evaluation-templates').subscribe({
      next: (r) => this.evalTemplates.set(r),
    });
  }

  saveGradingSystem(): void {
    this.api.post('/edu/config/grading-systems', this.gsForm).subscribe({
      next: () => {
        this.showGradingModal = false;
        this.gsForm = { name: '', type: 'numeric', scale_min: 0, scale_max: 5, passing_grade: 3, is_default: false };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Sistema de calificación creado' });
        this.loadAll();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el sistema' }),
    });
  }

  savePeriodType(): void {
    this.api.post('/edu/config/period-types', this.ptForm).subscribe({
      next: () => {
        this.showPeriodModal = false;
        this.ptForm = { code: '', name: '', default_duration_weeks: 16 };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Tipo de periodo creado' });
        this.loadAll();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el tipo' }),
    });
  }

  saveEvalTemplate(): void {
    this.api.post('/edu/config/evaluation-templates', this.etForm).subscribe({
      next: () => {
        this.showEvalModal = false;
        this.etForm = { name: '', description: '', components: [{ name: '', weight: 0, type: 'exam' }], is_default: false };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Plantilla de evaluación creada' });
        this.loadAll();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear la plantilla' }),
    });
  }
}
