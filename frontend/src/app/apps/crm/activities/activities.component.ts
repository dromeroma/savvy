import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-crm-activities',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Actividades</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Llamadas, reuniones, tareas y notas</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nueva Actividad</button>
      </div>
      <div class="space-y-3">
        @for (a of activities(); track a.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex justify-between items-start">
            <div class="flex items-start gap-3">
              <span class="text-lg mt-0.5">{{ typeIcon(a.type) }}</span>
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-white/90" [class.line-through]="a.completed">{{ a.subject }}</p>
                @if (a.description) { <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ a.description }}</p> }
                <div class="flex gap-3 text-xs text-gray-400 mt-1">
                  <span>{{ typeLabel(a.type) }}</span>
                  @if (a.due_date) { <span>Vence: {{ a.due_date }}</span> }
                </div>
              </div>
            </div>
            @if (!a.completed) {
              <button (click)="complete(a)" class="px-3 py-1 text-xs rounded-lg border border-green-500 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition">Completar</button>
            } @else {
              <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Completada</span>
            }
          </div>
        }
        @if (activities().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay actividades</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Actividad</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="call">Llamada</option><option value="meeting">Reunión</option><option value="email">Email</option><option value="task">Tarea</option><option value="note">Nota</option></select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Asunto</label><input [(ngModel)]="form.subject" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label><textarea [(ngModel)]="form.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
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
export class CrmActivitiesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  activities = signal<any[]>([]);
  showModal = false;
  form: any = { type: 'call', subject: '', description: '' };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/crm/activities').subscribe({ next: (r) => this.activities.set(r) }); }
  save(): void {
    this.api.post('/crm/activities', this.form).subscribe({
      next: () => { this.showModal = false; this.form = { type: 'call', subject: '', description: '' }; this.notify.show({ type: 'success', title: 'Listo', message: 'Actividad creada' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
  complete(a: any): void {
    this.api.patch(`/crm/activities/${a.id}`, { completed: true }).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Completada', message: a.subject }); this.load(); },
    });
  }
  typeIcon(t: string): string { return { call: '📞', meeting: '🤝', email: '📧', task: '✅', note: '📝' }[t] || '📋'; }
  typeLabel(t: string): string { return { call: 'Llamada', meeting: 'Reunión', email: 'Email', task: 'Tarea', note: 'Nota' }[t] || t; }
}
