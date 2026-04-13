import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface SubscriptionRow {
  id: string;
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  plan_code: string;
  plan_name: string;
  status: string;
  billing_cycle: string;
  started_at: string | null;
  expires_at: string | null;
  trial_ends_at: string | null;
  price_monthly: number;
  price_yearly: number;
}

@Component({
  selector: 'app-platform-subscriptions-list',
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Suscripciones</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Estado de las suscripciones de todas las empresas</p>
        </div>
      </div>

      <div class="flex gap-3 mb-4">
        <select [(ngModel)]="statusFilter" (ngModelChange)="load()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          <option value="trial">Trial</option>
          <option value="active">Activa</option>
          <option value="past_due">Pago pendiente</option>
          <option value="suspended">Suspendida</option>
          <option value="cancelled">Cancelada</option>
        </select>
        <select [(ngModel)]="planFilter" (ngModelChange)="load()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos los planes</option>
          <option value="starter">Starter</option>
          <option value="professional">Professional</option>
          <option value="enterprise">Enterprise</option>
          <option value="platform">Platform</option>
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
                  <th class="px-4 py-3 font-medium text-gray-500">Plan</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Estado</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Ciclo</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Desde</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Próximo pago</th>
                  <th class="px-4 py-3 font-medium text-gray-500 text-right">Precio</th>
                  <th class="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                @for (s of subscriptions(); track s.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50">
                    <td class="px-4 py-3">
                      <a [routerLink]="['/platform/organizations', s.organization_id]" class="font-medium text-gray-800 dark:text-white/90 hover:text-brand-600 dark:hover:text-brand-400">
                        {{ s.organization_name }}
                      </a>
                      <p class="text-xs text-gray-500 font-mono">{{ s.organization_slug }}</p>
                    </td>
                    <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ s.plan_name }}</td>
                    <td class="px-4 py-3">
                      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" [ngClass]="statusBadgeClass(s.status)">
                        {{ statusLabel(s.status) }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400 capitalize">{{ s.billing_cycle }}</td>
                    <td class="px-4 py-3 text-xs text-gray-500">{{ s.started_at }}</td>
                    <td class="px-4 py-3 text-xs text-gray-500">{{ s.expires_at || s.trial_ends_at || '—' }}</td>
                    <td class="px-4 py-3 text-right font-mono text-gray-700 dark:text-gray-300">
                      $ {{ s.billing_cycle === 'yearly' ? s.price_yearly : s.price_monthly }}
                    </td>
                    <td class="px-4 py-3 text-right">
                      <div class="flex gap-1 justify-end">
                        @if (s.status !== 'active') {
                          <button (click)="activate(s.id)" class="text-[10px] px-2 py-1 rounded-full bg-success-100 dark:bg-success-500/20 text-success-700 dark:text-success-400 hover:opacity-80">
                            Activar
                          </button>
                        }
                        @if (s.status !== 'suspended') {
                          <button (click)="suspend(s.id)" class="text-[10px] px-2 py-1 rounded-full bg-warning-100 dark:bg-warning-500/20 text-warning-700 dark:text-warning-400 hover:opacity-80">
                            Suspender
                          </button>
                        }
                      </div>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (subscriptions().length === 0) {
            <div class="text-center py-12">
              <p class="text-sm text-gray-400">No hay suscripciones que coincidan.</p>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class SubscriptionsListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  subscriptions = signal<SubscriptionRow[]>([]);
  statusFilter = '';
  planFilter = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.statusFilter) params['status'] = this.statusFilter;
    if (this.planFilter) params['plan_code'] = this.planFilter;
    this.api.get<SubscriptionRow[]>('/platform/subscriptions', params).subscribe({
      next: (rows) => {
        this.subscriptions.set(rows);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  activate(id: string): void {
    this.api.post(`/platform/subscriptions/${id}/activate`, {}).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Activada', message: 'Suscripción activada' });
        this.load();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo activar' }),
    });
  }

  suspend(id: string): void {
    if (!confirm('¿Suspender esta suscripción? La empresa perderá acceso.')) return;
    this.api.post(`/platform/subscriptions/${id}/suspend`, {}).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Suspendida', message: 'Suscripción suspendida' });
        this.load();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo suspender' }),
    });
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

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Activa', trial: 'Trial', past_due: 'Vencida',
      suspended: 'Suspendida', cancelled: 'Cancelada',
    };
    return labels[status] || status;
  }
}
