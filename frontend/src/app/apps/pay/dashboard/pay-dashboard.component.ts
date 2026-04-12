import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-pay-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6"><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyPay</h2><p class="text-sm text-gray-500 dark:text-gray-400">Infraestructura financiera del ecosistema</p></div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Volumen Transacciones</p><p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">$ {{ kpis().transaction_volume | number:'1.0-0' }}</p><p class="text-xs text-gray-400 mt-1">{{ kpis().total_transactions }} transacciones</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Fees Recaudados</p><p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">$ {{ kpis().total_fees_collected | number:'1.0-0' }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Wallets</p><p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ kpis().total_wallets }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Payouts</p><p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">$ {{ kpis().payout_volume | number:'1.0-0' }}</p><p class="text-xs text-gray-400 mt-1">{{ kpis().total_payouts }} payouts</p></div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Capturadas</p><p class="text-2xl font-bold text-teal-600 dark:text-teal-400 mt-1">{{ kpis().captured_transactions }}</p></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"><p class="text-sm text-gray-500">Liquidadas</p><p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{{ kpis().settled_transactions }}</p></div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones</h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          @for (a of actions; track a.label) { <a [routerLink]="a.route" class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center"><span class="text-2xl">{{ a.icon }}</span><span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ a.label }}</span></a> }
        </div>
      </div>
    </div>
  `,
})
export class PayDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  kpis = signal<any>({ transaction_volume: 0, total_transactions: 0, total_fees_collected: 0, total_wallets: 0, total_payouts: 0, payout_volume: 0, captured_transactions: 0, settled_transactions: 0 });
  readonly actions = [
    { label: 'Ledger', route: '/pay/ledger', icon: '📒' },
    { label: 'Transacciones', route: '/pay/transactions', icon: '💳' },
    { label: 'Wallets', route: '/pay/wallets', icon: '👛' },
    { label: 'Fees', route: '/pay/fees', icon: '💰' },
    { label: 'Payouts', route: '/pay/payouts', icon: '🏦' },
    { label: 'Suscripciones', route: '/pay/subscriptions', icon: '🔄' },
  ];
  ngOnInit(): void { this.api.get<any>('/pay/dashboard/kpis').subscribe({ next: (r) => this.kpis.set(r) }); }
}
