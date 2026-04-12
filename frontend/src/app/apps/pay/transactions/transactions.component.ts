import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pay-transactions',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Transacciones</h2><p class="text-sm text-gray-500 dark:text-gray-400">Pagos, transferencias y reembolsos</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Transaccion</button>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Fecha</th><th class="px-4 py-3 font-medium text-gray-500">Tipo</th><th class="px-4 py-3 font-medium text-gray-500">Monto</th><th class="px-4 py-3 font-medium text-gray-500">Fee</th><th class="px-4 py-3 font-medium text-gray-500">Metodo</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th><th class="px-4 py-3 font-medium text-gray-500">App</th></tr></thead>
        <tbody>@for (tx of transactions(); track tx.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50">
            <td class="px-4 py-3 text-xs text-gray-500">{{ tx.created_at | date:'short' }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ tx.transaction_type }}</td>
            <td class="px-4 py-3 font-mono font-bold text-gray-800 dark:text-white/90">$ {{ tx.amount | number:'1.0-0' }}</td>
            <td class="px-4 py-3 font-mono text-gray-500">$ {{ tx.fee_amount | number:'1.0-0' }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ tx.payment_method || '-' }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="statusClass(tx.status)">{{ tx.status }}</span></td>
            <td class="px-4 py-3 text-xs text-gray-400">{{ tx.source_app || '-' }}</td>
          </tr>
        }</tbody></table></div>
        @if (transactions().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay transacciones</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Transaccion</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Monto</label><input type="number" [(ngModel)]="form.amount" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.transaction_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="payment">Pago</option><option value="transfer">Transferencia</option></select></div></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Metodo</label><select [(ngModel)]="form.payment_method" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="cash">Efectivo</option><option value="card">Tarjeta</option><option value="bank_transfer">Transferencia</option><option value="wallet">Wallet</option><option value="mobile_payment">Pago movil</option></select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripcion</label><input [(ngModel)]="form.description" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Crear</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PayTransactionsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  transactions = signal<any[]>([]); showModal = false;
  form: any = { amount: 0, transaction_type: 'payment', payment_method: 'cash', description: '' };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/pay/transactions').subscribe({ next: (r) => this.transactions.set(r) }); }
  save(): void { this.api.post('/pay/transactions', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Transaccion creada' }); this.load(); }, error: (e: any) => this.notify.show({ type: 'error', title: 'Error', message: e?.error?.detail || 'No se pudo crear' }) }); }
  statusClass(s: string): string { return { pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', authorized: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', captured: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', settled: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400', failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', refunded: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' }[s] || 'bg-gray-100 text-gray-600'; }
}
