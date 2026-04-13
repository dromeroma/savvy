import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface Subscription {
  id: string;
  plan_id: string;
  status: string;
  billing_cycle: string;
  started_at: string;
  expires_at: string | null;
  trial_ends_at: string | null;
  auto_renew: boolean;
}

interface OrgDetail {
  id: string;
  name: string;
  slug: string;
  type: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  member_count: number;
  subscription: Subscription | null;
  plan_name: string | null;
}

interface Plan {
  id: string;
  code: string;
  name: string;
  price_monthly: number;
}

@Component({
  selector: 'app-platform-org-detail',
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="max-w-4xl">
      @if (org()) {
        <div class="mb-6">
          <a routerLink="/platform/organizations" class="text-xs text-gray-500 hover:text-brand-600 transition">← Volver a organizaciones</a>
          <div class="flex items-start justify-between mt-2 gap-4">
            <div>
              <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">{{ org()!.name }}</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400 font-mono">{{ org()!.slug }} · {{ org()!.type }}</p>
            </div>
            @if (org()!.type !== 'platform') {
              <button (click)="confirmDelete()" class="px-3 py-1.5 text-xs rounded-lg border border-red-400 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition">
                Eliminar empresa
              </button>
            }
          </div>
        </div>

        <!-- Tabs -->
        <div class="flex gap-1 mb-4 border-b border-gray-200 dark:border-gray-700">
          @for (tab of tabs; track tab.id) {
            <button (click)="activeTab.set(tab.id)"
              class="px-4 py-2 text-sm font-medium transition"
              [ngClass]="activeTab() === tab.id
                ? 'text-brand-600 dark:text-brand-400 border-b-2 border-brand-500'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
              {{ tab.label }}
            </button>
          }
        </div>

        @if (activeTab() === 'general') {
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-4">Datos de registro</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Nombre</label>
                <input type="text" [(ngModel)]="editForm.name"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Slug</label>
                <input type="text" [(ngModel)]="editForm.slug"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm font-mono" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Tipo</label>
                <select [(ngModel)]="editForm.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
                  <option value="business">Empresa</option>
                  <option value="personal">Personal</option>
                  <option value="demo">Demo</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Miembros</label>
                <input type="text" [value]="org()!.member_count" disabled
                  class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 px-3 py-2 text-sm" />
              </div>
            </div>
            <div class="mt-6 flex justify-end">
              <button (click)="save()" [disabled]="saving()"
                class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white transition">
                @if (saving()) { Guardando... } @else { Guardar cambios }
              </button>
            </div>
          </div>
        }

        @if (activeTab() === 'subscription') {
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            @if (org()!.subscription) {
              <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-4">Suscripción actual</h3>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide">Plan</p>
                  <p class="text-lg font-bold text-gray-800 dark:text-white/90">{{ org()!.plan_name }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide">Estado</p>
                  <p class="text-lg font-bold capitalize" [ngClass]="statusColor(org()!.subscription!.status)">
                    {{ statusLabel(org()!.subscription!.status) }}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide">Ciclo de facturación</p>
                  <p class="text-lg font-bold text-gray-800 dark:text-white/90 capitalize">{{ org()!.subscription!.billing_cycle }}</p>
                </div>
              </div>

              <div class="flex flex-wrap gap-2 mb-6">
                @if (org()!.subscription!.status !== 'active') {
                  <button (click)="activateSubscription()" class="px-3 py-1.5 text-xs rounded-lg bg-success-500 hover:bg-success-600 text-white transition">
                    Activar
                  </button>
                }
                @if (org()!.subscription!.status !== 'suspended') {
                  <button (click)="suspendSubscription()" class="px-3 py-1.5 text-xs rounded-lg border border-warning-400 text-warning-600 hover:bg-warning-50 dark:hover:bg-warning-900/20 transition">
                    Suspender
                  </button>
                }
              </div>

              <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">Cambiar plan</h4>
                <div class="flex gap-2">
                  <select [(ngModel)]="newPlanCode" class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
                    @for (p of plans(); track p.id) {
                      <option [value]="p.code">{{ p.name }} — $ {{ p.price_monthly }} / mes</option>
                    }
                  </select>
                  <button (click)="changePlan()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
                    Cambiar
                  </button>
                </div>
              </div>
            } @else {
              <p class="text-sm text-gray-500 mb-4">Esta empresa no tiene suscripción activa.</p>
              <div class="flex gap-2">
                <select [(ngModel)]="newPlanCode" class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
                  @for (p of plans(); track p.id) {
                    <option [value]="p.code">{{ p.name }}</option>
                  }
                </select>
                <button (click)="assignPlan()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
                  Asignar plan
                </button>
              </div>
            }
          </div>
        }
      } @else if (loading()) {
        <div class="flex items-center justify-center py-24">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      }
    </div>
  `,
})
export class OrganizationDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  saving = signal(false);
  org = signal<OrgDetail | null>(null);
  plans = signal<Plan[]>([]);
  activeTab = signal<'general' | 'subscription'>('general');
  newPlanCode = 'starter';

  tabs = [
    { id: 'general' as const, label: 'General' },
    { id: 'subscription' as const, label: 'Suscripción' },
  ];

  editForm = { name: '', slug: '', type: 'business' };

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
    this.loadOrg(id);
    this.api.get<Plan[]>('/platform/plans').subscribe({
      next: (p) => this.plans.set(p),
    });
  }

  private loadOrg(id: string): void {
    this.loading.set(true);
    this.api.get<OrgDetail>(`/platform/organizations/${id}`).subscribe({
      next: (o) => {
        this.org.set(o);
        this.editForm = { name: o.name, slug: o.slug, type: o.type };
        if (o.subscription) {
          this.newPlanCode = this.plans().find(p => p.id === o.subscription!.plan_id)?.code || 'starter';
        }
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  save(): void {
    const org = this.org();
    if (!org) return;
    this.saving.set(true);
    this.api.patch<OrgDetail>(`/platform/organizations/${org.id}`, this.editForm).subscribe({
      next: (updated) => {
        this.saving.set(false);
        this.org.set(updated);
        this.notify.show({ type: 'success', title: 'Guardado', message: 'Empresa actualizada' });
      },
      error: (err) => {
        this.saving.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err.error?.detail || 'No se pudo actualizar',
        });
      },
    });
  }

  activateSubscription(): void {
    const sub = this.org()?.subscription;
    if (!sub) return;
    this.api.post(`/platform/subscriptions/${sub.id}/activate`, {}).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Activada', message: 'Suscripción activada' });
        this.loadOrg(this.org()!.id);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo activar' }),
    });
  }

  suspendSubscription(): void {
    const sub = this.org()?.subscription;
    if (!sub) return;
    if (!confirm('¿Suspender la suscripción de esta empresa? Perderán acceso.')) return;
    this.api.post(`/platform/subscriptions/${sub.id}/suspend`, {}).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Suspendida', message: 'Suscripción suspendida' });
        this.loadOrg(this.org()!.id);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo suspender' }),
    });
  }

  changePlan(): void {
    const sub = this.org()?.subscription;
    if (!sub) return;
    this.api.patch(`/platform/subscriptions/${sub.id}`, { plan_code: this.newPlanCode }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Plan actualizado', message: `Cambiado a ${this.newPlanCode}` });
        this.loadOrg(this.org()!.id);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cambiar el plan' }),
    });
  }

  assignPlan(): void {
    const org = this.org();
    if (!org) return;
    this.api.post('/platform/subscriptions', {
      organization_id: org.id,
      plan_code: this.newPlanCode,
      status: 'active',
      billing_cycle: 'monthly',
    }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Asignado', message: 'Plan asignado' });
        this.loadOrg(org.id);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo asignar' }),
    });
  }

  confirmDelete(): void {
    const org = this.org();
    if (!org) return;
    if (!confirm(`¿Eliminar "${org.name}"? Esta acción es reversible solo por soporte.`)) return;
    this.api.delete(`/platform/organizations/${org.id}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminada', message: org.name });
        this.router.navigate(['/platform/organizations']);
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo eliminar',
      }),
    });
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Activa', trial: 'Trial', past_due: 'Vencida',
      suspended: 'Suspendida', cancelled: 'Cancelada',
    };
    return labels[status] || status;
  }

  statusColor(status: string): string {
    switch (status) {
      case 'active':    return 'text-success-600 dark:text-success-400';
      case 'trial':     return 'text-brand-600 dark:text-brand-400';
      case 'suspended': return 'text-warning-600 dark:text-warning-400';
      case 'cancelled': return 'text-error-600 dark:text-error-400';
      default:          return 'text-gray-600 dark:text-gray-400';
    }
  }
}
