import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-condo-announcements',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Comunicados</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Comunicado</button>
      </div>
      <div class="space-y-3">
        @for (a of announcements(); track a.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 text-xs rounded-full" [class]="a.priority === 'urgent' ? 'bg-red-100 text-red-700' : a.priority === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'">{{ a.category }}</span>
                <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ a.title }}</h4>
              </div>
              <span class="text-xs text-gray-400">{{ a.created_at | date:'short' }}</span>
            </div>
            @if (a.body) { <p class="text-sm text-gray-600 dark:text-gray-400">{{ a.body }}</p> }
          </div>
        }
        @if (announcements().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay comunicados</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Comunicado</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Titulo</label><input [(ngModel)]="form.title" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Contenido</label><textarea [(ngModel)]="form.body" rows="3" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label><select [(ngModel)]="form.category" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="general">General</option><option value="maintenance">Mantenimiento</option><option value="financial">Financiero</option><option value="event">Evento</option><option value="security">Seguridad</option><option value="emergency">Emergencia</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Prioridad</label><select [(ngModel)]="form.priority" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="low">Baja</option><option value="normal">Normal</option><option value="high">Alta</option><option value="urgent">Urgente</option></select></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Propiedad</label><select [(ngModel)]="form.property_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (p of properties(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }</select></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Publicar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CondoAnnouncementsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  announcements = signal<any[]>([]); properties = signal<any[]>([]); showModal = false;
  form: any = { title: '', body: '', category: 'general', priority: 'normal', property_id: '' };
  ngOnInit(): void { this.load(); this.api.get<any[]>('/condo/properties').subscribe({ next: (r) => this.properties.set(r) }); }
  load(): void { this.api.get<any[]>('/condo/announcements').subscribe({ next: (r) => this.announcements.set(r) }); }
  save(): void { this.api.post('/condo/announcements', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Publicado', message: 'Comunicado publicado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo publicar' }) }); }
}
