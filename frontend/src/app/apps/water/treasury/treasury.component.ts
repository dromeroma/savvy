import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  ClosingPreview,
  ClosingResponse,
  MovementType,
  TreasuryDashboard,
  WaterCashAccountListItem,
  WaterTreasuryMovementCreate,
  WaterTreasuryMovementListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

type Tab = 'dashboard' | 'movements' | 'closings';

@Component({
  selector: 'app-treasury',
  imports: [CommonModule, FormsModule],
  templateUrl: './treasury.component.html',
})
export class TreasuryComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  tab = signal<Tab>('dashboard');

  // Dashboard
  dashboardLoading = signal(false);
  dashboard = signal<TreasuryDashboard | null>(null);

  // Accounts (used in filters/forms)
  accounts = signal<WaterCashAccountListItem[]>([]);

  // Movements
  movLoading = signal(false);
  movements = signal<WaterTreasuryMovementListItem[]>([]);
  filterAccount = '';
  filterType: '' | MovementType = '';
  filterDateFrom = '';
  filterDateTo = '';

  // Movement form
  movFormOpen = signal(false);
  movSaving = signal(false);
  movFormError = signal('');
  movForm: WaterTreasuryMovementCreate = this.emptyMovement();

  // Closings (arqueos)
  closingsLoading = signal(false);
  closings = signal<ClosingResponse[]>([]);

  // Arqueo form
  arqueoFormOpen = signal(false);
  arqueoSaving = signal(false);
  arqueoError = signal('');
  arqueoAccount = '';
  arqueoDate = new Date().toISOString().slice(0, 10);
  arqueoCounted: string | number = 0;
  arqueoNotes = '';
  arqueoPreview = signal<ClosingPreview | null>(null);

  readonly arqueoDiff = computed(() => {
    const p = this.arqueoPreview();
    if (!p) return 0;
    return parseFloat(String(this.arqueoCounted || 0)) - parseFloat(p.expected_balance);
  });

  readonly categoriesByType: Record<string, string[]> = {
    income: ['other_income', 'reconnection', 'donation'],
    expense: ['salary', 'utility', 'maintenance', 'office', 'transport', 'tax', 'other'],
  };

  ngOnInit(): void {
    this.water.listCashAccounts().subscribe({
      next: (data) => this.accounts.set(data),
    });
    this.loadDashboard();
  }

  setTab(t: Tab): void {
    this.tab.set(t);
    if (t === 'dashboard') this.loadDashboard();
    if (t === 'movements') this.loadMovements();
    if (t === 'closings') this.loadClosings();
  }

  // ---- Dashboard ----
  loadDashboard(): void {
    this.dashboardLoading.set(true);
    this.water.treasuryDashboard().subscribe({
      next: (d) => {
        this.dashboard.set(d);
        this.dashboardLoading.set(false);
      },
      error: () => this.dashboardLoading.set(false),
    });
  }

  // ---- Movements ----
  loadMovements(): void {
    this.movLoading.set(true);
    this.water.listTreasuryMovements({
      cash_account_id: this.filterAccount || undefined,
      type: this.filterType || undefined,
      date_from: this.filterDateFrom || undefined,
      date_to: this.filterDateTo || undefined,
    }).subscribe({
      next: (data) => {
        this.movements.set(data);
        this.movLoading.set(false);
      },
      error: () => this.movLoading.set(false),
    });
  }

  openMovementForm(): void {
    this.movForm = this.emptyMovement();
    // pre-select default account if any
    const def = this.accounts().find((a) => a.is_default && a.is_active);
    if (def) this.movForm.cash_account_id = def.id;
    this.movFormError.set('');
    this.movFormOpen.set(true);
  }
  closeMovementForm(): void { this.movFormOpen.set(false); }

  submitMovement(): void {
    if (!this.movForm.cash_account_id || !this.movForm.description) {
      this.movFormError.set('Cuenta y descripción son obligatorias.');
      return;
    }
    const amount = parseFloat(String(this.movForm.amount || 0));
    if (amount <= 0) {
      this.movFormError.set('El monto debe ser mayor a 0.');
      return;
    }
    this.movSaving.set(true);
    this.movFormError.set('');
    this.water.createTreasuryMovement(this.movForm).subscribe({
      next: () => {
        this.movSaving.set(false);
        this.closeMovementForm();
        this.notify.show({ type: 'success', title: 'Registrado', message: 'Movimiento de tesorería registrado.' });
        this.loadMovements();
        this.loadDashboard();
      },
      error: (err) => {
        this.movSaving.set(false);
        this.movFormError.set(err?.error?.detail || 'Error al guardar.');
      },
    });
  }

  confirmDeleteMovement(m: WaterTreasuryMovementListItem): void {
    if (m.payment_id) {
      this.notify.show({
        type: 'error', title: 'No permitido',
        message: 'Este movimiento fue generado por un pago. Anula el pago en su lugar.',
      });
      return;
    }
    if (!confirm(`¿Eliminar el movimiento "${m.description}"?`)) return;
    this.water.deleteTreasuryMovement(m.id).subscribe({
      next: () => {
        this.loadMovements();
        this.loadDashboard();
      },
    });
  }

  // ---- Closings ----
  loadClosings(): void {
    this.closingsLoading.set(true);
    this.water.listClosings().subscribe({
      next: (data) => {
        this.closings.set(data);
        this.closingsLoading.set(false);
      },
      error: () => this.closingsLoading.set(false),
    });
  }

  openArqueo(): void {
    const def = this.accounts().find((a) => a.is_default && a.is_active);
    this.arqueoAccount = def?.id ?? '';
    this.arqueoDate = new Date().toISOString().slice(0, 10);
    this.arqueoCounted = 0;
    this.arqueoNotes = '';
    this.arqueoPreview.set(null);
    this.arqueoError.set('');
    this.arqueoFormOpen.set(true);
    if (this.arqueoAccount) this.refreshArqueoPreview();
  }
  closeArqueo(): void { this.arqueoFormOpen.set(false); }

  refreshArqueoPreview(): void {
    if (!this.arqueoAccount || !this.arqueoDate) {
      this.arqueoPreview.set(null);
      return;
    }
    this.water.closingPreview(this.arqueoAccount, this.arqueoDate).subscribe({
      next: (p) => this.arqueoPreview.set(p),
      error: () => this.arqueoPreview.set(null),
    });
  }

  submitArqueo(): void {
    if (!this.arqueoAccount) {
      this.arqueoError.set('Selecciona la cuenta.');
      return;
    }
    this.arqueoSaving.set(true);
    this.arqueoError.set('');
    this.water.createClosing({
      cash_account_id: this.arqueoAccount,
      closing_date: this.arqueoDate,
      counted_balance: this.arqueoCounted,
      notes: this.arqueoNotes || null,
    }).subscribe({
      next: () => {
        this.arqueoSaving.set(false);
        this.closeArqueo();
        this.notify.show({ type: 'success', title: 'Arqueo guardado', message: 'Arqueo registrado.' });
        this.loadClosings();
      },
      error: (err) => {
        this.arqueoSaving.set(false);
        this.arqueoError.set(err?.error?.detail || 'Error al guardar el arqueo.');
      },
    });
  }

  movBadge(type: string): string {
    return type === 'income'
      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300'
      : 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
  }

  private emptyMovement(): WaterTreasuryMovementCreate {
    return {
      cash_account_id: '',
      movement_date: new Date().toISOString().slice(0, 10),
      type: 'expense',
      category: 'other',
      amount: 0,
      description: '',
    };
  }
}
