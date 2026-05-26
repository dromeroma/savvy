import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  BatchGenerateResult,
  InvoiceStatus,
  WaterInvoice,
  WaterInvoiceListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { WhatsappShareButtonComponent } from '../../../shared/components/whatsapp-share-button/whatsapp-share-button.component';

@Component({
  selector: 'app-invoices-list',
  imports: [CommonModule, FormsModule, WhatsappShareButtonComponent],
  templateUrl: './invoices-list.component.html',
})
export class InvoicesListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  invoices = signal<WaterInvoiceListItem[]>([]);

  filterStatus = '';
  filterYear = new Date().getFullYear();
  filterMonth: number | '' = '';
  unpaidOnly = false;

  // Detail
  detailOpen = signal(false);
  detail = signal<WaterInvoice | null>(null);

  // Batch generate
  batchOpen = signal(false);
  batchSaving = signal(false);
  batchResult = signal<BatchGenerateResult | null>(null);
  batchYear = new Date().getFullYear();
  batchMonth = new Date().getMonth() + 1;
  batchIssueDate = new Date().toISOString().slice(0, 10);
  batchDueDate: string | null = null;

  readonly years = (() => {
    const y = new Date().getFullYear();
    return [y - 2, y - 1, y, y + 1];
  })();
  readonly months = [
    { v: 1, n: 'Enero' }, { v: 2, n: 'Febrero' }, { v: 3, n: 'Marzo' },
    { v: 4, n: 'Abril' }, { v: 5, n: 'Mayo' }, { v: 6, n: 'Junio' },
    { v: 7, n: 'Julio' }, { v: 8, n: 'Agosto' }, { v: 9, n: 'Septiembre' },
    { v: 10, n: 'Octubre' }, { v: 11, n: 'Noviembre' }, { v: 12, n: 'Diciembre' },
  ];
  readonly statuses: { v: string; n: string }[] = [
    { v: '', n: 'Todos los estados' },
    { v: 'pending', n: 'Pendiente' },
    { v: 'partial', n: 'Parcial' },
    { v: 'paid', n: 'Pagada' },
    { v: 'overdue', n: 'Vencida' },
    { v: 'annulled', n: 'Anulada' },
  ];

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.water.listInvoices({
      status: this.filterStatus || undefined,
      period_year: this.filterYear,
      period_month: this.filterMonth === '' ? undefined : Number(this.filterMonth),
      unpaid_only: this.unpaidOnly || undefined,
    }).subscribe({
      next: (data) => {
        this.invoices.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  openDetail(inv: WaterInvoiceListItem): void {
    this.water.getInvoice(inv.id).subscribe({
      next: (full) => {
        this.detail.set(full);
        this.detailOpen.set(true);
      },
    });
  }
  closeDetail(): void { this.detailOpen.set(false); }

  confirmAnnul(inv: WaterInvoiceListItem): void {
    if (!confirm(`¿Anular factura #${inv.consecutive}?`)) return;
    this.water.annulInvoice(inv.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Anulada', message: `Factura #${inv.consecutive} anulada.` });
        this.load();
      },
      error: (err) => {
        this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo anular.' });
      },
    });
  }

  openBatch(): void {
    this.batchYear = new Date().getFullYear();
    this.batchMonth = new Date().getMonth() + 1;
    this.batchIssueDate = new Date().toISOString().slice(0, 10);
    this.batchDueDate = null;
    this.batchResult.set(null);
    this.batchOpen.set(true);
  }
  closeBatch(): void { this.batchOpen.set(false); }

  runBatch(): void {
    this.batchSaving.set(true);
    this.water.batchGenerateInvoices({
      period_year: this.batchYear,
      period_month: this.batchMonth,
      issue_date: this.batchIssueDate || null,
      due_date: this.batchDueDate || null,
    }).subscribe({
      next: (res) => {
        this.batchSaving.set(false);
        this.batchResult.set(res);
        this.notify.show({
          type: 'success', title: 'Lote procesado',
          message: `${res.generated} factura(s) generada(s).`,
        });
        this.load();
      },
      error: (err) => {
        this.batchSaving.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo procesar el lote.',
        });
      },
    });
  }

  downloadPdf(id: string, ev?: Event): void {
    ev?.stopPropagation();
    this.water.downloadInvoicePdf(id).subscribe({
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

  badgeClass(s: string): string {
    switch (s) {
      case 'pending': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'partial': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'paid': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'overdue': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'annulled': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 line-through';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  whatsappTextFor(d: WaterInvoice): string {
    const total = Math.round(+d.total).toLocaleString('es-CO');
    const balance = Math.round(+d.balance).toLocaleString('es-CO');
    const period = `${d.period_year}-${String(d.period_month).padStart(2, '0')}`;
    const lines = [
      `Factura #${d.consecutive} (${period})`,
      `Consumo: ${d.consumption_cubic} m³`,
      `Total: $ ${total}`,
    ];
    if (+d.balance > 0) {
      lines.push(`Saldo pendiente: $ ${balance}`);
      lines.push(`Vence: ${d.due_date}`);
    } else if (d.status !== 'annulled') {
      lines.push('Estado: PAGADA ✅');
    }
    return lines.join('\n');
  }
}
