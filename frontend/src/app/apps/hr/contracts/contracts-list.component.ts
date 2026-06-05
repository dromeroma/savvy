import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import { HrContract, HrEmployeeListItem } from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

@Component({
  selector: 'app-hr-contracts-list',
  imports: [CommonModule, FormsModule, RouterLink, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Contratos</h1>
        <p class="text-sm text-slate-600 dark:text-slate-400">
          Vista global de contratos laborales. Para crear uno nuevo, hazlo desde la ficha del empleado.
        </p>
      </header>

      <section class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Estado</span>
          <select [(ngModel)]="filterStatus" (change)="load()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            <option value="active">Activo</option>
            <option value="draft">Borrador</option>
            <option value="suspended">Suspendido</option>
            <option value="terminated">Terminado</option>
            <option value="expired">Expirado</option>
          </select>
        </label>
        <button (click)="load()" type="button"
          class="rounded-md border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-700 dark:text-slate-300">
          Refrescar
        </button>
      </section>

      <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
            <tr>
              <th class="text-left px-4 py-2 font-medium">Número</th>
              <th class="text-left px-4 py-2 font-medium">Empleado</th>
              <th class="text-left px-4 py-2 font-medium">Tipo</th>
              <th class="text-left px-4 py-2 font-medium">Inicio</th>
              <th class="text-left px-4 py-2 font-medium">Fin</th>
              <th class="text-right px-4 py-2 font-medium">Salario</th>
              <th class="text-left px-4 py-2 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            @if (loading()) {
              <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
            } @else if (contracts().length === 0) {
              <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin contratos.</td></tr>
            } @else {
              @for (c of paginated(); track c.id) {
                <tr>
                  <td class="px-4 py-2 font-mono text-xs">{{ c.contract_number }}</td>
                  <td class="px-4 py-2">
                    <a [routerLink]="['/hr/employees', c.employee_id]" class="text-brand-700 dark:text-brand-300 hover:underline">
                      {{ employeeName(c.employee_id) }}
                    </a>
                  </td>
                  <td class="px-4 py-2 text-xs">{{ typeLabel(c.contract_type) }}</td>
                  <td class="px-4 py-2 text-xs">{{ c.start_date }}</td>
                  <td class="px-4 py-2 text-xs">{{ c.end_date || '—' }}</td>
                  <td class="px-4 py-2 text-right font-mono text-xs">
                    {{ c.currency }} {{ (+c.base_salary) | number:'1.0-0' }}
                  </td>
                  <td class="px-4 py-2">
                    <span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(c.status)">{{ c.status }}</span>
                  </td>
                </tr>
              }
            }
          </tbody>
        </table>
        <app-pagination [totalItems]="contracts().length" [(page)]="page" [(pageSize)]="pageSize" />
      </section>
    </div>
  `,
})
export class HrContractsListComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  contracts = signal<HrContract[]>([]);
  employees = signal<HrEmployeeListItem[]>([]);

  filterStatus = '';

  page = signal(0);
  pageSize = signal(20);
  paginated = computed(() => {
    const s = this.page() * this.pageSize();
    return this.contracts().slice(s, s + this.pageSize());
  });

  constructor() {
    effect(() => { this.contracts(); this.page.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    this.load();
    this.hr.listEmployees().subscribe({ next: (r) => this.employees.set(r) });
  }

  load(): void {
    this.loading.set(true);
    const params: { status?: string } = {};
    if (this.filterStatus) params.status = this.filterStatus;
    this.hr.listContracts(params).subscribe({
      next: (r) => { this.contracts.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }); },
    });
  }

  employeeName(id: string): string {
    const e = this.employees().find((x) => x.id === id);
    if (!e) return id.slice(0, 8);
    return `${e.first_name} ${e.last_name || ''}`.trim();
  }

  typeLabel(t: string): string {
    const map: Record<string, string> = {
      indefinido: 'Indefinido', fijo: 'Término fijo', obra_labor: 'Obra/labor',
      prestacion: 'Prestación', aprendiz: 'Aprendizaje', practicante: 'Practicante', otro: 'Otro',
    };
    return map[t] || t;
  }

  statusClass(s: string): string {
    const map: Record<string, string> = {
      active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      suspended: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      terminated: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      expired: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    };
    return map[s] || '';
  }
}
