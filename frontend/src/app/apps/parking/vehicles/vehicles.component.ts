import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-parking-vehicles',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Vehículos</h2><p class="text-sm text-gray-500 dark:text-gray-400">Registro de vehículos</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Vehículo</button>
      </div>
      <div class="mb-4"><input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar placa..." class="w-full sm:w-60 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Placa</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Tipo</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Marca</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Color</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th></tr></thead>
          <tbody>@for (v of vehicles(); track v.id) {
            <tr class="border-b border-gray-100 dark:border-gray-700/50"><td class="px-4 py-3 font-mono font-bold text-gray-800 dark:text-white/90">{{ v.plate }}</td><td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ v.vehicle_type }}</td><td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ v.brand || '-' }}</td><td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ v.color || '-' }}</td><td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="v.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'">{{ v.status }}</span></td></tr>
          }</tbody></table>
        </div>
        @if (vehicles().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay vehículos</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Vehículo</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Placa</label><input [(ngModel)]="form.plate" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm uppercase" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.vehicle_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="car">Carro</option><option value="motorcycle">Moto</option><option value="truck">Camión</option><option value="electric">Eléctrico</option><option value="bicycle">Bicicleta</option></select></div></div>
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Marca</label><input [(ngModel)]="form.brand" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Color</label><input [(ngModel)]="form.color" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ParkingVehiclesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  vehicles = signal<any[]>([]); showModal = false; search = '';
  form: any = { plate: '', vehicle_type: 'car', brand: '', color: '' };
  ngOnInit(): void { this.load(); }
  load(): void { const p: any = {}; if (this.search) p.search = this.search; this.api.get<any[]>('/parking/vehicles', p).subscribe({ next: (r) => this.vehicles.set(r) }); }
  save(): void { this.api.post('/parking/vehicles', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Vehículo registrado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo registrar' }) }); }
}
