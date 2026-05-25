import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PortalService } from '../../core/services/portal.service';
import { PortalPaymentItem } from '../../core/models/portal.model';

@Component({
  selector: 'app-portal-payments',
  imports: [CommonModule],
  template: `
    <div>
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90 mb-1">Mis pagos</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-5">Historial de pagos registrados.</p>

      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-sky-200 border-t-sky-600"></div>
        </div>
      } @else if (payments().length === 0) {
        <div class="rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-10 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">Aún no tienes pagos registrados.</p>
        </div>
      } @else {
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-700/30">
              <tr class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3">Recibo</th>
                <th class="px-4 py-3">Método</th>
                <th class="px-4 py-3 text-center">Facturas aplicadas</th>
                <th class="px-4 py-3 text-right">Monto</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              @for (p of payments(); track p.id) {
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ p.payment_date }}</td>
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ p.receipt_number || '—' }}</td>
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300 capitalize">{{ p.method }}</td>
                  <td class="px-4 py-3 text-center text-gray-700 dark:text-gray-300">{{ p.invoices_count }}</td>
                  <td class="px-4 py-3 text-right font-semibold text-emerald-700">$ {{ +p.amount | number:'1.0-0' }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class PortalPaymentsComponent implements OnInit {
  private readonly portal = inject(PortalService);
  loading = signal(true);
  payments = signal<PortalPaymentItem[]>([]);

  ngOnInit(): void {
    this.portal.payments().subscribe({
      next: (data) => { this.payments.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
}
