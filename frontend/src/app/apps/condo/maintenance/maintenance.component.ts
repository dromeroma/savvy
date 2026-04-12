import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-condo-maintenance',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Mantenimiento / PQR</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Solicitud</button>
      </div>
      <div class="space-y-3">
        @for (m of requests(); track m.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-medium text-gray-800 dark:text-white/90">{{ m.title }}</h4>
                <div class="flex gap-3 text-xs text-gray-500 mt-1">
                  <span>{{ m.category }}</span>
                  <span class="px-1.5 py-0.5 rounded" [class]="m.priority === 'urgent' ? 'bg-red-100 text-red-700' : m.priority === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'">{{ m.priority }}</span>
                  @if (m.assigned_to) { <span>Asignado: {{ m.assigned_to }}</span> }
                </div>
              </div>
              <span class="px-2 py-1 text-xs rounded-full" [class]="m.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : m.status === 'in_progress' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'">{{ statusLabel(m.status) }}</span>
            </div>
          </div>
        }
        @if (requests().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay solicitudes</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Solicitud</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Titulo</label><input [(ngModel)]="form.title" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripcion</label><textarea [(ngModel)]="form.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label><select [(ngModel)]="form.category" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="plumbing">Plomeria</option><option value="electrical">Electrico</option><option value="structural">Estructural</option><option value="elevator">Ascensor</option><option value="cleaning">Aseo</option><option value="security">Seguridad</option><option value="general">General</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Prioridad</label><select [(ngModel)]="form.priority" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="low">Baja</option><option value="medium">Media</option><option value="high">Alta</option><option value="urgent">Urgente</option></select></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Propiedad</label><select [(ngModel)]="form.property_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (p of properties(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }</select></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Crear</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CondoMaintenanceComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  requests = signal<any[]>([]); properties = signal<any[]>([]); showModal = false;
  form: any = { title: '', description: '', category: 'general', priority: 'medium', property_id: '' };
  ngOnInit(): void { this.load(); this.api.get<any[]>('/condo/properties').subscribe({ next: (r) => this.properties.set(r) }); }
  load(): void { this.api.get<any[]>('/condo/maintenance').subscribe({ next: (r) => this.requests.set(r) }); }
  save(): void { this.api.post('/condo/maintenance', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Solicitud creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
  statusLabel(s: string): string { return { open: 'Abierta', in_progress: 'En progreso', completed: 'Completada', cancelled: 'Cancelada' }[s] || s; }
}
