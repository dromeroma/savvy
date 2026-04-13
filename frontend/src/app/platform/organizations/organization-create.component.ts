import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface Plan {
  id: string;
  code: string;
  name: string;
  price_monthly: number;
  is_public: boolean;
}

@Component({
  selector: 'app-platform-org-create',
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="max-w-2xl">
      <div class="mb-6">
        <a routerLink="/platform/organizations" class="text-xs text-gray-500 hover:text-brand-600 transition">← Volver a organizaciones</a>
        <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90 mt-2">Nueva empresa</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Crea una organización con un dueño inicial y un plan de suscripción.</p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        <div class="space-y-4">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Datos de la empresa</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
              <input type="text" [(ngModel)]="form.name" (ngModelChange)="autoSlug()" placeholder="Mi Empresa S.A.S"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Slug *</label>
              <input type="text" [(ngModel)]="form.slug" placeholder="mi-empresa"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm font-mono" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Tipo</label>
            <select [(ngModel)]="form.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
              <option value="business">Empresa</option>
              <option value="personal">Personal</option>
              <option value="demo">Demo (pruebas)</option>
            </select>
          </div>

          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mt-6">Dueño inicial</h3>
          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre del dueño *</label>
            <input type="text" [(ngModel)]="form.owner_name" placeholder="Juan Pérez"
              class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Email *</label>
              <input type="email" [(ngModel)]="form.owner_email" placeholder="dueno@empresa.com"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Contraseña *</label>
              <input type="text" [(ngModel)]="form.owner_password" placeholder="Mínimo 8 caracteres"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm font-mono" />
            </div>
          </div>

          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mt-6">Plan de suscripción</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Plan *</label>
              <select [(ngModel)]="form.plan_code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
                @for (p of plans(); track p.id) {
                  <option [value]="p.code">{{ p.name }} — $ {{ p.price_monthly }} / mes</option>
                }
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Días de trial</label>
              <input type="number" [(ngModel)]="form.trial_days" min="0" max="365"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
            </div>
          </div>
        </div>

        <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <a routerLink="/platform/organizations"
            class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition">
            Cancelar
          </a>
          <button (click)="submit()" [disabled]="saving()"
            class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white transition">
            @if (saving()) { Creando... } @else { Crear empresa }
          </button>
        </div>
      </div>
    </div>
  `,
})
export class OrganizationCreateComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly notify = inject(NotificationService);

  plans = signal<Plan[]>([]);
  saving = signal(false);

  form = {
    name: '',
    slug: '',
    type: 'business' as const,
    owner_name: '',
    owner_email: '',
    owner_password: '',
    plan_code: 'starter',
    trial_days: 14,
  };

  constructor() {
    this.api.get<Plan[]>('/platform/plans').subscribe({
      next: (p) => this.plans.set(p.filter((x) => x.is_public !== false)),
    });
  }

  autoSlug(): void {
    if (!this.form.slug || this.form.slug === this.lastAuto) {
      const s = this.form.name
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
      this.form.slug = s;
      this.lastAuto = s;
    }
  }
  private lastAuto = '';

  submit(): void {
    if (
      !this.form.name ||
      !this.form.slug ||
      !this.form.owner_name ||
      !this.form.owner_email ||
      !this.form.owner_password
    ) {
      this.notify.show({ type: 'error', title: 'Faltan datos', message: 'Completa los campos obligatorios' });
      return;
    }
    this.saving.set(true);
    this.api.post<{ id: string }>('/platform/organizations', this.form).subscribe({
      next: (org) => {
        this.saving.set(false);
        this.notify.show({ type: 'success', title: 'Empresa creada', message: this.form.name });
        this.router.navigate(['/platform/organizations', org.id]);
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err.error?.detail || 'No se pudo crear la empresa';
        this.notify.show({ type: 'error', title: 'Error', message: detail });
      },
    });
  }
}
