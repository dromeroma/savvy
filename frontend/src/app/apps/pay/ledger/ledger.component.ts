import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-pay-ledger',
  imports: [CommonModule],
  template: `
    <div>
      <div class="mb-6"><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Ledger & Cuentas</h2><p class="text-sm text-gray-500 dark:text-gray-400">Doble partida — todos los saldos derivados del ledger</p></div>

      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Saldos por Cuenta</h3>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Codigo</th><th class="px-4 py-3 font-medium text-gray-500">Nombre</th><th class="px-4 py-3 font-medium text-gray-500">Tipo</th><th class="px-4 py-3 font-medium text-gray-500">Moneda</th><th class="px-4 py-3 font-medium text-gray-500 text-right">Saldo</th></tr></thead>
        <tbody>@for (b of balances(); track b.account_id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50"><td class="px-4 py-3 font-mono text-xs text-gray-500">{{ b.code }}</td><td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ b.name }}</td><td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ b.account_type }}</td><td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ b.currency }}</td><td class="px-4 py-3 font-mono text-right" [class]="b.balance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">$ {{ b.balance | number:'1.2-2' }}</td></tr>
        }</tbody></table></div>
        @if (balances().length === 0) { <p class="text-sm text-gray-400 text-center py-6">No hay cuentas</p> }
      </div>

      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Ultimos Movimientos</h3>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Fecha</th><th class="px-4 py-3 font-medium text-gray-500">Journal</th><th class="px-4 py-3 font-medium text-gray-500">Tipo</th><th class="px-4 py-3 font-medium text-gray-500 text-right">Monto</th><th class="px-4 py-3 font-medium text-gray-500">Descripcion</th></tr></thead>
        <tbody>@for (e of entries(); track e.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50"><td class="px-4 py-3 text-xs text-gray-500">{{ e.posted_at | date:'short' }}</td><td class="px-4 py-3 font-mono text-xs text-gray-400">{{ e.journal_id | slice:0:8 }}</td><td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="e.entry_type === 'debit' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'">{{ e.entry_type }}</span></td><td class="px-4 py-3 font-mono text-right text-gray-800 dark:text-white/90">$ {{ e.amount | number:'1.2-2' }}</td><td class="px-4 py-3 text-xs text-gray-500">{{ e.description || '-' }}</td></tr>
        }</tbody></table></div>
        @if (entries().length === 0) { <p class="text-sm text-gray-400 text-center py-6">No hay movimientos</p> }
      </div>
    </div>
  `,
})
export class PayLedgerComponent implements OnInit {
  private readonly api = inject(ApiService);
  balances = signal<any[]>([]); entries = signal<any[]>([]);
  ngOnInit(): void {
    this.api.get<any[]>('/pay/ledger/balances').subscribe({ next: (r) => this.balances.set(r) });
    this.api.get<any[]>('/pay/ledger/entries').subscribe({ next: (r) => this.entries.set(r) });
  }
}
