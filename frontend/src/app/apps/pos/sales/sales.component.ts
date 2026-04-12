import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pos-sales',
  imports: [CommonModule],
  template: `
    <div>
      <div class="mb-6"><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Historial de Ventas</h2></div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">#</th><th class="px-4 py-3 font-medium text-gray-500">Fecha</th><th class="px-4 py-3 font-medium text-gray-500">Subtotal</th><th class="px-4 py-3 font-medium text-gray-500">Descuento</th><th class="px-4 py-3 font-medium text-gray-500">Total</th><th class="px-4 py-3 font-medium text-gray-500">Metodo</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th><th class="px-4 py-3"></th></tr></thead>
        <tbody>@for (s of sales(); track s.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50">
            <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ s.sale_number }}</td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ s.created_at | date:'short' }}</td>
            <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">$ {{ s.subtotal | number:'1.0-0' }}</td>
            <td class="px-4 py-3 font-mono text-orange-600 dark:text-orange-400">$ {{ s.discount_amount | number:'1.0-0' }}</td>
            <td class="px-4 py-3 font-mono font-bold text-green-600 dark:text-green-400">$ {{ s.total | number:'1.0-0' }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ s.payment_method }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="s.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'">{{ s.status }}</span></td>
            <td class="px-4 py-3">@if (s.status === 'completed') { <button (click)="voidSale(s)" class="px-2 py-1 text-xs rounded-lg border border-red-400 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition">Anular</button> }</td>
          </tr>
        }</tbody></table></div>
        @if (sales().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay ventas</p> }
      </div>
    </div>
  `,
})
export class PosSalesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  sales = signal<any[]>([]);
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/pos/sales').subscribe({ next: (r) => this.sales.set(r) }); }
  voidSale(s: any): void {
    this.api.post(`/pos/sales/${s.id}/void`, {}).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Anulada', message: `${s.sale_number} anulada` }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo anular' }),
    });
  }
}
