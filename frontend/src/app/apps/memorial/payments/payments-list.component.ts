import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  ExequialContractListItem,
  MemorialInvoiceListItem,
  MemorialPaymentCreate,
  MemorialPaymentListItem,
  MemorialPaymentMethod,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-payments-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './payments-list.component.html',
})
export class MemorialPaymentsListComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  payments = signal<MemorialPaymentListItem[]>([]);
  contractsForPicker = signal<ExequialContractListItem[]>([]);

  filterMethod = '';
  filterDateFrom = '';
  filterDateTo = '';

  // Form
  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: MemorialPaymentCreate = this.emptyForm();
  pendingInvoices = signal<MemorialInvoiceListItem[]>([]);

  readonly methods: { value: MemorialPaymentMethod | ''; label: string }[] = [
    { value: '', label: 'Todos los métodos' },
    { value: 'cash', label: 'Efectivo' },
    { value: 'transfer', label: 'Transferencia' },
    { value: 'card', label: 'Tarjeta' },
    { value: 'check', label: 'Cheque' },
    { value: 'online', label: 'Pago en línea' },
  ];

  pendingBalance = computed(() => {
    return this.pendingInvoices()
      .reduce((acc, inv) => acc + (+inv.balance), 0);
  });

  ngOnInit(): void {
    this.load();
    this.memorial.listContracts({ status: 'active', limit: 500 }).subscribe({
      next: (data) => this.contractsForPicker.set(data),
    });
  }

  load(): void {
    this.loading.set(true);
    this.memorial.listPayments({
      method: this.filterMethod || undefined,
      date_from: this.filterDateFrom || undefined,
      date_to: this.filterDateTo || undefined,
    }).subscribe({
      next: (data) => { this.payments.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.pendingInvoices.set([]);
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  onContractChange(): void {
    // Cargar facturas pendientes del contrato seleccionado
    if (!this.form.contract_id) {
      this.pendingInvoices.set([]);
      return;
    }
    // Tomar nombre del titular del contrato
    const c = this.contractsForPicker().find(x => x.id === this.form.contract_id);
    if (c) this.form.payer_name = c.titular_display;
    this.memorial.listInvoices({
      contract_id: this.form.contract_id,
      unpaid_only: true,
    }).subscribe({
      next: (data) => this.pendingInvoices.set(data),
    });
  }

  submit(): void {
    if (!this.form.contract_id && !this.form.service_id) {
      this.formError.set('Selecciona un contrato o servicio asociado.');
      return;
    }
    if (!this.form.payer_name?.trim() || !this.form.payment_date || !this.form.amount) {
      this.formError.set('Pagador, fecha y monto son obligatorios.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    this.memorial.registerPayment(this.form).subscribe({
      next: (p) => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({
          type: 'success', title: 'Pago registrado',
          message: `${p.code} · $ ${(+p.amount).toLocaleString('es-CO')}`,
        });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail;
        this.formError.set(typeof detail === 'string' ? detail : 'Error al registrar el pago.');
      },
    });
  }

  methodLabel(m: string): string {
    return this.methods.find(x => x.value === m)?.label || m;
  }

  private emptyForm(): MemorialPaymentCreate {
    return {
      contract_id: null,
      service_id: null,
      payer_name: '',
      payment_date: new Date().toISOString().slice(0, 10),
      amount: 0,
      method: 'cash',
    };
  }
}
