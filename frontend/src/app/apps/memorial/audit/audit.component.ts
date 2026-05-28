import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import { AuditLogEntry } from '../../../core/models/memorial.model';

@Component({
  selector: 'app-memorial-audit',
  imports: [CommonModule, FormsModule, DatePipe],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-6">
      <header>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Auditoría</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">Trazabilidad de acciones críticas en SavvyMemorial.</p>
      </header>

      <section class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Acción</span>
          <input [(ngModel)]="filterAction" (keyup.enter)="refresh()"
            placeholder="ej: service.created"
            class="w-48 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Tipo recurso</span>
          <select [(ngModel)]="filterResourceType" (change)="refresh()"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            <option value="">— Todos —</option>
            <option value="service">Servicio</option>
            <option value="contract">Contrato</option>
            <option value="invoice">Factura</option>
            <option value="payment">Pago</option>
            <option value="lead">Lead</option>
            <option value="employee">Empleado</option>
            <option value="inventory_movement">Movimiento inventario</option>
          </select>
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Desde</span>
          <input [(ngModel)]="dateFrom" type="date"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="flex flex-col text-xs text-slate-600 dark:text-slate-400">
          <span class="mb-1">Hasta</span>
          <input [(ngModel)]="dateTo" type="date"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <button (click)="refresh()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          Filtrar
        </button>
      </section>

      <section>
        @if (loading()) {
          <p class="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
        } @else if (entries().length === 0) {
          <div class="rounded-lg border border-dashed border-slate-300 dark:border-slate-700 p-8 text-center">
            <p class="text-sm text-slate-500 dark:text-slate-400">No hay registros de auditoría que coincidan.</p>
            <p class="text-xs text-slate-400 dark:text-slate-500 mt-2">
              Las entradas aparecen aquí cuando los módulos las registran mediante el helper <code class="font-mono">record_audit()</code>.
            </p>
          </div>
        } @else {
          <ol class="relative border-l-2 border-slate-200 dark:border-slate-700 ml-3 space-y-3">
            @for (e of entries(); track e.id) {
              <li class="ml-4">
                <span class="absolute -left-[7px] mt-1.5 w-3 h-3 rounded-full bg-brand-500 border-2 border-white dark:border-slate-900"></span>
                <div class="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 p-3">
                  <div class="flex flex-wrap items-baseline justify-between gap-2">
                    <h3 class="text-sm font-medium font-mono text-slate-900 dark:text-slate-100">{{ e.action }}</h3>
                    <time class="text-xs text-slate-500 dark:text-slate-400">{{ e.created_at | date:'medium' }}</time>
                  </div>
                  <div class="mt-1 text-xs text-slate-600 dark:text-slate-400 flex flex-wrap gap-3">
                    @if (e.resource_type) {
                      <span><span class="text-slate-400">recurso:</span> {{ e.resource_type }}</span>
                    }
                    @if (e.resource_id) {
                      <span class="font-mono"><span class="text-slate-400">id:</span> {{ e.resource_id }}</span>
                    }
                    @if (e.actor_user_id) {
                      <span class="font-mono"><span class="text-slate-400">actor:</span> {{ e.actor_user_id.slice(0, 8) }}…</span>
                    }
                    @if (e.ip_address) { <span><span class="text-slate-400">ip:</span> {{ e.ip_address }}</span> }
                  </div>
                  @if (e.details) {
                    <details class="mt-2">
                      <summary class="text-xs text-brand-600 cursor-pointer hover:underline">Ver detalles</summary>
                      <pre class="mt-2 text-xs bg-slate-50 dark:bg-slate-800 rounded p-2 overflow-x-auto">{{ stringify(e.details) }}</pre>
                    </details>
                  }
                </div>
              </li>
            }
          </ol>

          @if (entries().length >= pageSize) {
            <div class="mt-4 flex justify-center">
              <button (click)="loadMore()" type="button"
                class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800">
                Cargar más
              </button>
            </div>
          }
        }
      </section>
    </div>
  `,
})
export class MemorialAuditComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);

  entries = signal<AuditLogEntry[]>([]);
  loading = signal(false);
  offset = signal(0);
  readonly pageSize = 100;

  filterAction = '';
  filterResourceType = '';
  dateFrom = '';
  dateTo = '';

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.offset.set(0);
    this.entries.set([]);
    this.load(true);
  }

  loadMore(): void {
    this.offset.set(this.offset() + this.pageSize);
    this.load(false);
  }

  private load(replace: boolean): void {
    this.loading.set(true);
    const params: Record<string, string | number> = {
      limit: this.pageSize, offset: this.offset(),
    };
    if (this.filterAction) params['action'] = this.filterAction;
    if (this.filterResourceType) params['resource_type'] = this.filterResourceType;
    if (this.dateFrom) params['date_from'] = new Date(this.dateFrom).toISOString();
    if (this.dateTo) {
      const end = new Date(this.dateTo);
      end.setHours(23, 59, 59);
      params['date_to'] = end.toISOString();
    }
    this.memorial.listAudit(params).subscribe({
      next: (r) => {
        this.entries.set(replace ? r : [...this.entries(), ...r]);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  stringify(d: unknown): string {
    return JSON.stringify(d, null, 2);
  }
}
