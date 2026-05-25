import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterExtrasService } from '../../../core/services/water-extras.service';
import { WaterAuditEntry } from '../../../core/models/water-phase6.model';

@Component({
  selector: 'app-water-audit',
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-4 sm:p-6 lg:p-8">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">Auditoría</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Registro inmutable de cambios: quién, qué, cuándo, desde dónde.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-3 mb-4">
        <input [(ngModel)]="filterAction" (ngModelChange)="onChange()" placeholder="Filtrar por acción (ej: payment.registered)"
          class="flex-1 sm:max-w-xs h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
        <input [(ngModel)]="filterResource" (ngModelChange)="onChange()" placeholder="Tipo de recurso (water_payment, water_invoice_batch...)"
          class="flex-1 sm:max-w-xs h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (entries().length === 0) {
        <div class="rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-10 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No hay entradas que coincidan.</p>
        </div>
      } @else {
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-700/30">
              <tr class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3">Actor</th>
                <th class="px-4 py-3">Acción</th>
                <th class="px-4 py-3">Recurso</th>
                <th class="px-4 py-3">Detalles</th>
                <th class="px-4 py-3">IP</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              @for (e of entries(); track e.id) {
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                  <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">{{ e.created_at | date:'short' }}</td>
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ e.actor_name || '—' }}</td>
                  <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">{{ e.action }}</span>
                  </td>
                  <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                    @if (e.resource_type) {
                      <div>{{ e.resource_type }}</div>
                      @if (e.resource_id) {
                        <div class="font-mono text-[10px] text-gray-400 truncate max-w-[12rem]">{{ e.resource_id }}</div>
                      }
                    } @else { — }
                  </td>
                  <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 max-w-md">
                    @if (e.details) {
                      <pre class="font-mono text-[10px] whitespace-pre-wrap break-all">{{ formatDetails(e.details) }}</pre>
                    } @else { — }
                  </td>
                  <td class="px-4 py-3 text-xs text-gray-400 font-mono">{{ e.ip_address || '—' }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class WaterAuditComponent implements OnInit {
  private readonly extras = inject(WaterExtrasService);

  loading = signal(true);
  entries = signal<WaterAuditEntry[]>([]);
  filterAction = '';
  filterResource = '';
  private t: any;

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.extras.listAudit({
      action: this.filterAction || undefined,
      resource_type: this.filterResource || undefined,
      limit: 200,
    }).subscribe({
      next: (data) => { this.entries.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  onChange(): void {
    clearTimeout(this.t);
    this.t = setTimeout(() => this.load(), 300);
  }

  formatDetails(d: Record<string, any>): string {
    return Object.entries(d).map(([k, v]) => `${k}: ${v}`).join('  ·  ');
  }
}
