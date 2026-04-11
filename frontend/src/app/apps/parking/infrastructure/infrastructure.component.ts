import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-infrastructure',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Infraestructura</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Sedes, zonas y espacios</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Sede</button>
      </div>
      <div class="grid gap-4">
        @for (loc of locations(); track loc.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between mb-2">
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ loc.code }}</span>
                  <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ loc.name }}</h4>
                </div>
                @if (loc.address) { <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ loc.address }}</p> }
              </div>
              <div class="text-right">
                <p class="text-lg font-bold text-blue-600 dark:text-blue-400">{{ loc.current_occupancy }} / {{ loc.total_capacity }}</p>
                <p class="text-xs text-gray-400">ocupados</p>
              </div>
            </div>
            <!-- Occupancy bar -->
            <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all" [style.width.%]="loc.total_capacity > 0 ? (loc.current_occupancy / loc.total_capacity) * 100 : 0"
                [class]="loc.current_occupancy / loc.total_capacity > 0.8 ? 'bg-red-500' : 'bg-brand-500'"></div>
            </div>
          </div>
        }
        @if (locations().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay sedes configuradas</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Sede</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código</label><input [(ngModel)]="form.code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div class="col-span-2"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dirección</label><input [(ngModel)]="form.address" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ciudad</label><input [(ngModel)]="form.city" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidad total</label><input type="number" [(ngModel)]="form.total_capacity" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
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
export class InfrastructureComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  locations = signal<any[]>([]);
  showModal = false;
  form: any = { code: '', name: '', address: '', city: '', total_capacity: 50 };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/parking/locations').subscribe({ next: (r) => this.locations.set(r) }); }
  save(): void {
    this.api.post('/parking/locations', this.form).subscribe({
      next: () => { this.showModal = false; this.form = { code: '', name: '', address: '', city: '', total_capacity: 50 }; this.notify.show({ type: 'success', title: 'Listo', message: 'Sede creada' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
}
