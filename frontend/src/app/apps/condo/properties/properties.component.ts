import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-condo-properties',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Propiedades</h2><p class="text-sm text-gray-500 dark:text-gray-400">Edificios y conjuntos</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Propiedad</button>
      </div>
      <div class="grid gap-4">
        @for (p of properties(); track p.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between">
              <div>
                <div class="flex items-center gap-2"><span class="font-mono text-xs text-gray-500">{{ p.code }}</span><h4 class="font-semibold text-gray-800 dark:text-white/90">{{ p.name }}</h4></div>
                <div class="flex gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
                  <span>{{ p.property_type }}</span><span>{{ p.total_units }} unidades</span>
                  <span>Cuota base: $ {{ p.admin_fee_base | number:'1.0-0' }}</span>
                  @if (p.city) { <span>{{ p.city }}</span> }
                </div>
              </div>
              <span class="px-2 py-1 text-xs rounded-full" [class]="p.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600'">{{ p.status }}</span>
            </div>
          </div>
        }
        @if (properties().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay propiedades</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Propiedad</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Codigo</label><input [(ngModel)]="form.code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div class="col-span-2"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.property_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="residential">Residencial</option><option value="commercial">Comercial</option><option value="mixed">Mixto</option><option value="office">Oficinas</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unidades</label><input type="number" [(ngModel)]="form.total_units" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cuota base</label><input type="number" [(ngModel)]="form.admin_fee_base" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Direccion</label><input [(ngModel)]="form.address" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CondoPropertiesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  properties = signal<any[]>([]); showModal = false;
  form: any = { code: '', name: '', property_type: 'residential', total_units: 0, admin_fee_base: 200000, address: '' };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/condo/properties').subscribe({ next: (r) => this.properties.set(r) }); }
  save(): void { this.api.post('/condo/properties', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Propiedad creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
