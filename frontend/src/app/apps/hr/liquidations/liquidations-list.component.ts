import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import { LiquidationListItem } from '../../../core/models/hr.model';

const REASON_LABELS: Record<string, string> = {
  voluntary: 'Renuncia',
  mutual: 'Mutuo acuerdo',
  with_cause: 'Despido con causa',
  without_cause: 'Despido sin causa',
  end_of_contract: 'Fin de contrato',
  retirement: 'Pensión',
  death: 'Fallecimiento',
  other: 'Otra',
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador',
  finalized: 'Finalizada',
  paid: 'Pagada',
  cancelled: 'Cancelada',
};

@Component({
  selector: 'app-hr-liquidations-list',
  imports: [CommonModule, FormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-4">
      <header class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Liquidaciones</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Liquidaciones definitivas al terminar contratos laborales.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <select [(ngModel)]="statusFilter" (ngModelChange)="reload()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">Todos los estados</option>
            <option value="draft">Borrador</option>
            <option value="finalized">Finalizada</option>
            <option value="paid">Pagada</option>
            <option value="cancelled">Cancelada</option>
          </select>
          <a routerLink="../employees" class="rounded-md bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 text-sm font-medium">
            + Nueva (desde empleado)
          </a>
        </div>
      </header>

      @if (loading()) {
        <p class="text-sm text-slate-500 dark:text-slate-400">Cargando…</p>
      } @else if (items().length === 0) {
        <div class="text-center py-12 bg-slate-50 dark:bg-slate-900 rounded-lg border border-dashed border-slate-300 dark:border-slate-700">
          <p class="text-sm text-slate-500 dark:text-slate-400">Sin liquidaciones registradas.</p>
          <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">
            Para liquidar, entra al detalle de un empleado y usa el botón "Liquidar".
          </p>
        </div>
      } @else {
      <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-3 font-medium">N°</th>
              <th class="text-left px-4 py-3 font-medium">Empleado</th>
              <th class="text-left px-4 py-3 font-medium">Causa</th>
              <th class="text-left px-4 py-3 font-medium">Terminación</th>
              <th class="text-right px-4 py-3 font-medium">Neto</th>
              <th class="text-left px-4 py-3 font-medium">Estado</th>
              <th class="text-right px-4 py-3 font-medium">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @for (it of items(); track it.id) {
              <tr>
                <td class="px-4 py-3 font-mono text-xs">{{ it.liquidation_number }}</td>
                <td class="px-4 py-3">
                  <div class="font-medium">{{ it.employee_name }}</div>
                  <div class="text-xs text-slate-500 dark:text-slate-400 font-mono">{{ it.employee_code }}</div>
                </td>
                <td class="px-4 py-3 text-xs">{{ reasonLabel(it.termination_reason) }}</td>
                <td class="px-4 py-3 text-xs">{{ it.termination_date | date:'mediumDate' }}</td>
                <td class="px-4 py-3 text-right font-mono font-semibold text-emerald-700 dark:text-emerald-300">$ {{ fmt(it.net_amount) }}</td>
                <td class="px-4 py-3"><span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(it.status)">{{ statusLabel(it.status) }}</span></td>
                <td class="px-4 py-3 text-right">
                  <a [routerLink]="['..', 'liquidations', it.id]" class="text-xs text-brand-600 hover:underline">Ver detalle →</a>
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
      }
    </div>
  `,
})
export class HrLiquidationsListComponent implements OnInit {
  private readonly api = inject(HrApiService);

  loading = signal(true);
  items = signal<LiquidationListItem[]>([]);
  statusFilter = '';

  ngOnInit(): void { this.reload(); }

  reload(): void {
    this.loading.set(true);
    this.api.listLiquidations(this.statusFilter ? { status: this.statusFilter } : {}).subscribe({
      next: (r) => { this.items.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  reasonLabel(r: string): string { return REASON_LABELS[r] || r; }
  statusLabel(s: string): string { return STATUS_LABELS[s] || s; }
  statusClass(s: string): string {
    const map: Record<string, string> = {
      draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      finalized: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      paid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    };
    return map[s] || '';
  }
  fmt(v: string): string { return Number(v || 0).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 }); }
}
