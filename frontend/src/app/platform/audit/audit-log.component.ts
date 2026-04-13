import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

interface AuditEntry {
  id: string;
  actor_user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  target_org_id: string | null;
  payload: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

@Component({
  selector: 'app-platform-audit-log',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Bitácora de auditoría</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Historial inmutable de acciones de plataforma</p>
      </div>

      <div class="flex gap-3 mb-4">
        <input [(ngModel)]="actionFilter" (ngModelChange)="debouncedLoad()" placeholder="Filtrar por acción (ej: plan.update)"
          class="flex-1 sm:max-w-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-4 py-2 text-sm font-mono" />
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500">Fecha</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Acción</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Recurso</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Payload</th>
                  <th class="px-4 py-3 font-medium text-gray-500">IP</th>
                </tr>
              </thead>
              <tbody>
                @for (e of entries(); track e.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50">
                    <td class="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{{ e.created_at | date:'short' }}</td>
                    <td class="px-4 py-3">
                      <span class="font-mono text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200">{{ e.action }}</span>
                    </td>
                    <td class="px-4 py-3 text-xs text-gray-600 dark:text-gray-400">
                      @if (e.resource_type) { {{ e.resource_type }} }
                      @if (e.resource_id) { <span class="font-mono text-[10px] text-gray-400">· {{ e.resource_id.slice(0, 8) }}</span> }
                    </td>
                    <td class="px-4 py-3">
                      @if (e.payload) {
                        <pre class="text-[10px] font-mono text-gray-500 dark:text-gray-400 max-w-xs overflow-x-auto">{{ e.payload | json }}</pre>
                      }
                    </td>
                    <td class="px-4 py-3 text-xs text-gray-500 font-mono">{{ e.ip_address || '—' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (entries().length === 0) {
            <div class="text-center py-12">
              <p class="text-sm text-gray-400">Sin entradas de auditoría.</p>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class AuditLogComponent implements OnInit {
  private readonly api = inject(ApiService);

  loading = signal(true);
  entries = signal<AuditEntry[]>([]);
  actionFilter = '';
  private timeout: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.load();
  }

  debouncedLoad(): void {
    if (this.timeout) clearTimeout(this.timeout);
    this.timeout = setTimeout(() => this.load(), 250);
  }

  load(): void {
    this.loading.set(true);
    const params: Record<string, string> = { limit: '200' };
    if (this.actionFilter) params['action'] = this.actionFilter;
    this.api.get<AuditEntry[]>('/platform/audit', params).subscribe({
      next: (list) => {
        this.entries.set(list);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
