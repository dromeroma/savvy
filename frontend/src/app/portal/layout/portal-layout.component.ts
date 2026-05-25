import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { PortalService } from '../../core/services/portal.service';
import { PortalMe } from '../../core/models/portal.model';
import { ThemeToggleComponent } from '../../shared/components/common/theme-toggle/theme-toggle.component';
import { NotificationBellComponent } from '../../shared/components/notification-bell/notification-bell.component';

@Component({
  selector: 'app-portal-layout',
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, ThemeToggleComponent, NotificationBellComponent],
  template: `
    <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
      <!-- Top bar -->
      <header class="sticky top-0 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-sky-500 to-cyan-600 flex items-center justify-center text-white text-base shrink-0">
              💧
            </div>
            <div class="min-w-0">
              @if (me()) {
                <p class="text-sm font-semibold text-gray-800 dark:text-white/90 truncate">{{ me()!.organization_name }}</p>
                <p class="text-[11px] text-gray-500 dark:text-gray-400 truncate">Portal del suscriptor</p>
              } @else {
                <p class="text-sm font-semibold text-gray-800 dark:text-white/90">SavvyWater · Portal</p>
              }
            </div>
          </div>
          <div class="flex items-center gap-2">
            <app-notification-bell />
            <app-theme-toggle />
            <button (click)="logout()" class="text-xs text-gray-500 hover:text-red-600 dark:hover:text-red-400 px-2 py-1">
              Cerrar sesión
            </button>
          </div>
        </div>

        <!-- Tabs -->
        <nav class="max-w-5xl mx-auto px-2 sm:px-6 flex gap-1 overflow-x-auto">
          @for (t of tabs; track t.route) {
            <a [routerLink]="t.route" routerLinkActive="border-sky-500 text-sky-700 dark:text-sky-300"
              [routerLinkActiveOptions]="{ exact: false }"
              class="px-3 py-2.5 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 transition whitespace-nowrap">
              {{ t.label }}
            </a>
          }
        </nav>
      </header>

      <main class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        @if (me()) {
          <div class="mb-5 text-sm text-gray-600 dark:text-gray-300">
            Hola, <span class="font-semibold text-gray-800 dark:text-white/90">{{ me()!.name }}</span>
            <span class="text-xs text-gray-400 ml-1">· {{ me()!.code }}</span>
          </div>
        }
        @if (errorMessage()) {
          <div class="rounded-xl border border-error-200 bg-error-50 dark:bg-error-500/10 dark:border-error-500/30 p-6 text-center">
            <p class="text-error-700 dark:text-error-400 mb-2">{{ errorMessage() }}</p>
            <button (click)="logout()" class="text-xs text-brand-500 underline">Cerrar sesión</button>
          </div>
        } @else {
          <router-outlet />
        }
      </main>
    </div>
  `,
})
export class PortalLayoutComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly portal = inject(PortalService);

  me = signal<PortalMe | null>(null);
  errorMessage = signal<string>('');

  readonly tabs = [
    { label: 'Inicio', route: '/portal/water/dashboard' },
    { label: 'Facturas', route: '/portal/water/invoices' },
    { label: 'Pagos', route: '/portal/water/payments' },
    { label: 'Consumo', route: '/portal/water/consumption' },
    { label: 'PQRS', route: '/portal/water/pqrs' },
  ];

  ngOnInit(): void {
    this.portal.me().subscribe({
      next: (m) => this.me.set(m),
      error: (err) => {
        this.errorMessage.set(
          err?.error?.detail ||
            'Tu usuario no está vinculado a un suscriptor del acueducto.',
        );
      },
    });
  }

  logout(): void {
    this.auth.logout();
  }
}
