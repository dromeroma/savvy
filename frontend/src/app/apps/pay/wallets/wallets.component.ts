import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pay-wallets',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Wallets</h2><p class="text-sm text-gray-500 dark:text-gray-400">Cuentas financieras con saldos derivados del ledger</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Wallet</button>
      </div>
      <div class="grid gap-4">
        @for (w of wallets(); track w.wallet.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between mb-3">
              <div><h4 class="font-semibold text-gray-800 dark:text-white/90">{{ w.wallet.wallet_type | uppercase }} Wallet</h4><p class="text-xs text-gray-500 dark:text-gray-400">{{ w.wallet.currency }} · {{ w.wallet.id | slice:0:8 }}</p></div>
              <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">{{ w.wallet.status }}</span>
            </div>
            <div class="grid grid-cols-4 gap-4 text-center">
              <div><p class="text-xs text-gray-500">Disponible</p><p class="text-lg font-bold text-green-600 dark:text-green-400">$ {{ w.balance.available | number:'1.0-0' }}</p></div>
              <div><p class="text-xs text-gray-500">Pendiente</p><p class="text-lg font-bold text-yellow-600 dark:text-yellow-400">$ {{ w.balance.pending | number:'1.0-0' }}</p></div>
              <div><p class="text-xs text-gray-500">Reservado</p><p class="text-lg font-bold text-blue-600 dark:text-blue-400">$ {{ w.balance.reserved | number:'1.0-0' }}</p></div>
              <div><p class="text-xs text-gray-500">Total</p><p class="text-lg font-bold text-gray-800 dark:text-white/90">$ {{ w.balance.total | number:'1.0-0' }}</p></div>
            </div>
          </div>
        }
        @if (wallets().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay wallets</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Wallet</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.wallet_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="user">Usuario</option><option value="merchant">Comercio</option><option value="platform">Plataforma</option></select></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Crear</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PayWalletsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  wallets = signal<any[]>([]); showModal = false;
  form: any = { wallet_type: 'user' };
  ngOnInit(): void { this.load(); }
  load(): void {
    this.api.get<any[]>('/pay/wallets').subscribe({ next: async (ws) => {
      const results: any[] = [];
      for (const w of ws) {
        this.api.get<any>(`/pay/wallets/${w.id}/balance`).subscribe({
          next: (b) => { results.push({ wallet: w, balance: b }); this.wallets.set([...results]); }
        });
      }
      if (ws.length === 0) this.wallets.set([]);
    }});
  }
  save(): void { this.api.post('/pay/wallets', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Wallet creado con 3 cuentas ledger' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
