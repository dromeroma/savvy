import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../shared/services/notification.service';

interface OrgResponse {
  id: string;
  name: string;
  slug: string;
  type: string;
  settings: Record<string, unknown>;
}

interface MyUser {
  id: string;
  name: string;
  email: string;
  platform_roles: string[];
}

interface OrgApp {
  app_code: string;
  app_name: string;
  is_active: boolean;
}

interface AppPermission {
  id: string;
  app_code: string;
  code: string;
  name: string;
  description: string | null;
  category: string | null;
}

interface CustomRole {
  id: string;
  app_code: string;
  code: string;
  name: string;
  description: string | null;
  permissions: string[];
  is_system: boolean;
  is_active: boolean;
}

type TabId = 'organization' | 'account' | 'custom_roles';

@Component({
  selector: 'app-organization-settings',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Configuración</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Ajustes de la organización y tu cuenta</p>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-4 border-b border-gray-200 dark:border-gray-700 overflow-x-auto custom-scrollbar">
        @for (tab of tabs; track tab.id) {
          <button (click)="selectTab(tab.id)"
            class="px-4 py-2 text-sm font-medium transition whitespace-nowrap"
            [ngClass]="activeTab() === tab.id
              ? 'text-brand-600 dark:text-brand-400 border-b-2 border-brand-500'
              : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
            {{ tab.label }}
          </button>
        }
      </div>

      <!-- ====================== ORG TAB ====================== -->
      @if (activeTab() === 'organization') {
        @if (loadingOrg()) {
          <div class="flex items-center justify-center py-16">
            <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
          </div>
        } @else {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
            <h3 class="text-base font-semibold text-gray-800 dark:text-white/90 mb-4">Información de la organización</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre</label>
                <input type="text" [(ngModel)]="orgName"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Slug</label>
                <input type="text" [value]="orgSlug()" disabled
                  class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-500" />
              </div>
            </div>
          </div>

          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
            <h3 class="text-base font-semibold text-gray-800 dark:text-white/90 mb-1">Modo de periodos fiscales</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-5">Cómo se gestionan los periodos contables cuando hay varios aplicativos activos.</p>
            <div class="space-y-3">
              <label class="flex items-start gap-4 p-4 rounded-lg border cursor-pointer transition"
                [ngClass]="fiscalMode() === 'per_app' ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10' : 'border-gray-200 dark:border-gray-700'">
                <input type="radio" name="fiscal_mode" value="per_app" [checked]="fiscalMode() === 'per_app'" (change)="fiscalMode.set('per_app')" class="mt-0.5 accent-brand-500" />
                <div>
                  <span class="block text-sm font-semibold text-gray-800 dark:text-white/90">Independiente por aplicativo</span>
                  <span class="block text-xs text-gray-500 mt-1">Cada aplicativo maneja sus propios periodos fiscales.</span>
                </div>
              </label>
              <label class="flex items-start gap-4 p-4 rounded-lg border cursor-pointer transition"
                [ngClass]="fiscalMode() === 'unified' ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10' : 'border-gray-200 dark:border-gray-700'">
                <input type="radio" name="fiscal_mode" value="unified" [checked]="fiscalMode() === 'unified'" (change)="fiscalMode.set('unified')" class="mt-0.5 accent-brand-500" />
                <div>
                  <span class="block text-sm font-semibold text-gray-800 dark:text-white/90">Unificado</span>
                  <span class="block text-xs text-gray-500 mt-1">Todos los aplicativos comparten un único periodo fiscal.</span>
                </div>
              </label>
            </div>
          </div>

          <div class="flex justify-end">
            <button (click)="saveOrg()" [disabled]="savingOrg()"
              class="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition disabled:opacity-50">
              @if (savingOrg()) { Guardando... } @else { Guardar cambios }
            </button>
          </div>
        }
      }

      <!-- ====================== ACCOUNT TAB ====================== -->
      @if (activeTab() === 'account') {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 max-w-xl">
          <h3 class="text-base font-semibold text-gray-800 dark:text-white/90 mb-1">Cambiar contraseña</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Actualiza tu contraseña de acceso a Savvy. Mínimo 8 caracteres.</p>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Contraseña actual *</label>
              <input type="password" [(ngModel)]="passwordForm.current_password" autocomplete="current-password"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nueva contraseña *</label>
              <input type="password" [(ngModel)]="passwordForm.new_password" autocomplete="new-password"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90" />
              <p class="text-[10px] text-gray-500 mt-1">Mínimo 8 caracteres.</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Confirmar nueva contraseña *</label>
              <input type="password" [(ngModel)]="passwordForm.confirm" autocomplete="new-password"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90" />
              @if (passwordForm.confirm && passwordForm.confirm !== passwordForm.new_password) {
                <p class="text-[10px] text-red-500 mt-1">Las contraseñas no coinciden.</p>
              }
            </div>
          </div>

          <div class="mt-6 flex justify-end">
            <button (click)="changePassword()" [disabled]="changingPassword() || !canChangePassword()"
              class="px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition disabled:opacity-50">
              @if (changingPassword()) { Guardando... } @else { Cambiar contraseña }
            </button>
          </div>
        </div>
      }

      <!-- ====================== CUSTOM ROLES TAB ====================== -->
      @if (activeTab() === 'custom_roles') {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-start justify-between mb-4 gap-4">
            <div>
              <h3 class="text-base font-semibold text-gray-800 dark:text-white/90">Roles personalizados</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">Crea roles propios para cada aplicación con los permisos que necesites.</p>
            </div>
            <button (click)="openCreateRole()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
              + Nuevo rol
            </button>
          </div>

          @if (loadingRoles()) {
            <div class="flex items-center justify-center py-10">
              <div class="animate-spin rounded-full h-6 w-6 border-4 border-brand-200 border-t-brand-600"></div>
            </div>
          } @else if (customRoles().length === 0) {
            <div class="text-center py-10 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
              <p class="text-sm text-gray-500">Aún no has creado roles personalizados.</p>
              <p class="text-xs text-gray-400 mt-1">Los roles del sistema (owner, admin, etc.) están disponibles automáticamente.</p>
            </div>
          } @else {
            <div class="space-y-3">
              @for (r of customRoles(); track r.id) {
                <div class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-400 font-mono uppercase">{{ r.app_code }}</span>
                        <p class="text-sm font-semibold text-gray-800 dark:text-white/90">{{ r.name }}</p>
                        <span class="text-[10px] text-gray-500 font-mono">· {{ r.code }}</span>
                      </div>
                      @if (r.description) {
                        <p class="text-xs text-gray-500 mb-2">{{ r.description }}</p>
                      }
                      <div class="flex flex-wrap gap-1">
                        @for (p of r.permissions; track p) {
                          <span class="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-mono">{{ p }}</span>
                        }
                        @if (r.permissions.length === 0) {
                          <span class="text-[10px] text-gray-400">Sin permisos</span>
                        }
                      </div>
                    </div>
                    <div class="flex flex-col gap-1">
                      <button (click)="openEditRole(r)" class="text-[10px] px-2 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">Editar</button>
                      <button (click)="deleteRole(r)" class="text-[10px] px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">Eliminar</button>
                    </div>
                  </div>
                </div>
              }
            </div>
          }
        </div>
      }

      <!-- Role editor modal -->
      @if (showRoleModal()) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-xl shadow-xl max-h-[90vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 shrink-0">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">
                {{ editingRoleId() ? 'Editar rol personalizado' : 'Nuevo rol personalizado' }}
              </h3>
            </div>
            <div class="p-6 overflow-y-auto flex-1 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">App *</label>
                <select [(ngModel)]="roleForm.app_code" (ngModelChange)="onAppChange()" [disabled]="!!editingRoleId()"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm disabled:opacity-60">
                  <option value="">Selecciona una app...</option>
                  @for (a of activeApps(); track a.app_code) {
                    <option [value]="a.app_code">{{ a.app_name }}</option>
                  }
                </select>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Código *</label>
                  <input type="text" [(ngModel)]="roleForm.code" [disabled]="!!editingRoleId()" placeholder="asistente_tesoreria"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm font-mono lowercase disabled:opacity-60" />
                  <p class="text-[10px] text-gray-500 mt-1">Solo minúsculas, números y "_"</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                  <input type="text" [(ngModel)]="roleForm.name" placeholder="Asistente de tesorería"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="roleForm.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm resize-none"></textarea>
              </div>

              <!-- Permissions -->
              <div class="border-t border-gray-200 dark:border-gray-700 pt-4 mt-2">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Permisos</label>
                @if (!roleForm.app_code) {
                  <p class="text-xs text-gray-400">Selecciona una app para ver los permisos disponibles.</p>
                } @else if (permissionsByCategory().length === 0) {
                  <p class="text-xs text-gray-400">Esta app no tiene permisos en el catálogo.</p>
                } @else {
                  <div class="space-y-3 max-h-60 overflow-y-auto custom-scrollbar pr-2">
                    @for (group of permissionsByCategory(); track group.category) {
                      <div>
                        <p class="text-[10px] uppercase tracking-wide text-gray-400 font-semibold mb-1">{{ group.category }}</p>
                        <div class="space-y-1">
                          @for (p of group.items; track p.code) {
                            <label class="flex items-start gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 p-1.5 rounded">
                              <input type="checkbox" [checked]="roleForm.permissions.includes(p.code)" (change)="togglePermission(p.code)" class="mt-0.5 rounded border-gray-300 text-brand-500" />
                              <div class="min-w-0 flex-1">
                                <p class="text-xs font-medium text-gray-800 dark:text-white/90">{{ p.name }}</p>
                                <p class="text-[10px] text-gray-500 font-mono">{{ p.code }}</p>
                                @if (p.description) {
                                  <p class="text-[10px] text-gray-500">{{ p.description }}</p>
                                }
                              </div>
                            </label>
                          }
                        </div>
                      </div>
                    }
                  </div>
                }
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3 shrink-0">
              <button (click)="closeRoleModal()" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="saveRole()" [disabled]="!canSaveRole()"
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
                {{ editingRoleId() ? 'Guardar' : 'Crear rol' }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class OrganizationSettingsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly notify = inject(NotificationService);

  activeTab = signal<TabId>('organization');
  tabs: Array<{ id: TabId; label: string }> = [
    { id: 'organization', label: 'Organización' },
    { id: 'account', label: 'Mi cuenta' },
    { id: 'custom_roles', label: 'Roles personalizados' },
  ];

  // Organization tab
  loadingOrg = signal(true);
  savingOrg = signal(false);
  orgName = '';
  orgSlug = signal('');
  orgId = signal('');
  fiscalMode = signal<'per_app' | 'unified'>('per_app');
  private currentSettings: Record<string, unknown> = {};

  // Account tab
  changingPassword = signal(false);
  passwordForm = { current_password: '', new_password: '', confirm: '' };

  // Custom roles tab
  loadingRoles = signal(false);
  customRoles = signal<CustomRole[]>([]);
  orgApps = signal<OrgApp[]>([]);
  permissionsCatalog = signal<AppPermission[]>([]);

  showRoleModal = signal(false);
  editingRoleId = signal<string | null>(null);
  roleForm = {
    app_code: '',
    code: '',
    name: '',
    description: '',
    permissions: [] as string[],
  };

  ngOnInit(): void {
    this.loadOrg();
  }

  selectTab(id: TabId): void {
    this.activeTab.set(id);
    if (id === 'custom_roles' && this.customRoles().length === 0) {
      this.loadCustomRoles();
      this.loadOrgApps();
    }
  }

  // -------- Organization tab --------

  private loadOrg(): void {
    this.api.get<OrgResponse>('/organizations/me').subscribe({
      next: (org) => {
        this.orgName = org.name;
        this.orgSlug.set(org.slug);
        this.orgId.set(org.id);
        this.currentSettings = org.settings || {};
        this.fiscalMode.set(
          (this.currentSettings['fiscal_period_mode'] as 'per_app' | 'unified') || 'per_app',
        );
        this.loadingOrg.set(false);
      },
      error: () => {
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar la organización' });
        this.loadingOrg.set(false);
      },
    });
  }

  saveOrg(): void {
    this.savingOrg.set(true);
    const merged = { ...this.currentSettings, fiscal_period_mode: this.fiscalMode() };
    this.api.patch<OrgResponse>('/organizations/me', {
      name: this.orgName,
      settings: merged,
    }).subscribe({
      next: (org) => {
        this.currentSettings = org.settings || {};
        this.notify.show({ type: 'success', title: 'Guardado', message: 'Configuración guardada' });
        this.savingOrg.set(false);
      },
      error: () => {
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo guardar' });
        this.savingOrg.set(false);
      },
    });
  }

  // -------- Account tab --------

  canChangePassword(): boolean {
    return (
      this.passwordForm.current_password.length > 0 &&
      this.passwordForm.new_password.length >= 8 &&
      this.passwordForm.new_password === this.passwordForm.confirm
    );
  }

  changePassword(): void {
    if (!this.canChangePassword()) return;
    this.changingPassword.set(true);
    this.api.post('/auth/change-password', {
      current_password: this.passwordForm.current_password,
      new_password: this.passwordForm.new_password,
    }).subscribe({
      next: () => {
        this.changingPassword.set(false);
        this.passwordForm = { current_password: '', new_password: '', confirm: '' };
        this.notify.show({
          type: 'success',
          title: 'Contraseña actualizada',
          message: 'Tu contraseña ha sido cambiada correctamente.',
        });
      },
      error: (err) => {
        this.changingPassword.set(false);
        const msg = err.error?.detail || 'No se pudo cambiar la contraseña';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
      },
    });
  }

  // -------- Custom roles tab --------

  private loadCustomRoles(): void {
    const oid = this.orgId();
    if (!oid) return;
    this.loadingRoles.set(true);
    // Use platform endpoint if available; fallback: listRoleCatalog filtered by org
    this.api.get<CustomRole[]>(`/platform/organizations/${oid}/custom-roles`).subscribe({
      next: (list) => {
        this.customRoles.set(list);
        this.loadingRoles.set(false);
      },
      error: () => {
        this.customRoles.set([]);
        this.loadingRoles.set(false);
      },
    });
  }

  private loadOrgApps(): void {
    const oid = this.orgId();
    if (!oid) return;
    this.api.get<OrgApp[]>(`/platform/organizations/${oid}/apps`).subscribe({
      next: (apps) => this.orgApps.set(apps.filter((a) => a.is_active)),
      error: () => this.orgApps.set([]),
    });
  }

  activeApps(): OrgApp[] {
    return this.orgApps();
  }

  openCreateRole(): void {
    this.editingRoleId.set(null);
    this.roleForm = { app_code: '', code: '', name: '', description: '', permissions: [] };
    this.permissionsCatalog.set([]);
    this.showRoleModal.set(true);
  }

  openEditRole(r: CustomRole): void {
    this.editingRoleId.set(r.id);
    this.roleForm = {
      app_code: r.app_code,
      code: r.code,
      name: r.name,
      description: r.description || '',
      permissions: [...r.permissions],
    };
    this.showRoleModal.set(true);
    this.loadPermissions(r.app_code);
  }

  closeRoleModal(): void {
    this.showRoleModal.set(false);
    this.editingRoleId.set(null);
  }

  onAppChange(): void {
    this.roleForm.permissions = [];
    if (this.roleForm.app_code) {
      this.loadPermissions(this.roleForm.app_code);
    } else {
      this.permissionsCatalog.set([]);
    }
  }

  private loadPermissions(appCode: string): void {
    this.api.get<AppPermission[]>(`/platform/apps/${appCode}/permissions`).subscribe({
      next: (list) => this.permissionsCatalog.set(list),
      error: () => this.permissionsCatalog.set([]),
    });
  }

  permissionsByCategory(): Array<{ category: string; items: AppPermission[] }> {
    const groups = new Map<string, AppPermission[]>();
    for (const p of this.permissionsCatalog()) {
      const cat = p.category || 'general';
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push(p);
    }
    return Array.from(groups.entries()).map(([category, items]) => ({ category, items }));
  }

  togglePermission(code: string): void {
    const idx = this.roleForm.permissions.indexOf(code);
    if (idx >= 0) {
      this.roleForm.permissions.splice(idx, 1);
    } else {
      this.roleForm.permissions.push(code);
    }
  }

  canSaveRole(): boolean {
    return !!(
      this.roleForm.app_code &&
      this.roleForm.code &&
      /^[a-z][a-z0-9_]*$/.test(this.roleForm.code) &&
      this.roleForm.name
    );
  }

  saveRole(): void {
    if (!this.canSaveRole()) return;
    const oid = this.orgId();
    if (!oid) return;
    const editId = this.editingRoleId();
    const payload = editId
      ? {
          name: this.roleForm.name,
          description: this.roleForm.description,
          permissions: this.roleForm.permissions,
        }
      : this.roleForm;

    const req$ = editId
      ? this.api.patch<CustomRole>(
          `/platform/organizations/${oid}/custom-roles/${editId}`,
          payload,
        )
      : this.api.post<CustomRole>(`/platform/organizations/${oid}/custom-roles`, payload);

    req$.subscribe({
      next: () => {
        this.notify.show({
          type: 'success',
          title: editId ? 'Rol actualizado' : 'Rol creado',
          message: this.roleForm.name,
        });
        this.closeRoleModal();
        this.loadCustomRoles();
      },
      error: (err) => {
        const msg = err.error?.detail || 'No se pudo guardar el rol';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
      },
    });
  }

  deleteRole(r: CustomRole): void {
    if (!confirm(`¿Eliminar el rol "${r.name}"?`)) return;
    const oid = this.orgId();
    if (!oid) return;
    this.api.delete(`/platform/organizations/${oid}/custom-roles/${r.id}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminado', message: r.name });
        this.loadCustomRoles();
      },
      error: (err) => {
        this.notify.show({
          type: 'error', title: 'Error',
          message: err.error?.detail || 'No se pudo eliminar',
        });
      },
    });
  }
}
