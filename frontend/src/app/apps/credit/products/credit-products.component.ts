import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-credit-products',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Productos de Crédito</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Plantillas configurables de préstamos</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Producto</button>
      </div>
      <div class="grid gap-4">
        @for (p of products(); track p.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between mb-2">
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-mono text-xs text-gray-500 dark:text-gray-400">{{ p.code }}</span>
                  <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ p.name }}</h4>
                </div>
                @if (p.description) { <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ p.description }}</p> }
              </div>
              <span class="px-2 py-1 text-xs rounded-full" [class]="p.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'">{{ p.status }}</span>
            </div>
            <div class="flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
              <span>Tasa: {{ p.interest_rate }}% {{ p.interest_rate_period }}</span>
              <span>Método: {{ methodLabel(p.amortization_method) }}</span>
              <span>Frecuencia: {{ freqLabel(p.payment_frequency) }}</span>
              <span>Plazo: {{ p.term_min }}-{{ p.term_max }} cuotas</span>
              <span>Monto: {{ p.amount_min | number:'1.0-0' }} - {{ p.amount_max | number:'1.0-0' }}</span>
              @if (p.grace_period_days > 0) { <span>Gracia: {{ p.grace_period_days }}d</span> }
              @if (p.late_fee_type !== 'none') { <span>Mora: {{ p.late_fee_value }}{{ p.late_fee_type === 'percentage' ? '%' : '' }}</span> }
            </div>
          </div>
        }
        @if (products().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay productos configurados</p> }
      </div>

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Producto de Crédito</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código</label><input [(ngModel)]="form.code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div class="col-span-2"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo Interés</label><select [(ngModel)]="form.interest_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="declining_balance">Saldo decreciente</option><option value="flat">Fijo sobre capital</option><option value="fixed">Tasa fija</option><option value="compound">Compuesto</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tasa (%)</label><input type="number" [(ngModel)]="form.interest_rate" step="0.01" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Periodo tasa</label><select [(ngModel)]="form.interest_rate_period" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="monthly">Mensual</option><option value="annual">Anual</option></select></div>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Amortización</label><select [(ngModel)]="form.amortization_method" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="french">Francés (cuota fija)</option><option value="german">Alemán (amort. const.)</option><option value="flat">Flat</option><option value="bullet">Bullet</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Frecuencia</label><select [(ngModel)]="form.payment_frequency" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="weekly">Semanal</option><option value="biweekly">Quincenal</option><option value="monthly">Mensual</option><option value="quarterly">Trimestral</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Gracia (días)</label><input type="number" [(ngModel)]="form.grace_period_days" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div class="grid grid-cols-4 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Plazo mín</label><input type="number" [(ngModel)]="form.term_min" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Plazo máx</label><input type="number" [(ngModel)]="form.term_max" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Monto mín</label><input type="number" [(ngModel)]="form.amount_min" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Monto máx</label><input type="number" [(ngModel)]="form.amount_max" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
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
export class CreditProductsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  products = signal<any[]>([]);
  showModal = false;
  form: any = { code: '', name: '', interest_type: 'declining_balance', interest_rate: 2, interest_rate_period: 'monthly', amortization_method: 'french', payment_frequency: 'monthly', grace_period_days: 0, term_min: 1, term_max: 24, amount_min: 100000, amount_max: 50000000 };

  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/credit/products').subscribe({ next: (r) => this.products.set(r) }); }
  save(): void {
    this.api.post('/credit/products', this.form).subscribe({
      next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Producto creado' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
  methodLabel(m: string): string { return { french: 'Francés', german: 'Alemán', flat: 'Flat', bullet: 'Bullet' }[m] || m; }
  freqLabel(f: string): string { return { weekly: 'Semanal', biweekly: 'Quincenal', monthly: 'Mensual', quarterly: 'Trimestral' }[f] || f; }
}
