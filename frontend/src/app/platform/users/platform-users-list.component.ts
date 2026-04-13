import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface PlatformUser {
  id: string;
  name: string;
  email: string;
  created_at: string;
  last_login_at: string | null;
  organization_count: number;
  platform_roles: string[];
}

interface PlatformRole {
  id: string;
  code: string;
  name: string;
  description: string | null;
}

@Component({
  selector: 'app-platform-users-list',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Usuarios de plataforma</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Todos los usuarios del ecosistema Savvy</p>
        </div>
      </div>

      <div class="flex gap-3 mb-4">
        <input [(ngModel)]="search" (ngModelChange)="debouncedLoad()" placeholder="Buscar por nombre o email..."
          class="flex-1 sm:max-w-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-4 py-2 text-sm" />
        <select [(ngModel)]="roleFilter" (ngModelChange)="load()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos</option>
          <option value="with">Con rol de plataforma</option>
          <option value="without">Sin rol de plataforma</option>
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
                  <th class="px-4 py-3 font-medium text-gray-500">Usuario</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Email</th>
                  <th class="px-4 py-3 font-medium text-gray-500 text-right">Orgs</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Roles de plataforma</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Último login</th>
                  <th class="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                @for (u of users(); track u.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50">
                    <td class="px-4 py-3">
                      <p class="font-medium text-gray-800 dark:text-white/90">{{ u.name }}</p>
                    </td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400 font-mono text-xs">{{ u.email }}</td>
                    <td class="px-4 py-3 text-right font-mono text-gray-700 dark:text-gray-300">{{ u.organization_count }}</td>
                    <td class="px-4 py-3">
                      @if (u.platform_roles.length > 0) {
                        <div class="flex flex-wrap gap-1">
                          @for (r of u.platform_roles; track r) {
                            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-brand-100 dark:bg-brand-500/20 text-brand-700 dark:text-brand-400">
                              {{ r }}
                              <button (click)="revoke(u, r)" class="hover:text-error-600 transition">×</button>
                            </span>
                          }
                        </div>
                      } @else {
                        <span class="text-xs text-gray-400">—</span>
                      }
                    </td>
                    <td class="px-4 py-3 text-xs text-gray-500">{{ u.last_login_at ? (u.last_login_at | date:'short') : 'Nunca' }}</td>
                    <td class="px-4 py-3 text-right">
                      <button (click)="openGrant(u)" class="text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline">
                        Asignar rol
                      </button>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (users().length === 0) {
            <div class="text-center py-12">
              <p class="text-sm text-gray-400">No hay usuarios.</p>
            </div>
          }
        </div>
      }

      <!-- Grant modal -->
      @if (grantingUser()) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Asignar rol a {{ grantingUser()!.name }}</h3>
            </div>
            <div class="p-6 space-y-3">
              <select [(ngModel)]="selectedRoleCode" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
                @for (r of platformRoles(); track r.id) {
                  <option [value]="r.code">{{ r.name }} — {{ r.description }}</option>
                }
              </select>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="grantingUser.set(null)" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="confirmGrant()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Asignar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PlatformUsersListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  users = signal<PlatformUser[]>([]);
  platformRoles = signal<PlatformRole[]>([]);

  grantingUser = signal<PlatformUser | null>(null);
  selectedRoleCode = 'support';

  search = '';
  roleFilter = '';
  private loadTimeout: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.load();
    this.api.get<PlatformRole[]>('/platform/roles').subscribe({
      next: (r) => this.platformRoles.set(r),
    });
  }

  debouncedLoad(): void {
    if (this.loadTimeout) clearTimeout(this.loadTimeout);
    this.loadTimeout = setTimeout(() => this.load(), 250);
  }

  load(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.search) params['search'] = this.search;
    if (this.roleFilter === 'with') params['with_platform_role'] = 'true';
    if (this.roleFilter === 'without') params['with_platform_role'] = 'false';
    this.api.get<PlatformUser[]>('/platform/users', params).subscribe({
      next: (list) => {
        this.users.set(list);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  openGrant(u: PlatformUser): void {
    this.grantingUser.set(u);
    this.selectedRoleCode = 'support';
  }

  confirmGrant(): void {
    const u = this.grantingUser();
    if (!u) return;
    this.api.post('/platform/roles/grant', {
      user_id: u.id,
      role_code: this.selectedRoleCode,
    }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Asignado', message: `${this.selectedRoleCode} → ${u.name}` });
        this.grantingUser.set(null);
        this.load();
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo asignar',
      }),
    });
  }

  revoke(u: PlatformUser, roleCode: string): void {
    if (!confirm(`¿Revocar rol "${roleCode}" a ${u.name}?`)) return;
    this.api.delete('/platform/roles/revoke', {
      user_id: u.id,
      role_code: roleCode,
    }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Revocado', message: `${roleCode} eliminado` });
        this.load();
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo revocar',
      }),
    });
  }
}
