import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  ExequialPlan,
  ExequialPlanCreate,
  ExequialPlanListItem,
  PlanType,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-plans-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './plans-list.component.html',
})
export class MemorialPlansListComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  plans = signal<ExequialPlanListItem[]>([]);

  search = '';
  activeOnly = false;
  private searchTimer: any;

  formOpen = signal(false);
  editing = signal<ExequialPlan | null>(null);
  saving = signal(false);
  formError = signal('');
  form: ExequialPlanCreate = this.emptyForm();
  coverageInput = '';  // textarea con un item por línea

  readonly types: { value: PlanType; label: string }[] = [
    { value: 'individual', label: 'Individual' },
    { value: 'familiar', label: 'Familiar' },
    { value: 'empresarial', label: 'Empresarial' },
  ];

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.memorial.listPlans({
      active_only: this.activeOnly || undefined,
      search: this.search || undefined,
    }).subscribe({
      next: (data) => { this.plans.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  onSearchChange(): void {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.load(), 300);
  }

  openCreate(): void {
    this.editing.set(null);
    this.form = this.emptyForm();
    this.coverageInput = '';
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(p: ExequialPlanListItem): void {
    this.memorial.getPlan(p.id).subscribe({
      next: (full) => {
        this.editing.set(full);
        this.form = {
          code: full.code,
          name: full.name,
          description: full.description,
          plan_type: full.plan_type,
          max_beneficiaries: full.max_beneficiaries,
          max_age_at_affiliation: full.max_age_at_affiliation,
          max_age_for_coverage: full.max_age_for_coverage,
          waiting_period_days: full.waiting_period_days,
          monthly_fee: full.monthly_fee,
          quarterly_fee: full.quarterly_fee,
          semiannual_fee: full.semiannual_fee,
          annual_fee: full.annual_fee,
          coverage_amount: full.coverage_amount,
          coverage_items: full.coverage_items || [],
          is_active: full.is_active,
          valid_from: full.valid_from,
          valid_to: full.valid_to,
        };
        this.coverageInput = (full.coverage_items || []).join('\n');
        this.formError.set('');
        this.formOpen.set(true);
      },
    });
  }

  closeForm(): void { this.formOpen.set(false); }

  submit(): void {
    if (!this.form.code || !this.form.name || !this.form.valid_from) {
      this.formError.set('Código, nombre y vigencia desde son obligatorios.');
      return;
    }
    this.form.coverage_items = this.coverageInput
      .split('\n').map(s => s.trim()).filter(Boolean);
    this.saving.set(true);
    this.formError.set('');
    const e = this.editing();
    const obs = e
      ? this.memorial.updatePlan(e.id, this.stripImmutable(this.form))
      : this.memorial.createPlan(this.form);
    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({
          type: 'success',
          title: e ? 'Plan actualizado' : 'Plan creado',
          message: this.form.name,
        });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail;
        this.formError.set(typeof detail === 'string' ? detail : 'Error al guardar.');
      },
    });
  }

  confirmDelete(p: ExequialPlanListItem): void {
    if (p.contracts_count > 0) {
      this.notify.show({
        type: 'warning', title: 'Plan en uso',
        message: `Este plan tiene ${p.contracts_count} contrato(s). Desactívalo en vez de eliminarlo.`,
      });
      return;
    }
    if (!confirm(`¿Eliminar el plan "${p.name}"?`)) return;
    this.memorial.deletePlan(p.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminado', message: p.name });
        this.load();
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo eliminar.',
      }),
    });
  }

  typeLabel(t: string): string {
    switch (t) {
      case 'individual': return 'Individual';
      case 'familiar': return 'Familiar';
      case 'empresarial': return 'Empresarial';
      default: return t;
    }
  }

  typeBadge(t: string): string {
    switch (t) {
      case 'individual': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'familiar': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'empresarial': return 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  private emptyForm(): ExequialPlanCreate {
    return {
      code: '',
      name: '',
      plan_type: 'individual',
      waiting_period_days: 30,
      monthly_fee: 0,
      quarterly_fee: 0,
      semiannual_fee: 0,
      annual_fee: 0,
      coverage_amount: 0,
      coverage_items: [],
      is_active: true,
      valid_from: new Date().toISOString().slice(0, 10),
    };
  }

  private stripImmutable(data: ExequialPlanCreate): Partial<ExequialPlanCreate> {
    const { code, plan_type, valid_from, ...rest } = data;
    return rest;
  }
}
