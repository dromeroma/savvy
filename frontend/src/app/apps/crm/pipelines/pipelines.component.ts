import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pipelines',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Pipelines</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Configura tus embudos de ventas</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Pipeline</button>
      </div>
      @for (p of pipelines(); track p.id) {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-4">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ p.name }}</h4>
              @if (p.description) { <p class="text-xs text-gray-500 dark:text-gray-400">{{ p.description }}</p> }
            </div>
            @if (p.is_default) { <span class="px-2 py-1 text-xs font-medium rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">Predeterminado</span> }
          </div>
          <div class="flex flex-wrap gap-2">
            @for (s of p.stages; track s.id) {
              <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs" [style.border-color]="s.color || '#d1d5db'" [style.background-color]="(s.color || '#f3f4f6') + '15'">
                <span class="font-medium text-gray-800 dark:text-white/90">{{ s.name }}</span>
                <span class="text-gray-500 dark:text-gray-400">{{ s.probability }}%</span>
                @if (s.is_won) { <span class="text-green-600">✓</span> }
                @if (s.is_lost) { <span class="text-red-600">✗</span> }
              </div>
            }
          </div>
        </div>
      }
      @if (pipelines().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay pipelines configurados</p> }
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto custom-scrollbar p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Pipeline</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label><input [(ngModel)]="form.description" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"><input type="checkbox" [(ngModel)]="form.is_default" class="rounded border-gray-300" /> Predeterminado</label>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Etapas</label>
                @for (s of form.stages; track $index) {
                  <div class="flex gap-2 mb-2">
                    <input [(ngModel)]="s.name" placeholder="Nombre" class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-2 py-1 text-sm" />
                    <input type="number" [(ngModel)]="s.probability" placeholder="%" min="0" max="100" class="w-16 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-2 py-1 text-sm" />
                    <label class="flex items-center gap-1 text-xs text-green-600"><input type="checkbox" [(ngModel)]="s.is_won" /> Won</label>
                    <label class="flex items-center gap-1 text-xs text-red-600"><input type="checkbox" [(ngModel)]="s.is_lost" /> Lost</label>
                    <button (click)="form.stages.splice($index, 1)" class="text-red-500 px-1">✕</button>
                  </div>
                }
                <button (click)="form.stages.push({ name: '', sort_order: form.stages.length, probability: 0, is_won: false, is_lost: false })" class="text-sm text-brand-600 dark:text-brand-400 hover:underline">+ Agregar etapa</button>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PipelinesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  pipelines = signal<any[]>([]);
  showModal = false;
  form: any = { name: '', description: '', is_default: false, stages: [
    { name: 'Contacto inicial', sort_order: 0, probability: 10, is_won: false, is_lost: false },
    { name: 'Calificado', sort_order: 1, probability: 25, is_won: false, is_lost: false },
    { name: 'Propuesta', sort_order: 2, probability: 50, is_won: false, is_lost: false },
    { name: 'Negociación', sort_order: 3, probability: 75, is_won: false, is_lost: false },
    { name: 'Cerrado Ganado', sort_order: 4, probability: 100, is_won: true, is_lost: false },
    { name: 'Cerrado Perdido', sort_order: 5, probability: 0, is_won: false, is_lost: true },
  ] };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/crm/pipelines').subscribe({ next: (r) => this.pipelines.set(r) }); }
  save(): void {
    this.api.post('/crm/pipelines', this.form).subscribe({
      next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Pipeline creado' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
}
