import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-payments',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Registrar Pago</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Recibir pagos de préstamos</p>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 max-w-lg">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Préstamo</label>
            <select [(ngModel)]="form.loan_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
              <option value="">-- Seleccionar préstamo --</option>
              @for (l of activeLoans(); track l.id) {
                <option [value]="l.id">{{ l.loan_number }} · Saldo: $ {{ l.balance_principal | number:'1.0-0' }}</option>
              }
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Monto</label>
            <input type="number" [(ngModel)]="form.amount" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Método</label>
            <select [(ngModel)]="form.method" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
              <option value="cash">Efectivo</option>
              <option value="bank_transfer">Transferencia</option>
              <option value="mobile_payment">Pago móvil</option>
              <option value="check">Cheque</option>
            </select>
          </div>
          <button (click)="pay()" [disabled]="!form.loan_id || !form.amount"
            class="w-full px-4 py-2.5 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition disabled:opacity-50">
            Registrar Pago
          </button>
        </div>

        @if (lastPayment()) {
          <div class="mt-6 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
            <p class="text-sm font-medium text-green-800 dark:text-green-300">Pago registrado</p>
            <div class="text-xs text-green-600 dark:text-green-400 mt-1 space-y-1">
              <p>Capital aplicado: $ {{ lastPayment()!.principal_applied | number:'1.2-2' }}</p>
              <p>Interés aplicado: $ {{ lastPayment()!.interest_applied | number:'1.2-2' }}</p>
              @if (lastPayment()!.penalty_applied > 0) {
                <p>Penalidad aplicada: $ {{ lastPayment()!.penalty_applied | number:'1.2-2' }}</p>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `,
})
export class PaymentsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  activeLoans = signal<any[]>([]);
  lastPayment = signal<any>(null);
  form: any = { loan_id: '', amount: 0, method: 'cash' };

  ngOnInit(): void {
    this.api.get<any[]>('/credit/loans', { status: 'active' }).subscribe({
      next: (r) => {
        const all = r || [];
        this.activeLoans.set(all.filter((l: any) => ['active', 'current', 'delinquent'].includes(l.status)));
      },
    });
  }

  pay(): void {
    this.api.post('/credit/payments', this.form).subscribe({
      next: (r: any) => {
        this.lastPayment.set(r);
        this.notify.show({ type: 'success', title: 'Pago registrado', message: `$ ${r.amount} aplicado correctamente` });
        this.form.amount = 0;
        // Refresh loans
        this.api.get<any[]>('/credit/loans').subscribe({
          next: (loans) => this.activeLoans.set((loans || []).filter((l: any) => ['active', 'current', 'delinquent'].includes(l.status))),
        });
      },
      error: (e: any) => this.notify.show({ type: 'error', title: 'Error', message: e?.error?.detail || 'No se pudo registrar el pago' }),
    });
  }
}
