import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pay-fees',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Reglas de Fees</h2><p class="text-sm text-gray-500 dark:text-gray-400">Comisiones configurables por tipo de transaccion</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Regla</button>
      </div>
      <div class="grid gap-4">
        @for (r of rules(); track r.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between"><h4 class="font-semibold text-gray-800 dark:text-white/90">{{ r.name }}</h4><span class="px-2 py-1 text-xs rounded-full" [class]="r.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600'">{{ r.is_active ? 'Activa' : 'Inactiva' }}</span></div>
            <div class="flex flex-wrap gap-3 text-xs text-gray-500 mt-2"><span>Tipo: {{ r.fee_type }}</span>@if (r.percentage_value > 0) { <span>{{ r.percentage_value }}%</span> }@if (r.fixed_value > 0) { <span>Fijo: $ {{ r.fixed_value | number:'1.0-0' }}</span> }<span>Min: $ {{ r.min_fee | number:'1.0-0' }}</span><span>Aplica a: {{ r.applies_to }}</span></div>
          </div>
        }
        @if (rules().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay reglas configuradas</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Regla de Fee</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-3 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.fee_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="percentage">Porcentaje</option><option value="fixed">Fijo</option><option value="tiered">Escalonado</option></select></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">% Valor</label><input type="number" [(ngModel)]="form.percentage_value" step="0.01" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fijo</label><input type="number" [(ngModel)]="form.fixed_value" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Min Fee</label><input type="number" [(ngModel)]="form.min_fee" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Aplica a</label><select [(ngModel)]="form.applies_to" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="all">Todos</option><option value="payment">Pagos</option><option value="payout">Payouts</option><option value="subscription">Suscripciones</option><option value="transfer">Transferencias</option></select></div></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PayFeesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  rules = signal<any[]>([]); showModal = false;
  form: any = { name: '', fee_type: 'percentage', percentage_value: 2.5, fixed_value: 0, min_fee: 500, applies_to: 'all' };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/pay/fees/rules').subscribe({ next: (r) => this.rules.set(r) }); }
  save(): void { this.api.post('/pay/fees/rules', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Regla creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
