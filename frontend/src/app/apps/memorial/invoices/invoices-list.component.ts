import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  MemorialInvoiceListItem,
  MemorialInvoiceSource,
  MemorialInvoiceStatus,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { WhatsappShareButtonComponent } from '../../../shared/components/whatsapp-share-button/whatsapp-share-button.component';

@Component({
  selector: 'app-memorial-invoices-list',
  imports: [CommonModule, FormsModule, WhatsappShareButtonComponent],
  templateUrl: './invoices-list.component.html',
})
export class MemorialInvoicesListComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  invoices = signal<MemorialInvoiceListItem[]>([]);

  filterSource = '';
  filterStatus = '';
  unpaidOnly = false;
  generating = signal(false);

  readonly sources: { value: MemorialInvoiceSource | ''; label: string }[] = [
    { value: '', label: 'Todos los orígenes' },
    { value: 'exequial_dues', label: 'Cuota plan exequial' },
    { value: 'service', label: 'Servicio funerario' },
  ];

  readonly statuses: { value: MemorialInvoiceStatus | ''; label: string }[] = [
    { value: '', label: 'Todos los estados' },
    { value: 'pending', label: 'Pendiente' },
    { value: 'partial', label: 'Pago parcial' },
    { value: 'paid', label: 'Pagada' },
    { value: 'overdue', label: 'Vencida' },
    { value: 'annulled', label: 'Anulada' },
  ];

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.memorial.listInvoices({
      source_type: this.filterSource || undefined,
      status: this.filterStatus || undefined,
      unpaid_only: this.unpaidOnly || undefined,
    }).subscribe({
      next: (data) => { this.invoices.set(data); this.loading.set(false); },
      error: (err) => {
        this.loading.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudieron cargar las facturas.',
        });
      },
    });
  }

  generateDues(): void {
    if (!confirm('Generar cuotas para todos los contratos activos cuya fecha de pago ya llegó. ¿Continuar?')) return;
    this.generating.set(true);
    this.memorial.batchGenerateDues().subscribe({
      next: (r) => {
        this.generating.set(false);
        this.notify.show({
          type: 'success', title: 'Cuotas generadas',
          message: `Se generaron ${r.generated} cuotas (saltadas: ${r.skipped_no_fee}).`,
        });
        this.load();
      },
      error: (err) => {
        this.generating.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudieron generar las cuotas.',
        });
      },
    });
  }

  downloadPdf(id: string): void {
    this.memorial.downloadInvoicePdf(id).subscribe({
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

  confirmAnnul(inv: MemorialInvoiceListItem): void {
    if (+inv.paid_amount > 0) {
      this.notify.show({
        type: 'warning', title: 'No permitido',
        message: 'No se puede anular una factura con pagos aplicados.',
      });
      return;
    }
    if (!confirm(`¿Anular la factura ${inv.code}?`)) return;
    this.memorial.annulInvoice(inv.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Anulada', message: inv.code }); this.load(); },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo anular.',
      }),
    });
  }

  badge(s: string): string {
    switch (s) {
      case 'pending': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'partial': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'paid': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'overdue': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'annulled': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 line-through';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  statusLabel(s: string): string {
    return this.statuses.find(x => x.value === s)?.label || s;
  }

  sourceLabel(s: string): string {
    return this.sources.find(x => x.value === s)?.label || s;
  }

  whatsappTextFor(i: MemorialInvoiceListItem): string {
    const total = Math.round(+i.total).toLocaleString('es-CO');
    const balance = Math.round(+i.balance).toLocaleString('es-CO');
    const lines = [
      `Factura ${i.code}`,
      `${this.sourceLabel(i.source_type)}`,
      `Total: $ ${total}`,
    ];
    if (+i.balance > 0) {
      lines.push(`Saldo pendiente: $ ${balance}`);
      lines.push(`Vence: ${i.due_date}`);
    } else if (i.status !== 'annulled') {
      lines.push('Estado: PAGADA ✅');
    }
    return lines.join('\n');
  }
}
