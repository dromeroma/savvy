import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';
import { ThemeToggleComponent } from '../../shared/components/common/theme-toggle/theme-toggle.component';

interface PlatformUser {
  id: string;
  name: string;
  email: string;
  platform_roles: string[];
}

@Component({
  selector: 'app-platform-layout',
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, ThemeToggleComponent],
  template: `
    <div class="flex h-screen bg-gray-50 dark:bg-gray-900">
      <!-- Sidebar -->
      <aside class="w-64 shrink-0 flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800">
        <!-- Brand header -->
        <div class="h-16 flex items-center gap-3 px-5 border-b border-gray-200 dark:border-gray-800">
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold text-sm">
            S
          </div>
          <div class="min-w-0">
            <p class="text-sm font-bold text-gray-800 dark:text-white/90 leading-tight truncate">Savvy Platform</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 leading-tight truncate">Panel Super Admin</p>
          </div>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 overflow-y-auto custom-scrollbar py-4 px-3 space-y-1">
          <p class="px-3 pb-2 text-[10px] uppercase tracking-wider font-semibold text-gray-400">Administración</p>

          @for (item of menu; track item.route) {
            <a [routerLink]="item.route" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-400"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
              <span class="text-base">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </a>
          }
        </nav>

        <!-- User block -->
        <div class="border-t border-gray-200 dark:border-gray-800 p-4">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-9 h-9 rounded-full bg-brand-100 dark:bg-brand-500/20 flex items-center justify-center text-sm font-bold text-brand-600 dark:text-brand-400">
              {{ userInitials }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-800 dark:text-white/90 truncate">{{ userName }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ userEmail }}</p>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <app-theme-toggle />
            <button (click)="logout()" class="text-xs text-gray-500 hover:text-red-600 dark:hover:text-red-400 transition">
              Cerrar sesión
            </button>
          </div>
        </div>
      </aside>

      <!-- Main content -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Topbar -->
        <header class="h-16 shrink-0 flex items-center justify-between px-6 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800">
          <div>
            <h1 class="text-lg font-semibold text-gray-800 dark:text-white/90">Savvy Platform</h1>
            <p class="text-xs text-gray-500 dark:text-gray-400">Administración global del ecosistema</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-500/20 text-xs font-medium text-brand-700 dark:text-brand-400">
              <span class="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse"></span>
              Super Admin
            </span>
          </div>
        </header>

        <main class="flex-1 overflow-y-auto custom-scrollbar p-6">
          <router-outlet />
        </main>
      </div>
    </div>
  `,
})
export class PlatformLayoutComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  userName = '';
  userEmail = '';
  userInitials = 'S';

  menu = [
    { icon: '📊', label: 'Dashboard', route: '/platform/dashboard' },
    { icon: '🏢', label: 'Organizaciones', route: '/platform/organizations' },
    { icon: '💳', label: 'Suscripciones', route: '/platform/subscriptions' },
    { icon: '📦', label: 'Planes', route: '/platform/plans' },
    { icon: '👥', label: 'Usuarios', route: '/platform/users' },
    { icon: '📜', label: 'Auditoría', route: '/platform/audit' },
  ];

  ngOnInit(): void {
    this.api.get<PlatformUser>('/auth/me').subscribe({
      next: (user) => {
        this.userName = user.name || 'Super Admin';
        this.userEmail = user.email || '';
        this.userInitials = this.getInitials(user.name);
      },
      error: () => {
        this.userName = 'Super Admin';
      },
    });
  }

  logout(): void {
    this.auth.logout();
  }

  private getInitials(name: string): string {
    if (!name) return 'S';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0].slice(0, 2).toUpperCase();
  }
}
