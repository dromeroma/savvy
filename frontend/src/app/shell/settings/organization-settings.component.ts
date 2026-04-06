import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface OrgResponse {
  id: string;
  name: string;
  slug: string;
  type: string;
  settings: Record<string, unknown>;
}

@Component({
  selector: 'app-organization-settings',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <!-- Header -->
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Configuración</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Ajustes generales de la organización
        </p>
      </div>

      <!-- Loading -->
      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div
            class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"
          ></div>
        </div>
      } @else {
        <!-- Org Info Card -->
        <div
          class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h3 class="text-base font-semibold text-gray-800 dark:text-white/90 mb-4">
            Información de la organización
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1"
                >Nombre</label
              >
              <input
                type="text"
                [(ngModel)]="orgName"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1"
                >Slug</label
              >
              <input
                type="text"
                [value]="orgSlug()"
                disabled
                class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-500 dark:text-gray-400 cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        <!-- Fiscal Period Mode Card -->
        <div
          class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h3 class="text-base font-semibold text-gray-800 dark:text-white/90 mb-1">
            Modo de periodos fiscales
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-5">
            Define cómo se gestionan los periodos contables cuando tienes varios aplicativos
            activos.
          </p>

          <div class="space-y-3">
            <!-- Option: per_app -->
            <label
              class="flex items-start gap-4 p-4 rounded-lg border cursor-pointer transition-all"
              [ngClass]="{
                'border-brand-500 bg-brand-50 dark:bg-brand-500/10': fiscalMode() === 'per_app',
                'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600':
                  fiscalMode() !== 'per_app'
              }"
            >
              <input
                type="radio"
                name="fiscal_mode"
                value="per_app"
                [checked]="fiscalMode() === 'per_app'"
                (change)="fiscalMode.set('per_app')"
                class="mt-0.5 accent-brand-500"
              />
              <div>
                <span class="block text-sm font-semibold text-gray-800 dark:text-white/90">
                  Independiente por aplicativo
                </span>
                <span class="block text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Cada aplicativo (Iglesia, POS, etc.) maneja sus propios periodos fiscales. Puedes
                  cerrar el periodo de un aplicativo sin afectar a los demás.
                </span>
              </div>
            </label>

            <!-- Option: unified -->
            <label
              class="flex items-start gap-4 p-4 rounded-lg border cursor-pointer transition-all"
              [ngClass]="{
                'border-brand-500 bg-brand-50 dark:bg-brand-500/10': fiscalMode() === 'unified',
                'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600':
                  fiscalMode() !== 'unified'
              }"
            >
              <input
                type="radio"
                name="fiscal_mode"
                value="unified"
                [checked]="fiscalMode() === 'unified'"
                (change)="fiscalMode.set('unified')"
                class="mt-0.5 accent-brand-500"
              />
              <div>
                <span class="block text-sm font-semibold text-gray-800 dark:text-white/90">
                  Unificado
                </span>
                <span class="block text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Todos los aplicativos comparten un único periodo fiscal. Al cerrar un periodo, se
                  cierra para toda la organización.
                </span>
              </div>
            </label>
          </div>
        </div>

        <!-- Save button -->
        <div class="flex justify-end">
          <button
            (click)="save()"
            [disabled]="saving()"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            @if (saving()) {
              <div
                class="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"
              ></div>
              Guardando...
            } @else {
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
                <path
                  d="M17 21V13H7V21M7 3V8H15M19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16L21 8V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21Z"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              Guardar cambios
            }
          </button>
        </div>
      }
    </div>
  `,
})
export class OrganizationSettingsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  saving = signal(false);
  orgName = '';
  orgSlug = signal('');
  fiscalMode = signal<'per_app' | 'unified'>('per_app');

  private currentSettings: Record<string, unknown> = {};

  ngOnInit(): void {
    this.loadOrg();
  }

  private loadOrg(): void {
    this.api.get<OrgResponse>('/organizations/me').subscribe({
      next: (org) => {
        this.orgName = org.name;
        this.orgSlug.set(org.slug);
        this.currentSettings = org.settings || {};
        this.fiscalMode.set(
          (this.currentSettings['fiscal_period_mode'] as 'per_app' | 'unified') || 'per_app',
        );
        this.loading.set(false);
      },
      error: () => {
        this.notify.show({ type: 'error', title: 'Error', message: 'Error al cargar la configuración' });
        this.loading.set(false);
      },
    });
  }

  save(): void {
    this.saving.set(true);

    const mergedSettings = {
      ...this.currentSettings,
      fiscal_period_mode: this.fiscalMode(),
    };

    this.api
      .patch<OrgResponse>('/organizations/me', {
        name: this.orgName,
        settings: mergedSettings,
      })
      .subscribe({
        next: (org) => {
          this.currentSettings = org.settings || {};
          this.notify.show({ type: 'success', title: 'Guardado', message: 'Configuración guardada correctamente' });
          this.saving.set(false);
        },
        error: () => {
          this.notify.show({ type: 'error', title: 'Error', message: 'Error al guardar la configuración' });
          this.saving.set(false);
        },
      });
  }
}
