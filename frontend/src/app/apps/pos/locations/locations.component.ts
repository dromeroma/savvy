import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pos-locations',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Sucursales</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Sucursal</button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        @for (l of locations(); track l.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ l.name }}</h4>
            <p class="text-xs text-gray-500 mt-1 font-mono">{{ l.code }}</p>
            @if (l.address) { <p class="text-xs text-gray-500 mt-1">{{ l.address }}</p> }
            @if (l.city) { <p class="text-xs text-gray-500">{{ l.city }}</p> }
          </div>
        }
        @if (locations().length === 0) { <p class="text-sm text-gray-400 col-span-full text-center py-8">No hay sucursales</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Sucursal</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-3 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Codigo</label><input [(ngModel)]="form.code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div class="col-span-2"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Direccion</label><input [(ngModel)]="form.address" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ciudad</label><input [(ngModel)]="form.city" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefono</label><input [(ngModel)]="form.phone" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PosLocationsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  locations = signal<any[]>([]); showModal = false;
  form: any = { code: '', name: '', address: '', city: '', phone: '' };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/pos/locations').subscribe({ next: (r) => this.locations.set(r) }); }
  save(): void { this.api.post('/pos/locations', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Sucursal creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
