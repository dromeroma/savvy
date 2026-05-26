import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  ContractStatus,
  ExequialContractCreate,
  ExequialContractListItem,
  ExequialPlanListItem,
  PaymentFrequency,
  PlanType,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-contracts-list',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './contracts-list.component.html',
})
export class MemorialContractsListComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);
  private readonly router = inject(Router);

  loading = signal(true);
  contracts = signal<ExequialContractListItem[]>([]);
  plansForPicker = signal<ExequialPlanListItem[]>([]);

  search = '';
  filterStatus = '';
  filterPlan = '';
  private searchTimer: any;

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: ExequialContractCreate = this.emptyForm();
  beneficiaryDraft = this.emptyBeneficiary();

  readonly statuses: { value: ContractStatus | ''; label: string }[] = [
    { value: '', label: 'Todos los estados' },
    { value: 'active', label: 'Activo' },
    { value: 'suspended', label: 'Suspendido' },
    { value: 'cancelled', label: 'Cancelado' },
    { value: 'expired', label: 'Expirado' },
  ];

  readonly frequencies: { value: PaymentFrequency; label: string }[] = [
    { value: 'monthly', label: 'Mensual' },
    { value: 'quarterly', label: 'Trimestral' },
    { value: 'semiannual', label: 'Semestral' },
    { value: 'annual', label: 'Anual' },
  ];

  readonly types: { value: PlanType; label: string }[] = [
    { value: 'individual', label: 'Individual' },
    { value: 'familiar', label: 'Familiar' },
    { value: 'empresarial', label: 'Empresarial' },
  ];

  ngOnInit(): void {
    this.load();
    this.memorial.listPlans({ active_only: true }).subscribe({
      next: (plans) => this.plansForPicker.set(plans),
    });
  }

  load(): void {
    this.loading.set(true);
    this.memorial.listContracts({
      search: this.search || undefined,
      status: this.filterStatus || undefined,
      plan_id: this.filterPlan || undefined,
    }).subscribe({
      next: (data) => { this.contracts.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  onSearchChange(): void {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.load(), 300);
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.beneficiaryDraft = this.emptyBeneficiary();
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  // Mantener beneficiarios en sincronía con el tipo de plan
  onAffiliateTypeChange(): void {
    if (this.form.affiliate_type === 'individual') {
      // forzar 1 beneficiario titular = el mismo titular
      this.form.beneficiaries = [];
    }
  }

  addBeneficiary(): void {
    if (!this.beneficiaryDraft.first_name?.trim()) return;
    this.form.beneficiaries = [...(this.form.beneficiaries || []), { ...this.beneficiaryDraft }];
    this.beneficiaryDraft = this.emptyBeneficiary();
  }

  removeBeneficiary(idx: number): void {
    const list = [...(this.form.beneficiaries || [])];
    list.splice(idx, 1);
    this.form.beneficiaries = list;
  }

  submit(): void {
    if (!this.form.plan_id || !this.form.affiliate_type || !this.form.payment_frequency || !this.form.start_date) {
      this.formError.set('Plan, tipo, frecuencia y fecha de inicio son obligatorios.');
      return;
    }
    // Empresarial requiere razón social; individual/familiar requieren nombre del titular
    if (this.form.affiliate_type === 'empresarial' && !this.form.titular_business_name?.trim()) {
      this.formError.set('Para contratos empresariales, ingresa la razón social.');
      return;
    }
    if (this.form.affiliate_type !== 'empresarial' && !this.form.titular_first_name?.trim()) {
      this.formError.set('Ingresa el nombre del titular.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    this.memorial.createContract(this.form).subscribe({
      next: (c) => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({
          type: 'success', title: 'Contrato creado',
          message: `${c.code} · ${c.plan_name}`,
        });
        this.router.navigate(['/memorial/contracts', c.id]);
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail;
        this.formError.set(typeof detail === 'string' ? detail : 'Error al crear el contrato.');
      },
    });
  }

  badge(s: string): string {
    switch (s) {
      case 'active': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'suspended': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'cancelled': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 line-through';
      case 'expired': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  statusLabel(s: string): string {
    switch (s) {
      case 'active': return 'Activo';
      case 'suspended': return 'Suspendido';
      case 'cancelled': return 'Cancelado';
      case 'expired': return 'Expirado';
      default: return s;
    }
  }

  freqLabel(f: string): string {
    return this.frequencies.find(x => x.value === f)?.label || f;
  }

  affiliateLabel(t: string): string {
    return this.types.find(x => x.value === t)?.label || t;
  }

  // Filtra los planes del picker por tipo escogido en el form
  plansFiltered(): ExequialPlanListItem[] {
    if (!this.form.affiliate_type) return this.plansForPicker();
    return this.plansForPicker().filter(p => p.plan_type === this.form.affiliate_type);
  }

  private emptyForm(): ExequialContractCreate {
    return {
      plan_id: '',
      affiliate_type: 'individual',
      payment_frequency: 'monthly',
      start_date: new Date().toISOString().slice(0, 10),
      beneficiaries: [],
    };
  }

  private emptyBeneficiary() {
    return {
      first_name: '',
      last_name: '',
      document_type: null as string | null,
      document_number: '',
      relationship: '',
      is_titular: false,
    };
  }
}
