import { Component, computed, ElementRef, HostListener, inject, OnInit, signal, ViewChild } from '@angular/core';
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
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-memorial-payments-list',
  imports: [CommonModule, FormsModule, PaginationComponent],
  templateUrl: './payments-list.component.html',
})
export class MemorialPaymentsListComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  payments = signal<MemorialPaymentListItem[]>([]);
  contractsForPicker = signal<ExequialContractListItem[]>([]);

  // Contract picker (searchable)
  @ViewChild('contractPicker') contractPickerEl?: ElementRef<HTMLDivElement>;
  contractSearchTerm = '';
  contractPickerOpen = signal(false);
  contractPickerLoading = signal(false);
  contractPickerHighlight = signal(-1);
  selectedContract = signal<ExequialContractListItem | null>(null);
  private searchDebounce?: ReturnType<typeof setTimeout>;

  page = signal(0);
  pageSize = signal(20);
  paginatedPayments = computed(() => {
    const start = this.page() * this.pageSize();
    return this.payments().slice(start, start + this.pageSize());
  });

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
    this.searchContracts('');
  }

  load(): void {
    this.loading.set(true);
    this.memorial.listPayments({
      method: this.filterMethod || undefined,
      date_from: this.filterDateFrom || undefined,
      date_to: this.filterDateTo || undefined,
    }).subscribe({
      next: (data) => { this.payments.set(data); this.page.set(0); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.pendingInvoices.set([]);
    this.formError.set('');
    this.selectedContract.set(null);
    this.contractSearchTerm = '';
    this.searchContracts('');
    this.formOpen.set(true);
  }

  closeForm(): void {
    this.formOpen.set(false);
    this.contractPickerOpen.set(false);
  }

  // ============ Contract picker ============

  searchContracts(term: string): void {
    this.contractPickerLoading.set(true);
    this.memorial.listContracts({
      status: 'active',
      search: term?.trim() || undefined,
      limit: 50,
    }).subscribe({
      next: (data) => {
        this.contractsForPicker.set(data);
        this.contractPickerHighlight.set(-1);
        this.contractPickerLoading.set(false);
      },
      error: () => this.contractPickerLoading.set(false),
    });
  }

  onContractSearchInput(value: string): void {
    this.contractSearchTerm = value;
    this.contractPickerOpen.set(true);
    if (this.searchDebounce) clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => this.searchContracts(value), 250);
  }

  selectContract(c: ExequialContractListItem): void {
    this.form.contract_id = c.id;
    this.selectedContract.set(c);
    this.form.payer_name = c.titular_display;
    this.contractSearchTerm = '';
    this.contractPickerOpen.set(false);
    this.loadPendingInvoices(c.id);
  }

  clearContract(): void {
    this.form.contract_id = null;
    this.selectedContract.set(null);
    this.pendingInvoices.set([]);
    this.contractSearchTerm = '';
    this.searchContracts('');
    this.contractPickerOpen.set(true);
  }

  private loadPendingInvoices(contractId: string): void {
    this.memorial.listInvoices({ contract_id: contractId, unpaid_only: true }).subscribe({
      next: (data) => this.pendingInvoices.set(data),
    });
  }

  onPickerKey(ev: KeyboardEvent): void {
    const list = this.contractsForPicker();
    if (!this.contractPickerOpen()) {
      if (ev.key === 'ArrowDown' || ev.key === 'Enter') {
        this.contractPickerOpen.set(true);
      }
      return;
    }
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      this.contractPickerHighlight.set(Math.min(this.contractPickerHighlight() + 1, list.length - 1));
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      this.contractPickerHighlight.set(Math.max(this.contractPickerHighlight() - 1, 0));
    } else if (ev.key === 'Enter') {
      ev.preventDefault();
      const idx = this.contractPickerHighlight();
      if (idx >= 0 && idx < list.length) this.selectContract(list[idx]);
    } else if (ev.key === 'Escape') {
      this.contractPickerOpen.set(false);
    }
  }

  @HostListener('document:mousedown', ['$event'])
  onDocClick(ev: MouseEvent): void {
    if (!this.contractPickerOpen()) return;
    const root = this.contractPickerEl?.nativeElement;
    if (root && !root.contains(ev.target as Node)) {
      this.contractPickerOpen.set(false);
    }
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
