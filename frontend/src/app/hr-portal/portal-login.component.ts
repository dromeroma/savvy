import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HrPortalService } from './portal.service';

@Component({
  selector: 'app-hr-portal-login',
  imports: [CommonModule, FormsModule],
  template: `
    <main class="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center px-4 py-10">
      <div class="w-full max-w-md">
        <div class="text-center mb-6">
          <h1 class="text-3xl font-semibold text-slate-900 dark:text-slate-100">Portal del empleado</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Consulta tus desprendibles, solicita vacaciones y completa tus evaluaciones.</p>
        </div>

        <form (ngSubmit)="login()" class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6 space-y-4">
          <label class="block">
            <span class="text-xs text-slate-600 dark:text-slate-400">Empresa (slug)</span>
            <input [(ngModel)]="orgSlug" name="org_slug" required
              placeholder="ej: memorial-demo"
              class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
          </label>

          <label class="block">
            <span class="text-xs text-slate-600 dark:text-slate-400">Código de empleado</span>
            <input [(ngModel)]="employeeCode" name="employee_code" required
              placeholder="ej: EMP-001"
              class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm uppercase" />
          </label>

          <label class="block">
            <span class="text-xs text-slate-600 dark:text-slate-400">Número de documento</span>
            <input [(ngModel)]="documentNumber" name="document_number" required
              class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
          </label>

          @if (error()) {
            <p class="text-sm text-rose-600">{{ error() }}</p>
          }

          <button type="submit" [disabled]="loading()"
            class="w-full rounded-md bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
            {{ loading() ? 'Verificando...' : 'Ingresar' }}
          </button>

          <p class="text-xs text-slate-500 dark:text-slate-400 text-center pt-2">
            ¿Problemas para ingresar? Contacta a Recursos Humanos.
          </p>
        </form>
      </div>
    </main>
  `,
})
export class HrPortalLoginComponent {
  private readonly portal = inject(HrPortalService);
  private readonly router = inject(Router);

  orgSlug = '';
  employeeCode = '';
  documentNumber = '';
  loading = signal(false);
  error = signal('');

  login(): void {
    if (!this.orgSlug.trim() || !this.employeeCode.trim() || !this.documentNumber.trim()) {
      this.error.set('Completa todos los campos.');
      return;
    }
    this.error.set('');
    this.loading.set(true);
    this.portal
      .login({
        org_slug: this.orgSlug.trim(),
        employee_code: this.employeeCode.trim(),
        document_number: this.documentNumber.trim(),
      })
      .subscribe({
        next: (res) => {
          this.portal.saveToken(res.token, res.employee);
          this.loading.set(false);
          this.router.navigate(['/hr-portal/home']);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(err?.error?.detail || 'Credenciales no válidas.');
        },
      });
  }
}
