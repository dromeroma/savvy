import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PortalService } from '../../core/services/portal.service';
import { PortalInvoiceItem } from '../../core/models/portal.model';
import { NotificationService } from '../../shared/services/notification.service';

@Component({
  selector: 'app-portal-invoices',
  imports: [CommonModule],
  template: `
    <div>
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90 mb-1">Mis facturas</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-5">
        Historial completo. Las facturas pendientes aparecen primero.
      </p>

      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-sky-200 border-t-sky-600"></div>
        </div>
      } @else if (invoices().length === 0) {
        <div class="rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-10 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">Aún no tienes facturas.</p>
        </div>
      } @else {
        <div class="space-y-2">
          @for (i of invoices(); track i.id) {
            <div class="rounded-xl border bg-white dark:bg-gray-800 p-4"
              [ngClass]="i.status === 'overdue'
                ? 'border-red-300 dark:border-red-700/50'
                : 'border-gray-200 dark:border-gray-700'">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-semibold text-gray-800 dark:text-white/90">Factura #{{ i.consecutive }}</span>
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize"
                      [ngClass]="badge(i.status)">{{ statusLabel(i.status) }}</span>
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Periodo {{ i.period_year }}-{{ pad(i.period_month) }} ·
                    Consumo: {{ i.consumption_cubic }} m³
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    Vence: {{ i.due_date }}
                  </div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-[10px] text-gray-400 uppercase">Total</div>
                  <div class="text-lg font-bold text-gray-800 dark:text-white/90">$ {{ +i.total | number:'1.0-0' }}</div>
                  @if (+i.balance > 0) {
                    <div class="text-[10px] text-red-600 mt-0.5">Saldo: $ {{ +i.balance | number:'1.0-0' }}</div>
                  } @else if (i.status !== 'annulled') {
                    <div class="text-[10px] text-emerald-600 mt-0.5">Pagada</div>
                  }
                </div>
              </div>
              <button (click)="downloadPdf(i.id)"
                class="mt-3 w-full px-3 py-2 rounded-lg text-xs font-medium bg-sky-500 hover:bg-sky-600 text-white">
                Descargar PDF
              </button>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class PortalInvoicesComponent implements OnInit {
  private readonly portal = inject(PortalService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  invoices = signal<PortalInvoiceItem[]>([]);

  ngOnInit(): void {
    this.portal.invoices().subscribe({
      next: (data) => { this.invoices.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  downloadPdf(id: string): void {
    this.portal.downloadMyInvoicePdf(id).subscribe({
      next: ({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `factura-${id}.pdf`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      },
      error: () => this.notify.show({
        type: 'error', title: 'Error', message: 'No se pudo descargar el PDF.',
      }),
    });
  }

  badge(s: string): string {
    switch (s) {
      case 'pending': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'partial': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'paid': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'overdue': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'annulled': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  statusLabel(s: string): string {
    switch (s) {
      case 'pending': return 'Pendiente';
      case 'partial': return 'Pago parcial';
      case 'paid': return 'Pagada';
      case 'overdue': return 'Vencida';
      case 'annulled': return 'Anulada';
      default: return s;
    }
  }

  pad(n: number): string { return String(n).padStart(2, '0'); }
}
