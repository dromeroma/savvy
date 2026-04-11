import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-parking-services',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Servicios Adicionales</h2><p class="text-sm text-gray-500 dark:text-gray-400">Lavado, valet y más</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Servicio</button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        @for (s of serviceTypes(); track s.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ s.name }}</h4>
            <div class="flex gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>{{ catLabel(s.category) }}</span>
              <span class="font-mono font-bold text-green-600 dark:text-green-400">$ {{ s.price | number:'1.0-0' }}</span>
            </div>
          </div>
        }
        @if (serviceTypes().length === 0) { <p class="text-sm text-gray-400 col-span-full text-center py-8">No hay servicios configurados</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Servicio</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoría</label><select [(ngModel)]="form.category" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="wash">Lavado</option><option value="valet">Valet</option><option value="detailing">Detailing</option><option value="tire">Llantas</option><option value="other">Otro</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Precio</label><input type="number" [(ngModel)]="form.price" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ParkingServicesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  serviceTypes = signal<any[]>([]); showModal = false;
  form: any = { name: '', category: 'wash', price: 15000 };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/parking/services/types').subscribe({ next: (r) => this.serviceTypes.set(r) }); }
  save(): void { this.api.post('/parking/services/types', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Servicio creado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
  catLabel(c: string): string { return { wash: 'Lavado', valet: 'Valet', detailing: 'Detailing', tire: 'Llantas', other: 'Otro' }[c] || c; }
}
