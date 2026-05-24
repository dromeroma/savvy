import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  CashAccountType,
  WaterCashAccountCreate,
  WaterCashAccountListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-cash-accounts-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './cash-accounts-list.component.html',
})
export class CashAccountsListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  accounts = signal<WaterCashAccountListItem[]>([]);

  formOpen = signal(false);
  editing = signal<WaterCashAccountListItem | null>(null);
  saving = signal(false);
  formError = signal('');
  form: WaterCashAccountCreate = this.emptyForm();

  readonly types: { v: CashAccountType; n: string }[] = [
    { v: 'cash', n: 'Efectivo (caja)' },
    { v: 'bank', n: 'Cuenta bancaria' },
    { v: 'other', n: 'Otra' },
  ];

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.water.listCashAccounts().subscribe({
      next: (data) => {
        this.accounts.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.editing.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(a: WaterCashAccountListItem): void {
    this.editing.set(a);
    this.water.getCashAccount(a.id).subscribe({
      next: (full) => {
        this.form = {
          code: full.code,
          name: full.name,
          type: full.type,
          initial_balance: full.initial_balance,
          is_default: full.is_default,
          is_active: full.is_active,
          notes: full.notes,
        };
        this.formError.set('');
        this.formOpen.set(true);
      },
    });
  }

  closeForm(): void { this.formOpen.set(false); }

  submit(): void {
    if (!this.form.code || !this.form.name) {
      this.formError.set('Código y nombre son obligatorios.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    const e = this.editing();
    const obs = e
      ? this.water.updateCashAccount(e.id, this.stripImmutable(this.form))
      : this.water.createCashAccount(this.form);
    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({ type: 'success', title: e ? 'Actualizada' : 'Creada', message: 'Cuenta guardada.' });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'Error al guardar.');
      },
    });
  }

  confirmDelete(a: WaterCashAccountListItem): void {
    if (!confirm(`¿Eliminar la cuenta "${a.name}"?`)) return;
    this.water.deleteCashAccount(a.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminada', message: 'Cuenta eliminada.' });
        this.load();
      },
      error: (err) => {
        this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo eliminar.' });
      },
    });
  }

  typeBadge(t: string): string {
    switch (t) {
      case 'cash': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'bank': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  }

  private emptyForm(): WaterCashAccountCreate {
    return {
      code: '',
      name: '',
      type: 'cash',
      initial_balance: 0,
      is_default: false,
      is_active: true,
    };
  }

  private stripImmutable(data: WaterCashAccountCreate): Partial<WaterCashAccountCreate> {
    const { code, ...rest } = data;
    return rest;
  }
}
