import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-loan-detail',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      @if (loan()) {
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">{{ loan()!.loan_number }}</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Capital: $ {{ loan()!.principal | number:'1.0-0' }} · Tasa: {{ loan()!.interest_rate }}% · {{ loan()!.total_installments }} cuotas
            </p>
          </div>
          <a routerLink="/credit/loans" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Volver</a>
        </div>

        <!-- Balances -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p class="text-xs text-gray-500 dark:text-gray-400">Saldo Capital</p>
            <p class="text-lg font-bold text-blue-600 dark:text-blue-400">$ {{ loan()!.balance_principal | number:'1.0-0' }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p class="text-xs text-gray-500 dark:text-gray-400">Interés Pendiente</p>
            <p class="text-lg font-bold text-orange-600 dark:text-orange-400">$ {{ loan()!.balance_interest | number:'1.0-0' }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p class="text-xs text-gray-500 dark:text-gray-400">Total Pagado</p>
            <p class="text-lg font-bold text-green-600 dark:text-green-400">$ {{ loan()!.total_paid | number:'1.0-0' }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p class="text-xs text-gray-500 dark:text-gray-400">Estado</p>
            <p class="text-lg font-bold text-gray-800 dark:text-white/90">{{ statusLabel(loan()!.status) }}</p>
          </div>
        </div>

        <!-- Amortization Table -->
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Tabla de Amortización</h3>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">#</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Fecha</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Capital</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Interés</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Cuota</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Saldo</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Pagado</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Estado</th>
              </tr></thead>
              <tbody>
                @for (a of amortization(); track a.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50" [class.bg-green-50]="a.status === 'paid'" [class.dark:bg-green-900/10]="a.status === 'paid'">
                    <td class="px-3 py-2 text-gray-500">{{ a.installment_number }}</td>
                    <td class="px-3 py-2 text-gray-600 dark:text-gray-400">{{ a.due_date }}</td>
                    <td class="px-3 py-2 font-mono text-gray-800 dark:text-white/90">$ {{ a.principal_amount | number:'1.2-2' }}</td>
                    <td class="px-3 py-2 font-mono text-gray-600 dark:text-gray-400">$ {{ a.interest_amount | number:'1.2-2' }}</td>
                    <td class="px-3 py-2 font-mono font-bold text-gray-800 dark:text-white/90">$ {{ a.total_amount | number:'1.2-2' }}</td>
                    <td class="px-3 py-2 font-mono text-gray-600 dark:text-gray-400">$ {{ a.balance_after | number:'1.2-2' }}</td>
                    <td class="px-3 py-2 font-mono text-gray-600 dark:text-gray-400">$ {{ a.paid_amount | number:'1.2-2' }}</td>
                    <td class="px-3 py-2"><span class="px-2 py-0.5 text-xs rounded-full" [class]="installmentClass(a.status)">{{ installmentLabel(a.status) }}</span></td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>

        <!-- Payments -->
        @if (payments().length > 0) {
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Historial de Pagos</h3>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div class="overflow-x-auto custom-scrollbar">
              <table class="w-full text-sm">
                <thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Fecha</th>
                  <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Monto</th>
                  <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Capital</th>
                  <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Interés</th>
                  <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Método</th>
                </tr></thead>
                <tbody>
                  @for (p of payments(); track p.id) {
                    <tr class="border-b border-gray-100 dark:border-gray-700/50">
                      <td class="px-3 py-2 text-gray-600 dark:text-gray-400">{{ p.payment_date }}</td>
                      <td class="px-3 py-2 font-mono font-bold text-green-600 dark:text-green-400">$ {{ p.amount | number:'1.2-2' }}</td>
                      <td class="px-3 py-2 font-mono text-gray-600 dark:text-gray-400">$ {{ p.principal_applied | number:'1.2-2' }}</td>
                      <td class="px-3 py-2 font-mono text-gray-600 dark:text-gray-400">$ {{ p.interest_applied | number:'1.2-2' }}</td>
                      <td class="px-3 py-2 text-gray-600 dark:text-gray-400">{{ p.method }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>
        }
      }
    </div>
  `,
})
export class LoanDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  loan = signal<any>(null);
  amortization = signal<any[]>([]);
  payments = signal<any[]>([]);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') || '';
    this.api.get<any>(`/credit/loans/${id}`).subscribe({ next: (r) => this.loan.set(r) });
    this.api.get<any[]>(`/credit/loans/${id}/amortization`).subscribe({ next: (r) => this.amortization.set(r) });
    this.api.get<any[]>(`/credit/payments/loan/${id}`).subscribe({ next: (r) => this.payments.set(r) });
  }

  statusLabel(s: string): string { return { pending: 'Pendiente', active: 'Activo', current: 'Al día', delinquent: 'En mora', paid_off: 'Pagado', written_off: 'Castigado', restructured: 'Reestructurado' }[s] || s; }
  installmentLabel(s: string): string { return { pending: 'Pendiente', partial: 'Parcial', paid: 'Pagada', overdue: 'Vencida' }[s] || s; }
  installmentClass(s: string): string {
    return { pending: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400', paid: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', partial: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', overdue: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' }[s] || '';
  }
}
