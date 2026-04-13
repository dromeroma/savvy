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

interface OrgApp {
  app_code: string;
  app_name: string;
  app_icon: string | null;
  app_color: string | null;
  is_active: boolean;
  status: string | null;
  activated_at: string | null;
  trial_ends_at: string | null;
  expires_at: string | null;
}

interface AppRoleEntry {
  app_code: string;
  app_name: string;
  role: string;
}

interface OrgMember {
  user_id: string;
  name: string;
  email: string;
  membership_id: string;
  membership_role: string;
  joined_at: string;
  app_roles: AppRoleEntry[];
}

interface AppRole {
  id: string;
  app_code: string;
  code: string;
  name: string;
  description: string | null;
}

interface FeatureRow {
  id: string;
  key: string;
  name: string;
  description: string | null;
  category: string | null;
  feature_type: string;
}

interface FeatureOverride {
  id: string;
  organization_id: string;
  feature_id: string;
  enabled: boolean | null;
  limit_value: number | null;
  reason: string | null;
  expires_at: string | null;
}

interface CustomRoleRow {
  id: string;
  app_code: string;
  code: string;
  name: string;
  description: string | null;
  permissions: string[];
  is_system: boolean;
  is_active: boolean;
}

interface AppPerm {
  id: string;
  app_code: string;
  code: string;
  name: string;
  description: string | null;
  category: string | null;
}

type TabId = 'general' | 'subscription' | 'apps' | 'members' | 'custom_roles' | 'features';

@Component({
  selector: 'app-platform-org-detail',
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="max-w-5xl">
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

        <!-- ===== GENERAL ===== -->
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

        <!-- ===== SUBSCRIPTION ===== -->
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
                  <button (click)="activateSubscription()" class="px-3 py-1.5 text-xs rounded-lg bg-success-500 hover:bg-success-600 text-white transition">Activar</button>
                }
                @if (org()!.subscription!.status !== 'suspended') {
                  <button (click)="suspendSubscription()" class="px-3 py-1.5 text-xs rounded-lg border border-warning-400 text-warning-600 hover:bg-warning-50 dark:hover:bg-warning-900/20 transition">Suspender</button>
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
                  <button (click)="changePlan()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">Cambiar</button>
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
                <button (click)="assignPlan()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">Asignar plan</button>
              </div>
            }
          </div>
        }

        <!-- ===== APPS ===== -->
        @if (activeTab() === 'apps') {
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-4">Apps del ecosistema</h3>
            @if (loadingApps()) {
              <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-6 w-6 border-4 border-brand-200 border-t-brand-600"></div>
              </div>
            } @else {
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                @for (a of orgApps(); track a.app_code) {
                  <div class="flex items-center justify-between p-4 rounded-lg border transition"
                    [ngClass]="a.is_active ? 'border-brand-400 bg-brand-50/30 dark:bg-brand-500/10' : 'border-gray-200 dark:border-gray-700'">
                    <div class="flex items-center gap-3 min-w-0">
                      <div class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm shrink-0"
                        [style.background-color]="a.app_color || '#9ca3af'">
                        {{ a.app_name.slice(0, 1) }}
                      </div>
                      <div class="min-w-0">
                        <p class="text-sm font-semibold text-gray-800 dark:text-white/90 truncate">{{ a.app_name }}</p>
                        <p class="text-[10px] text-gray-500 font-mono">{{ a.app_code }}</p>
                      </div>
                    </div>
                    @if (a.is_active) {
                      <button (click)="deactivateApp(a.app_code)" class="text-xs px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition">
                        Desactivar
                      </button>
                    } @else {
                      <button (click)="activateApp(a.app_code)" class="text-xs px-2 py-1 rounded bg-brand-500 hover:bg-brand-600 text-white transition">
                        Activar
                      </button>
                    }
                  </div>
                }
              </div>
            }
          </div>
        }

        <!-- ===== MEMBERS ===== -->
        @if (activeTab() === 'members') {
          <div class="space-y-4">
            <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Usuarios de la empresa ({{ members().length }})</h3>
                <button (click)="showInviteModal = true" class="px-3 py-1.5 text-xs rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
                  + Invitar usuario
                </button>
              </div>
              @if (loadingMembers()) {
                <div class="flex items-center justify-center py-8">
                  <div class="animate-spin rounded-full h-6 w-6 border-4 border-brand-200 border-t-brand-600"></div>
                </div>
              } @else if (members().length === 0) {
                <p class="text-sm text-gray-400 text-center py-6">Sin usuarios.</p>
              } @else {
                <div class="space-y-2">
                  @for (m of members(); track m.user_id) {
                    <div class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div class="flex items-start justify-between gap-3">
                        <div class="min-w-0">
                          <div class="flex items-center gap-2">
                            <p class="text-sm font-semibold text-gray-800 dark:text-white/90">{{ m.name }}</p>
                            <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 uppercase tracking-wide">{{ m.membership_role }}</span>
                          </div>
                          <p class="text-xs text-gray-500 font-mono">{{ m.email }}</p>
                          @if (m.app_roles.length > 0) {
                            <div class="flex flex-wrap gap-1.5 mt-2">
                              @for (ar of m.app_roles; track ar.app_code) {
                                <span class="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-400">
                                  <span class="font-medium">{{ ar.app_name }}</span>
                                  <span class="opacity-70">·</span>
                                  <span>{{ ar.role }}</span>
                                  <button (click)="revokeAppRole(m.user_id, ar.app_code)" class="hover:text-error-600 transition">×</button>
                                </span>
                              }
                            </div>
                          }
                        </div>
                        <div class="flex flex-col gap-1">
                          <button (click)="openAssignRoleForMember(m)" class="text-[10px] px-2 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                            + Rol de app
                          </button>
                          @if (m.membership_role !== 'owner') {
                            <button (click)="removeMember(m.user_id)" class="text-[10px] px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition">
                              Quitar
                            </button>
                          }
                        </div>
                      </div>
                    </div>
                  }
                </div>
              }
            </div>
          </div>
        }

        <!-- ===== CUSTOM ROLES ===== -->
        @if (activeTab() === 'custom_roles') {
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <div class="flex items-start justify-between gap-3 mb-4">
              <div>
                <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Roles personalizados</h3>
                <p class="text-xs text-gray-500">Crea roles propios de esta empresa con los permisos que necesites.</p>
              </div>
              <button (click)="openCreateCustomRole()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
                + Nuevo rol
              </button>
            </div>
            @if (loadingCustomRoles()) {
              <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-6 w-6 border-4 border-brand-200 border-t-brand-600"></div>
              </div>
            } @else if (customRoles().length === 0) {
              <div class="text-center py-8 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
                <p class="text-sm text-gray-500">Sin roles personalizados todavía.</p>
                <p class="text-xs text-gray-400 mt-1">Los roles del sistema siempre están disponibles.</p>
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
                        @if (r.description) { <p class="text-xs text-gray-500 mb-2">{{ r.description }}</p> }
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
                        <button (click)="openEditCustomRole(r)" class="text-[10px] px-2 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">Editar</button>
                        <button (click)="deleteCustomRole(r)" class="text-[10px] px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">Eliminar</button>
                      </div>
                    </div>
                  </div>
                }
              </div>
            }
          </div>
        }

        <!-- ===== FEATURES OVERRIDES ===== -->
        @if (activeTab() === 'features') {
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">Feature overrides</h3>
            <p class="text-xs text-gray-500 mb-4">Activa o desactiva una feature específica para esta empresa, sobrescribiendo el plan.</p>
            @if (loadingFeatures()) {
              <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-6 w-6 border-4 border-brand-200 border-t-brand-600"></div>
              </div>
            } @else {
              <div class="space-y-2">
                @for (f of features(); track f.id) {
                  <div class="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700">
                    <div class="min-w-0">
                      <p class="text-sm font-medium text-gray-800 dark:text-white/90">{{ f.name }}</p>
                      <p class="text-[10px] text-gray-500 font-mono">{{ f.key }}</p>
                      @if (overrideFor(f.id); as ov) {
                        @if (ov.reason) { <p class="text-[10px] text-gray-500 mt-1">"{{ ov.reason }}"</p> }
                      }
                    </div>
                    <div class="flex items-center gap-2">
                      @if (overrideFor(f.id); as ov) {
                        <span class="text-[10px] px-2 py-0.5 rounded-full"
                          [ngClass]="ov.enabled ? 'bg-success-100 text-success-700 dark:bg-success-500/20 dark:text-success-400' : 'bg-error-100 text-error-700 dark:bg-error-500/20 dark:text-error-400'">
                          {{ ov.enabled ? 'forzado ON' : 'forzado OFF' }}
                        </span>
                        <button (click)="removeOverride(f.key)" class="text-[10px] px-2 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                          Quitar
                        </button>
                      } @else {
                        <button (click)="setOverride(f.key, true)" class="text-[10px] px-2 py-1 rounded bg-success-500 hover:bg-success-600 text-white">
                          Forzar ON
                        </button>
                        <button (click)="setOverride(f.key, false)" class="text-[10px] px-2 py-1 rounded bg-error-500 hover:bg-error-600 text-white">
                          Forzar OFF
                        </button>
                      }
                    </div>
                  </div>
                }
              </div>
            }
          </div>
        }
      } @else if (loading()) {
        <div class="flex items-center justify-center py-24">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      }

      <!-- Invite modal -->
      @if (showInviteModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Invitar usuario a {{ org()?.name }}</h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre completo *</label>
                <input type="text" [(ngModel)]="inviteForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Email *</label>
                <input type="email" [(ngModel)]="inviteForm.email" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Contraseña inicial *</label>
                <input type="text" [(ngModel)]="inviteForm.password" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm font-mono" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Rol de membresía</label>
                <select [(ngModel)]="inviteForm.membership_role" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
                  <option value="member">Miembro</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showInviteModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="inviteMember()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Invitar</button>
            </div>
          </div>
        </div>
      }

      <!-- Custom role editor modal -->
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
                <select [(ngModel)]="customRoleForm.app_code" (ngModelChange)="onRoleAppChange()" [disabled]="!!editingRoleId()"
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
                  <input type="text" [(ngModel)]="customRoleForm.code" [disabled]="!!editingRoleId()" placeholder="asistente_ventas"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm font-mono lowercase disabled:opacity-60" />
                  <p class="text-[10px] text-gray-500 mt-1">Solo minúsculas, números y "_"</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                  <input type="text" [(ngModel)]="customRoleForm.name"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="customRoleForm.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm resize-none"></textarea>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-700 pt-4 mt-2">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Permisos</label>
                @if (!customRoleForm.app_code) {
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
                              <input type="checkbox" [checked]="customRoleForm.permissions.includes(p.code)" (change)="toggleRolePermission(p.code)" class="mt-0.5 rounded border-gray-300 text-brand-500" />
                              <div class="min-w-0 flex-1">
                                <p class="text-xs font-medium text-gray-800 dark:text-white/90">{{ p.name }}</p>
                                <p class="text-[10px] text-gray-500 font-mono">{{ p.code }}</p>
                                @if (p.description) { <p class="text-[10px] text-gray-500">{{ p.description }}</p> }
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
              <button (click)="saveCustomRole()" [disabled]="!canSaveCustomRole()"
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
                {{ editingRoleId() ? 'Guardar' : 'Crear rol' }}
              </button>
            </div>
          </div>
        </div>
      }

      <!-- Assign app role modal -->
      @if (assigningMember()) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Asignar rol de app a {{ assigningMember()!.name }}</h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">App</label>
                <select [(ngModel)]="roleForm.app_code" (ngModelChange)="loadRolesForApp()" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm">
                  <option value="">Selecciona una app...</option>
                  @for (a of activeApps(); track a.app_code) {
                    <option [value]="a.app_code">{{ a.app_name }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Rol</label>
                <select [(ngModel)]="roleForm.role" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" [disabled]="!roleForm.app_code">
                  <option value="">Selecciona un rol...</option>
                  @for (r of rolesForSelectedApp(); track r.id) {
                    <option [value]="r.code">{{ r.name }}@if (r.description) { — {{ r.description }} }</option>
                  }
                </select>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="assigningMember.set(null)" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="confirmAssignRole()" [disabled]="!roleForm.app_code || !roleForm.role" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg">Asignar</button>
            </div>
          </div>
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
  activeTab = signal<TabId>('general');
  newPlanCode = 'starter';

  // apps
  loadingApps = signal(false);
  orgApps = signal<OrgApp[]>([]);

  // members
  loadingMembers = signal(false);
  members = signal<OrgMember[]>([]);

  // features
  loadingFeatures = signal(false);
  features = signal<FeatureRow[]>([]);
  overrides = signal<FeatureOverride[]>([]);

  // modals
  showInviteModal = false;
  inviteForm = { name: '', email: '', password: '', membership_role: 'member' };

  assigningMember = signal<OrgMember | null>(null);
  roleForm = { app_code: '', role: '' };
  rolesForSelectedApp = signal<AppRole[]>([]);

  tabs: Array<{ id: TabId; label: string }> = [
    { id: 'general', label: 'General' },
    { id: 'subscription', label: 'Suscripción' },
    { id: 'apps', label: 'Apps' },
    { id: 'members', label: 'Usuarios & roles' },
    { id: 'custom_roles', label: 'Roles personalizados' },
    { id: 'features', label: 'Features' },
  ];

  // Custom roles tab
  loadingCustomRoles = signal(false);
  customRoles = signal<CustomRoleRow[]>([]);
  permissionsCatalog = signal<AppPerm[]>([]);
  showRoleModal = signal(false);
  editingRoleId = signal<string | null>(null);
  customRoleForm = {
    app_code: '',
    code: '',
    name: '',
    description: '',
    permissions: [] as string[],
  };

  editForm = { name: '', slug: '', type: 'business' };

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
    this.loadOrg(id);
    this.api.get<Plan[]>('/platform/plans').subscribe({
      next: (p) => this.plans.set(p),
    });
  }

  selectTab(id: TabId): void {
    this.activeTab.set(id);
    const orgId = this.org()?.id;
    if (!orgId) return;
    if (id === 'apps') this.loadOrgApps(orgId);
    if (id === 'members') {
      this.loadMembers(orgId);
      this.loadOrgApps(orgId);
    }
    if (id === 'custom_roles') {
      this.loadCustomRoles(orgId);
      this.loadOrgApps(orgId);
    }
    if (id === 'features') this.loadFeatures(orgId);
  }

  private loadOrg(id: string): void {
    this.loading.set(true);
    this.api.get<OrgDetail>(`/platform/organizations/${id}`).subscribe({
      next: (o) => {
        this.org.set(o);
        this.editForm = { name: o.name, slug: o.slug, type: o.type };
        if (o.subscription) {
          this.newPlanCode = this.plans().find((p) => p.id === o.subscription!.plan_id)?.code || 'starter';
        }
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  // ---------- General ----------

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
        this.notify.show({ type: 'error', title: 'Error', message: err.error?.detail || 'No se pudo actualizar' });
      },
    });
  }

  // ---------- Subscription ----------

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
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err.error?.detail || 'No se pudo eliminar' }),
    });
  }

  // ---------- Apps tab ----------

  private loadOrgApps(orgId: string): void {
    this.loadingApps.set(true);
    this.api.get<OrgApp[]>(`/platform/organizations/${orgId}/apps`).subscribe({
      next: (apps) => {
        this.orgApps.set(apps);
        this.loadingApps.set(false);
      },
      error: () => this.loadingApps.set(false),
    });
  }

  activateApp(appCode: string): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    this.api.post(`/platform/organizations/${orgId}/apps/activate`, { app_code: appCode }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Activada', message: `App ${appCode} activada` });
        this.loadOrgApps(orgId);
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo activar la app',
      }),
    });
  }

  deactivateApp(appCode: string): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    if (!confirm(`¿Desactivar "${appCode}"? Los usuarios perderán acceso a este módulo.`)) return;
    this.api.post(`/platform/organizations/${orgId}/apps/deactivate`, { app_code: appCode }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Desactivada', message: `App ${appCode} desactivada` });
        this.loadOrgApps(orgId);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo desactivar' }),
    });
  }

  activeApps(): OrgApp[] {
    return this.orgApps().filter((a) => a.is_active);
  }

  // ---------- Members tab ----------

  private loadMembers(orgId: string): void {
    this.loadingMembers.set(true);
    this.api.get<OrgMember[]>(`/platform/organizations/${orgId}/members`).subscribe({
      next: (list) => {
        this.members.set(list);
        this.loadingMembers.set(false);
      },
      error: () => this.loadingMembers.set(false),
    });
  }

  inviteMember(): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    if (!this.inviteForm.name || !this.inviteForm.email || !this.inviteForm.password) {
      this.notify.show({ type: 'error', title: 'Faltan datos', message: 'Completa todos los campos' });
      return;
    }
    this.api.post(`/platform/organizations/${orgId}/members`, this.inviteForm).subscribe({
      next: () => {
        this.showInviteModal = false;
        this.inviteForm = { name: '', email: '', password: '', membership_role: 'member' };
        this.loadMembers(orgId);
        this.notify.show({ type: 'success', title: 'Invitado', message: 'Usuario agregado a la empresa' });
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo invitar',
      }),
    });
  }

  removeMember(userId: string): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    if (!confirm('¿Quitar este usuario de la empresa? Perderá acceso inmediato.')) return;
    this.api.delete(`/platform/organizations/${orgId}/members/${userId}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminado', message: 'Usuario removido' });
        this.loadMembers(orgId);
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo eliminar',
      }),
    });
  }

  openAssignRoleForMember(m: OrgMember): void {
    this.assigningMember.set(m);
    this.roleForm = { app_code: '', role: '' };
    this.rolesForSelectedApp.set([]);
  }

  loadRolesForApp(): void {
    const code = this.roleForm.app_code;
    if (!code) {
      this.rolesForSelectedApp.set([]);
      return;
    }
    this.api.get<AppRole[]>(`/platform/apps/${code}/roles`).subscribe({
      next: (list) => this.rolesForSelectedApp.set(list),
    });
  }

  confirmAssignRole(): void {
    const m = this.assigningMember();
    const orgId = this.org()?.id;
    if (!m || !orgId || !this.roleForm.app_code || !this.roleForm.role) return;
    this.api.post(`/platform/organizations/${orgId}/app-roles`, {
      user_id: m.user_id,
      app_code: this.roleForm.app_code,
      role: this.roleForm.role,
    }).subscribe({
      next: () => {
        this.assigningMember.set(null);
        this.notify.show({ type: 'success', title: 'Rol asignado', message: `${this.roleForm.app_code} · ${this.roleForm.role}` });
        this.loadMembers(orgId);
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo asignar',
      }),
    });
  }

  revokeAppRole(userId: string, appCode: string): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    if (!confirm(`¿Revocar el rol en ${appCode}?`)) return;
    this.api.delete(`/platform/organizations/${orgId}/app-roles`, {
      user_id: userId,
      app_code: appCode,
    }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Revocado', message: 'Rol eliminado' });
        this.loadMembers(orgId);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo revocar' }),
    });
  }

  // ---------- Custom roles tab ----------

  private loadCustomRoles(orgId: string): void {
    this.loadingCustomRoles.set(true);
    this.api.get<CustomRoleRow[]>(`/platform/organizations/${orgId}/custom-roles`).subscribe({
      next: (list) => {
        this.customRoles.set(list);
        this.loadingCustomRoles.set(false);
      },
      error: () => {
        this.customRoles.set([]);
        this.loadingCustomRoles.set(false);
      },
    });
  }

  openCreateCustomRole(): void {
    this.editingRoleId.set(null);
    this.customRoleForm = { app_code: '', code: '', name: '', description: '', permissions: [] };
    this.permissionsCatalog.set([]);
    this.showRoleModal.set(true);
  }

  openEditCustomRole(r: CustomRoleRow): void {
    this.editingRoleId.set(r.id);
    this.customRoleForm = {
      app_code: r.app_code,
      code: r.code,
      name: r.name,
      description: r.description || '',
      permissions: [...r.permissions],
    };
    this.showRoleModal.set(true);
    this.loadPermissionsForApp(r.app_code);
  }

  closeRoleModal(): void {
    this.showRoleModal.set(false);
    this.editingRoleId.set(null);
  }

  onRoleAppChange(): void {
    this.customRoleForm.permissions = [];
    if (this.customRoleForm.app_code) {
      this.loadPermissionsForApp(this.customRoleForm.app_code);
    } else {
      this.permissionsCatalog.set([]);
    }
  }

  private loadPermissionsForApp(appCode: string): void {
    this.api.get<AppPerm[]>(`/platform/apps/${appCode}/permissions`).subscribe({
      next: (list) => this.permissionsCatalog.set(list),
      error: () => this.permissionsCatalog.set([]),
    });
  }

  permissionsByCategory(): Array<{ category: string; items: AppPerm[] }> {
    const groups = new Map<string, AppPerm[]>();
    for (const p of this.permissionsCatalog()) {
      const cat = p.category || 'general';
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push(p);
    }
    return Array.from(groups.entries()).map(([category, items]) => ({ category, items }));
  }

  toggleRolePermission(code: string): void {
    const idx = this.customRoleForm.permissions.indexOf(code);
    if (idx >= 0) {
      this.customRoleForm.permissions.splice(idx, 1);
    } else {
      this.customRoleForm.permissions.push(code);
    }
  }

  canSaveCustomRole(): boolean {
    return !!(
      this.customRoleForm.app_code &&
      this.customRoleForm.code &&
      /^[a-z][a-z0-9_]*$/.test(this.customRoleForm.code) &&
      this.customRoleForm.name
    );
  }

  saveCustomRole(): void {
    if (!this.canSaveCustomRole()) return;
    const orgId = this.org()?.id;
    if (!orgId) return;
    const editId = this.editingRoleId();
    const payload = editId
      ? {
          name: this.customRoleForm.name,
          description: this.customRoleForm.description,
          permissions: this.customRoleForm.permissions,
        }
      : this.customRoleForm;

    const req$ = editId
      ? this.api.patch<CustomRoleRow>(
          `/platform/organizations/${orgId}/custom-roles/${editId}`,
          payload,
        )
      : this.api.post<CustomRoleRow>(
          `/platform/organizations/${orgId}/custom-roles`,
          payload,
        );

    req$.subscribe({
      next: () => {
        this.notify.show({
          type: 'success',
          title: editId ? 'Rol actualizado' : 'Rol creado',
          message: this.customRoleForm.name,
        });
        this.closeRoleModal();
        this.loadCustomRoles(orgId);
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo guardar',
      }),
    });
  }

  deleteCustomRole(r: CustomRoleRow): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    if (!confirm(`¿Eliminar el rol "${r.name}"?`)) return;
    this.api.delete(`/platform/organizations/${orgId}/custom-roles/${r.id}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminado', message: r.name });
        this.loadCustomRoles(orgId);
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo eliminar',
      }),
    });
  }

  // ---------- Features tab ----------

  private loadFeatures(orgId: string): void {
    this.loadingFeatures.set(true);
    Promise.all([
      new Promise<FeatureRow[]>((resolve) =>
        this.api.get<FeatureRow[]>('/platform/features').subscribe({ next: resolve, error: () => resolve([]) }),
      ),
      new Promise<FeatureOverride[]>((resolve) =>
        this.api.get<FeatureOverride[]>(`/platform/organizations/${orgId}/overrides`).subscribe({ next: resolve, error: () => resolve([]) }),
      ),
    ]).then(([features, overrides]) => {
      this.features.set(features);
      this.overrides.set(overrides);
      this.loadingFeatures.set(false);
    });
  }

  overrideFor(featureId: string): FeatureOverride | null {
    return this.overrides().find((o) => o.feature_id === featureId) || null;
  }

  setOverride(featureKey: string, enabled: boolean): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    const reason = prompt('Motivo del override (opcional):') || '';
    this.api.put(`/platform/organizations/${orgId}/overrides`, {
      feature_key: featureKey,
      enabled,
      reason,
    }).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Override aplicado', message: `${featureKey} ${enabled ? 'ON' : 'OFF'}` });
        this.loadFeatures(orgId);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo aplicar el override' }),
    });
  }

  removeOverride(featureKey: string): void {
    const orgId = this.org()?.id;
    if (!orgId) return;
    this.api.delete(`/platform/organizations/${orgId}/overrides/${featureKey}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Override removido', message: featureKey });
        this.loadFeatures(orgId);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo remover' }),
    });
  }

  // ---------- helpers ----------

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
