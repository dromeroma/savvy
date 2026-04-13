import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';

interface OrgSummary {
  id: string;
  name: string;
  slug: string;
  type: string;
  created_at: string;
  member_count: number;
  subscription_status: string | null;
  plan_name: string | null;
  plan_code: string | null;
}

@Component({
  selector: 'app-platform-organizations-list',
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Organizaciones</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Todas las empresas registradas en Savvy</p>
        </div>
        <a routerLink="/platform/organizations/new"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
          + Nueva empresa
        </a>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 mb-4">
        <input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar por nombre o slug..."
          class="flex-1 sm:max-w-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-4 py-2 text-sm" />
        <select [(ngModel)]="statusFilter" (ngModelChange)="load()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          <option value="trial">En trial</option>
          <option value="active">Activa</option>
          <option value="past_due">Pago pendiente</option>
          <option value="suspended">Suspendida</option>
          <option value="cancelled">Cancelada</option>
        </select>
        <select [(ngModel)]="typeFilter" (ngModelChange)="load()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos los tipos</option>
          <option value="business">Empresa</option>
          <option value="personal">Personal</option>
          <option value="demo">Demo</option>
          <option value="platform">Plataforma</option>
        </select>
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
                  <th class="px-4 py-3 font-medium text-gray-500">Empresa</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Tipo</th>
                  <th class="px-4 py-3 font-medium text-gray-500 text-right">Miembros</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Plan</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Estado</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Creada</th>
                  <th class="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                @for (org of organizations(); track org.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition">
                    <td class="px-4 py-3">
                      <div>
                        <p class="font-medium text-gray-800 dark:text-white/90">{{ org.name }}</p>
                        <p class="text-xs text-gray-500 font-mono">{{ org.slug }}</p>
                      </div>
                    </td>
                    <td class="px-4 py-3">
                      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize"
                        [ngClass]="typeBadgeClass(org.type)">
                        {{ org.type }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-right font-mono text-gray-700 dark:text-gray-300">{{ org.member_count }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ org.plan_name || '—' }}</td>
                    <td class="px-4 py-3">
                      @if (org.subscription_status) {
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                          [ngClass]="statusBadgeClass(org.subscription_status)">
                          {{ statusLabel(org.subscription_status) }}
                        </span>
                      } @else {
                        <span class="text-xs text-gray-400">Sin suscripción</span>
                      }
                    </td>
                    <td class="px-4 py-3 text-xs text-gray-500">{{ org.created_at | date:'shortDate' }}</td>
                    <td class="px-4 py-3 text-right">
                      <a [routerLink]="['/platform/organizations', org.id]"
                        class="text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline">
                        Ver →
                      </a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (organizations().length === 0) {
            <div class="text-center py-12">
              <p class="text-sm text-gray-400">No hay organizaciones que coincidan.</p>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class OrganizationsListComponent implements OnInit {
  private readonly api = inject(ApiService);

  loading = signal(true);
  organizations = signal<OrgSummary[]>([]);
  search = '';
  statusFilter = '';
  typeFilter = '';
  private loadTimeout: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    if (this.loadTimeout) clearTimeout(this.loadTimeout);
    this.loadTimeout = setTimeout(() => {
      this.loading.set(true);
      const params: Record<string, string> = {};
      if (this.search) params['search'] = this.search;
      if (this.statusFilter) params['status'] = this.statusFilter;
      if (this.typeFilter) params['type'] = this.typeFilter;
      this.api.get<OrgSummary[]>('/platform/organizations', params).subscribe({
        next: (list) => {
          this.organizations.set(list);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
    }, 200);
  }

  statusBadgeClass(status: string): string {
    switch (status) {
      case 'active':    return 'bg-success-100 text-success-700 dark:bg-success-500/20 dark:text-success-400';
      case 'trial':     return 'bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-400';
      case 'past_due':  return 'bg-warning-100 text-warning-700 dark:bg-warning-500/20 dark:text-warning-400';
      case 'suspended': return 'bg-warning-100 text-warning-700 dark:bg-warning-500/20 dark:text-warning-400';
      case 'cancelled': return 'bg-error-100 text-error-700 dark:bg-error-500/20 dark:text-error-400';
      default:          return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300';
    }
  }

  typeBadgeClass(type: string): string {
    switch (type) {
      case 'platform': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-400';
      case 'demo':     return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400';
      case 'business': return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
      default:         return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Activa',
      trial: 'Trial',
      past_due: 'Vencida',
      suspended: 'Suspendida',
      cancelled: 'Cancelada',
    };
    return labels[status] || status;
  }
}
