import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-pay-payouts',
  imports: [CommonModule],
  template: `
    <div>
      <div class="mb-6"><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Payouts</h2><p class="text-sm text-gray-500 dark:text-gray-400">Retiros y transferencias a comercios</p></div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Fecha</th><th class="px-4 py-3 font-medium text-gray-500">Monto</th><th class="px-4 py-3 font-medium text-gray-500">Fee</th><th class="px-4 py-3 font-medium text-gray-500">Neto</th><th class="px-4 py-3 font-medium text-gray-500">Metodo</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th></tr></thead>
        <tbody>@for (p of payouts(); track p.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50"><td class="px-4 py-3 text-xs text-gray-500">{{ p.created_at | date:'short' }}</td><td class="px-4 py-3 font-mono text-gray-800 dark:text-white/90">$ {{ p.amount | number:'1.0-0' }}</td><td class="px-4 py-3 font-mono text-gray-500">$ {{ p.fee | number:'1.0-0' }}</td><td class="px-4 py-3 font-mono font-bold text-green-600 dark:text-green-400">$ {{ p.net_amount | number:'1.0-0' }}</td><td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ p.method }}</td><td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="p.status === 'executed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'">{{ p.status }}</span></td></tr>
        }</tbody></table></div>
        @if (payouts().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay payouts</p> }
      </div>
    </div>
  `,
})
export class PayPayoutsComponent implements OnInit {
  private readonly api = inject(ApiService);
  payouts = signal<any[]>([]);
  ngOnInit(): void { this.api.get<any[]>('/pay/payouts').subscribe({ next: (r) => this.payouts.set(r) }); }
}
