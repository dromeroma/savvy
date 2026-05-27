import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MemorialPortalService } from './portal.service';

@Component({
  selector: 'app-memorial-portal-login',
  imports: [CommonModule, FormsModule],
  template: `
    <main class="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center px-4 py-10">
      <div class="w-full max-w-md">
        <div class="text-center mb-6">
          <h1 class="text-3xl font-semibold text-slate-900 dark:text-slate-100">Portal del afiliado</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Consulte su contrato exequial, cuotas y pagos.</p>
        </div>

        <form (ngSubmit)="login()" class="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6 space-y-4">
          <label class="block">
            <span class="text-xs text-slate-600 dark:text-slate-400">Funeraria (slug)</span>
            <input [(ngModel)]="orgSlug" name="org_slug" required
              placeholder="ej: memorial-demo"
              class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm" />
          </label>

          <label class="block">
            <span class="text-xs text-slate-600 dark:text-slate-400">Email del titular</span>
            <input [(ngModel)]="email" name="email" type="email"
              class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm" />
          </label>

          <div class="text-center text-xs text-slate-400">— o —</div>

          <label class="block">
            <span class="text-xs text-slate-600 dark:text-slate-400">Número de documento</span>
            <input [(ngModel)]="documentNumber" name="document_number"
              class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm" />
          </label>

          @if (error()) {
            <p class="text-sm text-rose-600">{{ error() }}</p>
          }

          <button type="submit" [disabled]="loading()"
            class="w-full rounded-md bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
            {{ loading() ? 'Verificando...' : 'Ingresar' }}
          </button>

          <p class="text-xs text-slate-500 dark:text-slate-400 text-center pt-2">
            ¿Problemas para ingresar? Contacte a la funeraria directamente.
          </p>
        </form>
      </div>
    </main>
  `,
})
export class MemorialPortalLoginComponent {
  private readonly portal = inject(MemorialPortalService);
  private readonly router = inject(Router);

  orgSlug = '';
  email = '';
  documentNumber = '';
  loading = signal(false);
  error = signal('');

  login(): void {
    if (!this.orgSlug.trim()) {
      this.error.set('Indique la funeraria.');
      return;
    }
    if (!this.email.trim() && !this.documentNumber.trim()) {
      this.error.set('Indique email o número de documento.');
      return;
    }
    this.error.set('');
    this.loading.set(true);
    this.portal
      .login({
        org_slug: this.orgSlug.trim(),
        email: this.email.trim() || undefined,
        document_number: this.documentNumber.trim() || undefined,
      })
      .subscribe({
        next: (res) => {
          this.portal.saveToken(res.token, res.contract);
          this.loading.set(false);
          this.router.navigate(['/memorial-portal/home']);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(err?.error?.detail || 'Credenciales no válidas.');
        },
      });
  }
}
