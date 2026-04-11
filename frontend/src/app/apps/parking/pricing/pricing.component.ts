import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-parking-pricing',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Tarifas</h2><p class="text-sm text-gray-500 dark:text-gray-400">Reglas de precio configurables</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Tarifa</button>
      </div>
      <div class="grid gap-4">
        @for (r of rules(); track r.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ r.name }}</h4>
              @if (r.is_default) { <span class="px-2 py-1 text-xs font-medium rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">Predeterminada</span> }
            </div>
            <div class="flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
              <span>Tipo: {{ r.vehicle_type }}</span>
              <span>Modelo: {{ modelLabel(r.pricing_model) }}</span>
              <span>Tarifa: $ {{ r.base_rate | number:'1.0-0' }}</span>
              <span>Mín: $ {{ r.min_charge | number:'1.0-0' }}</span>
              @if (r.max_daily) { <span>Máx diario: $ {{ r.max_daily | number:'1.0-0' }}</span> }
              <span>Gracia: {{ r.grace_minutes }} min</span>
            </div>
          </div>
        }
        @if (rules().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay tarifas configuradas</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Tarifa</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Vehículo</label><select [(ngModel)]="form.vehicle_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="car">Carro</option><option value="motorcycle">Moto</option><option value="truck">Camión</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Modelo</label><select [(ngModel)]="form.pricing_model" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="per_minute">Por minuto</option><option value="per_hour">Por hora</option><option value="flat_rate">Tarifa plana</option><option value="daily">Diario</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tarifa base</label><input type="number" [(ngModel)]="form.base_rate" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mín cobro</label><input type="number" [(ngModel)]="form.min_charge" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Máx diario</label><input type="number" [(ngModel)]="form.max_daily" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Gracia (min)</label><input type="number" [(ngModel)]="form.grace_minutes" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"><input type="checkbox" [(ngModel)]="form.is_default" class="rounded border-gray-300" /> Predeterminada</label>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ParkingPricingComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  rules = signal<any[]>([]); showModal = false;
  form: any = { name: '', vehicle_type: 'car', pricing_model: 'per_minute', base_rate: 100, min_charge: 3000, max_daily: null, grace_minutes: 15, is_default: false };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/parking/pricing/rules').subscribe({ next: (r) => this.rules.set(r) }); }
  save(): void { this.api.post('/parking/pricing/rules', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Tarifa creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
  modelLabel(m: string): string { return { per_minute: 'Por minuto', per_hour: 'Por hora', flat_rate: 'Tarifa plana', daily: 'Diario', dynamic: 'Dinámico' }[m] || m; }
}
