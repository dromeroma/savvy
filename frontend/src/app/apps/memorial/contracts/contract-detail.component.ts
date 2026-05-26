import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  ContractStatus,
  ExequialBeneficiaryCreate,
  ExequialContract,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-contract-detail',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './contract-detail.component.html',
})
export class MemorialContractDetailComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  contract = signal<ExequialContract | null>(null);

  addingBen = signal(false);
  savingBen = signal(false);
  benForm: ExequialBeneficiaryCreate = this.emptyBeneficiary();

  transitioning = signal(false);

  allowed = computed<ContractStatus[]>(() => {
    const s = this.contract()?.status;
    switch (s) {
      case 'active': return ['suspended', 'cancelled', 'expired'];
      case 'suspended': return ['active', 'cancelled'];
      case 'expired': return ['active', 'cancelled'];
      default: return [];
    }
  });

  titularDisplay = computed(() => {
    const c = this.contract();
    if (!c) return '';
    if (c.affiliate_type === 'empresarial') return c.titular_business_name || '(sin nombre)';
    return `${c.titular_first_name || ''} ${c.titular_last_name || ''}`.trim() || '(sin nombre)';
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading.set(true);
    this.memorial.getContract(id).subscribe({
      next: (c) => { this.contract.set(c); this.loading.set(false); },
      error: () => {
        this.loading.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar el contrato.' });
      },
    });
  }

  transition(s: ContractStatus): void {
    const c = this.contract();
    if (!c) return;
    let reason: string | undefined;
    if (s === 'cancelled') {
      reason = prompt('Motivo de cancelación (opcional):') || undefined;
    }
    const label = this.statusLabel(s);
    if (!confirm(`¿Cambiar el contrato a "${label}"?`)) return;
    this.transitioning.set(true);
    this.memorial.transitionContract(c.id, s, reason).subscribe({
      next: (upd) => {
        this.contract.set(upd);
        this.transitioning.set(false);
        this.notify.show({ type: 'success', title: 'Estado actualizado', message: label });
      },
      error: (err) => {
        this.transitioning.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo cambiar el estado.',
        });
      },
    });
  }

  // Beneficiaries
  openAddBen(): void {
    this.benForm = this.emptyBeneficiary();
    this.addingBen.set(true);
  }
  closeAddBen(): void { this.addingBen.set(false); }

  saveBen(): void {
    const c = this.contract();
    if (!c || !this.benForm.first_name.trim()) return;
    this.savingBen.set(true);
    this.memorial.addBeneficiary(c.id, this.benForm).subscribe({
      next: () => {
        this.savingBen.set(false);
        this.closeAddBen();
        this.load(c.id);
      },
      error: (err) => {
        this.savingBen.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo añadir el beneficiario.',
        });
      },
    });
  }

  removeBen(id: string): void {
    const c = this.contract();
    if (!c) return;
    if (!confirm('¿Eliminar este beneficiario?')) return;
    this.memorial.removeBeneficiary(c.id, id).subscribe({
      next: () => this.load(c.id),
      error: () => this.notify.show({
        type: 'error', title: 'Error', message: 'No se pudo eliminar.',
      }),
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
    switch (f) {
      case 'monthly': return 'Mensual';
      case 'quarterly': return 'Trimestral';
      case 'semiannual': return 'Semestral';
      case 'annual': return 'Anual';
      default: return f;
    }
  }

  affiliateLabel(t: string): string {
    switch (t) {
      case 'individual': return 'Individual';
      case 'familiar': return 'Familiar';
      case 'empresarial': return 'Empresarial';
      default: return t;
    }
  }

  private emptyBeneficiary(): ExequialBeneficiaryCreate {
    return {
      first_name: '',
      last_name: '',
      relationship: '',
      document_number: '',
      is_titular: false,
    };
  }
}
