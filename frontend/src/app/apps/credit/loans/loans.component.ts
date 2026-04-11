import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-loans',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Préstamos</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Préstamos activos y su estado</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Préstamo</button>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-sm">
            <thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left">
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">N.</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Capital</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Tasa</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Cuotas</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Saldo</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Próx. Pago</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
              <th class="px-4 py-3"></th>
            </tr></thead>
            <tbody>
              @for (l of loans(); track l.id) {
                <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/5 transition cursor-pointer" (click)="openLoan(l.id)">
                  <td class="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">{{ l.loan_number }}</td>
                  <td class="px-4 py-3 font-mono text-gray-800 dark:text-white/90">$ {{ l.principal | number:'1.0-0' }}</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ l.interest_rate }}%</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ l.total_installments }}</td>
                  <td class="px-4 py-3 font-mono text-gray-800 dark:text-white/90">$ {{ l.balance_principal | number:'1.0-0' }}</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ l.next_payment_date || '-' }}</td>
                  <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="loanStatusClass(l.status)">{{ loanStatusLabel(l.status) }}</span></td>
                  <td class="px-4 py-3">
                    @if (l.status === 'pending') {
                      <button (click)="disburse(l, $event)" class="px-3 py-1 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition">Desembolsar</button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        @if (loans().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay préstamos</p> }
      </div>

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Préstamo</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Prestatario</label><select [(ngModel)]="loanForm.borrower_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">--</option>@for (b of borrowers(); track b.id) { <option [value]="b.id">{{ b.first_name }} {{ b.last_name }}</option> }</select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Producto</label><select [(ngModel)]="loanForm.product_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">--</option>@for (p of products(); track p.id) { <option [value]="p.id">{{ p.code }} - {{ p.name }}</option> }</select></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capital</label><input type="number" [(ngModel)]="loanForm.principal" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cuotas</label><input type="number" [(ngModel)]="loanForm.term" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="createLoan()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Crear</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class LoansComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  private readonly router = inject(Router);
  loans = signal<any[]>([]);
  borrowers = signal<any[]>([]);
  products = signal<any[]>([]);
  showModal = false;
  loanForm: any = { borrower_id: '', product_id: '', principal: 0, term: 12 };

  ngOnInit(): void {
    this.load();
    this.api.get<any>('/credit/borrowers', { page_size: 500 }).subscribe({ next: (r) => this.borrowers.set(r.items || []) });
    this.api.get<any[]>('/credit/products').subscribe({ next: (r) => this.products.set(r) });
  }
  load(): void { this.api.get<any[]>('/credit/loans').subscribe({ next: (r) => this.loans.set(r) }); }
  createLoan(): void {
    this.api.post('/credit/loans', this.loanForm).subscribe({
      next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Préstamo creado con tabla de amortización' }); this.load(); },
      error: (e: any) => this.notify.show({ type: 'error', title: 'Error', message: e?.error?.detail || 'No se pudo crear' }),
    });
  }
  disburse(l: any, event: Event): void {
    event.stopPropagation();
    this.api.post(`/credit/loans/${l.id}/disburse`, { method: 'cash' }).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Desembolsado', message: `${l.loan_number} desembolsado` }); this.load(); },
    });
  }
  openLoan(id: string): void { this.router.navigate(['/credit/loans', id]); }
  loanStatusLabel(s: string): string { return { pending: 'Pendiente', active: 'Activo', current: 'Al día', delinquent: 'En mora', defaulted: 'Impago', paid_off: 'Pagado', written_off: 'Castigado', restructured: 'Reestructurado' }[s] || s; }
  loanStatusClass(s: string): string {
    return { pending: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400', active: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', current: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', delinquent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', paid_off: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' }[s] || 'bg-gray-100 text-gray-600';
  }
}
