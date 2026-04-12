import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-condo-areas',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Areas Comunes</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Area</button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        @for (a of areas(); track a.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ a.name }}</h4>
            <div class="flex gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>{{ typeLabel(a.area_type) }}</span>
              @if (a.capacity) { <span>Cap: {{ a.capacity }}</span> }
              @if (a.reservation_fee > 0) { <span>$ {{ a.reservation_fee | number:'1.0-0' }}</span> }
              <span>{{ a.requires_reservation ? 'Reservable' : 'Libre' }}</span>
            </div>
          </div>
        }
        @if (areas().length === 0) { <p class="text-sm text-gray-400 col-span-full text-center py-8">No hay areas comunes</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Area Comun</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.area_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="social">Social</option><option value="gym">Gimnasio</option><option value="pool">Piscina</option><option value="bbq">BBQ</option><option value="meeting_room">Salon</option><option value="playground">Parque</option><option value="terrace">Terraza</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidad</label><input type="number" [(ngModel)]="form.capacity" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Propiedad</label><select [(ngModel)]="form.property_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (p of properties(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }</select></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CondoAreasComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  areas = signal<any[]>([]); properties = signal<any[]>([]); showModal = false;
  form: any = { name: '', area_type: 'social', capacity: null, property_id: '' };
  ngOnInit(): void { this.load(); this.api.get<any[]>('/condo/properties').subscribe({ next: (r) => this.properties.set(r) }); }
  load(): void { this.api.get<any[]>('/condo/areas').subscribe({ next: (r) => this.areas.set(r) }); }
  save(): void { this.api.post('/condo/areas', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Area creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
  typeLabel(t: string): string { return { social: 'Social', gym: 'Gimnasio', pool: 'Piscina', bbq: 'BBQ', meeting_room: 'Salon', playground: 'Parque', terrace: 'Terraza', other: 'Otro' }[t] || t; }
}
