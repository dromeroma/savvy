import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  PaymentMethod,
  WaterInvoiceListItem,
  WaterPaymentCreate,
  WaterPaymentListItem,
  WaterSubscriberListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-payments-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './payments-list.component.html',
})
export class PaymentsListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  payments = signal<WaterPaymentListItem[]>([]);
  subscribers = signal<WaterSubscriberListItem[]>([]);

  // Filters
  filterMethod = '';
  filterDateFrom = '';
  filterDateTo = '';

  // Form
  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: WaterPaymentCreate = this.emptyForm();
  subscriberInvoices = signal<WaterInvoiceListItem[]>([]);

  /** Preview of auto-allocation based on the amount entered. */
  readonly allocationPreview = computed(() => {
    const amount = parseFloat(String(this.form.amount || 0));
    if (amount <= 0) return [];
    let remaining = amount;
    const result: { invoice: WaterInvoiceListItem; amount: number }[] = [];
    for (const inv of this.subscriberInvoices()) {
      if (remaining <= 0) break;
      const bal = parseFloat(inv.balance);
      if (bal <= 0) continue;
      const apply = Math.min(remaining, bal);
      result.push({ invoice: inv, amount: apply });
      remaining -= apply;
    }
    return result;
  });

  readonly allocationLeftover = computed(() => {
    const amount = parseFloat(String(this.form.amount || 0));
    const allocated = this.allocationPreview().reduce((s, r) => s + r.amount, 0);
    return Math.max(0, amount - allocated);
  });

  readonly methods: { v: PaymentMethod | ''; n: string }[] = [
    { v: '', n: 'Todos los métodos' },
    { v: 'cash', n: 'Efectivo' },
    { v: 'transfer', n: 'Transferencia' },
    { v: 'card', n: 'Tarjeta' },
    { v: 'check', n: 'Cheque' },
    { v: 'online', n: 'Online' },
  ];

  ngOnInit(): void {
    this.water.listSubscribers({ limit: 500 }).subscribe({
      next: (data) => this.subscribers.set(data),
    });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.water.listPayments({
      method: this.filterMethod || undefined,
      date_from: this.filterDateFrom || undefined,
      date_to: this.filterDateTo || undefined,
    }).subscribe({
      next: (data) => {
        this.payments.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.subscriberInvoices.set([]);
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  onSubscriberChange(subId: string): void {
    this.form.subscriber_id = subId;
    if (!subId) {
      this.subscriberInvoices.set([]);
      return;
    }
    this.water.listInvoices({ subscriber_id: subId, unpaid_only: true, limit: 100 }).subscribe({
      next: (data) => this.subscriberInvoices.set(data),
    });
  }

  submit(): void {
    if (!this.form.subscriber_id) {
      this.formError.set('Selecciona el suscriptor.');
      return;
    }
    const amount = parseFloat(String(this.form.amount || 0));
    if (amount <= 0) {
      this.formError.set('El monto debe ser mayor a 0.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    this.water.registerPayment(this.form).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({
          type: 'success', title: 'Pago registrado',
          message: 'El pago se aplicó a las facturas pendientes.',
        });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'Error al registrar el pago.');
      },
    });
  }

  methodLabel(m: PaymentMethod): string {
    return this.methods.find((x) => x.v === m)?.n ?? m;
  }

  /** Total unpaid balance for the selected subscriber (sum of preview source). */
  get subscriberOpenBalance(): number {
    return this.subscriberInvoices().reduce((s, i) => s + parseFloat(i.balance), 0);
  }

  private emptyForm(): WaterPaymentCreate {
    return {
      subscriber_id: '',
      amount: 0,
      payment_date: new Date().toISOString().slice(0, 10),
      method: 'cash',
    };
  }
}
