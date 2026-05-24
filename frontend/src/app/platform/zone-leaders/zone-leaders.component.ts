import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface PlatformZone {
  id: string;
  number: number;
  name: string | null;
  denomination_id: string;
  denomination_name: string;
  denomination_code: string;
}

interface ZoneLeader {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  zone_id: string;
  zone_number: number;
  zone_name: string | null;
  denomination_id: string;
  denomination_name: string;
  organization_id: string | null;
  organization_name: string | null;
  role: 'presbitero' | 'lider';
  assigned_at: string;
}

interface PlatformUser {
  id: string;
  name: string;
  email: string;
}

@Component({
  selector: 'app-zone-leaders',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <!-- Header -->
      <div class="flex items-start justify-between mb-6 gap-4 flex-wrap">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Liderazgos de Zona</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Asigna y revoca presbíteros y líderes de zona. Los líderes ven métricas
            agregadas de las demás iglesias de su zona.
          </p>
        </div>
        <button (click)="openForm()"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium shadow-theme-xs">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Asignar líder
        </button>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-3 mb-4">
        <select [(ngModel)]="denominationFilter" (ngModelChange)="onFilterChange()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option [ngValue]="''">Todas las denominaciones</option>
          @for (d of denominations(); track d.id) {
            <option [ngValue]="d.id">{{ d.name }} ({{ d.code }})</option>
          }
        </select>
        <select [(ngModel)]="zoneFilter" (ngModelChange)="load()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option [ngValue]="''">Todas las zonas</option>
          @for (z of filteredZones(); track z.id) {
            <option [ngValue]="z.id">Zona {{ z.number }}{{ z.name ? ' — ' + z.name : '' }}</option>
          }
        </select>
      </div>

      <!-- Loading -->
      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (leaders().length === 0) {
        <div class="rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-10 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">Aún no hay líderes asignados.</p>
        </div>
      } @else {
        <!-- Table -->
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-700/30">
              <tr class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <th class="px-4 py-3">Usuario</th>
                <th class="px-4 py-3">Zona</th>
                <th class="px-4 py-3">Denominación</th>
                <th class="px-4 py-3">Iglesia base</th>
                <th class="px-4 py-3">Rol</th>
                <th class="px-4 py-3">Asignado</th>
                <th class="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              @for (l of leaders(); track l.id) {
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                  <td class="px-4 py-3">
                    <div class="font-medium text-gray-800 dark:text-white/90">{{ l.user_name }}</div>
                    <div class="text-xs text-gray-400">{{ l.user_email }}</div>
                  </td>
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">
                    Zona {{ l.zone_number }}@if (l.zone_name) { — {{ l.zone_name }} }
                  </td>
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ l.denomination_name }}</td>
                  <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ l.organization_name || '—' }}</td>
                  <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize"
                      [ngClass]="l.role === 'presbitero'
                        ? 'bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-300'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'">
                      {{ l.role }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                    {{ l.assigned_at | date:'short' }}
                  </td>
                  <td class="px-4 py-3 text-right">
                    <button (click)="confirmRevoke(l)"
                      class="text-xs text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 font-medium">
                      Revocar
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }

      <!-- Assign modal -->
      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="closeForm()">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90 mb-1">Asignar líder de zona</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-5">El usuario podrá ver métricas agregadas de las demás iglesias de la zona.</p>

            @if (formError()) {
              <div class="mb-4 p-3 bg-error-50 border border-error-200 text-error-700 dark:bg-error-500/10 dark:border-error-500/30 dark:text-error-400 rounded-lg text-sm">
                {{ formError() }}
              </div>
            }

            <div class="space-y-4">
              <!-- User search -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Usuario</label>
                <input [(ngModel)]="userSearch" (ngModelChange)="onUserSearch()" placeholder="Buscar por nombre o email..."
                  class="w-full h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                @if (userResults().length > 0 && !selectedUser()) {
                  <div class="mt-1 max-h-40 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
                    @for (u of userResults(); track u.id) {
                      <button type="button" (click)="selectUser(u)"
                        class="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <div class="font-medium text-gray-800 dark:text-white/90">{{ u.name }}</div>
                        <div class="text-xs text-gray-400">{{ u.email }}</div>
                      </button>
                    }
                  </div>
                }
                @if (selectedUser()) {
                  <div class="mt-2 p-2 rounded-lg bg-brand-50 dark:bg-brand-500/10 text-sm flex items-center justify-between">
                    <span class="text-brand-700 dark:text-brand-300">{{ selectedUser()!.name }} ({{ selectedUser()!.email }})</span>
                    <button (click)="clearUser()" class="text-xs text-gray-500 hover:text-red-600">x</button>
                  </div>
                }
              </div>

              <!-- Zone -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Zona</label>
                <select [(ngModel)]="formZoneId"
                  class="w-full h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">Selecciona una zona</option>
                  @for (z of zones(); track z.id) {
                    <option [value]="z.id">{{ z.denomination_code }} Zona {{ z.number }}{{ z.name ? ' — ' + z.name : '' }}</option>
                  }
                </select>
              </div>

              <!-- Role -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rol</label>
                <select [(ngModel)]="formRole"
                  class="w-full h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="presbitero">Presbítero</option>
                  <option value="lider">Líder</option>
                </select>
              </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
              <button (click)="closeForm()"
                class="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600">
                Cancelar
              </button>
              <button (click)="submit()" [disabled]="saving() || !selectedUser() || !formZoneId"
                class="px-4 py-2 rounded-lg text-sm font-medium text-white bg-brand-500 hover:bg-brand-600 disabled:bg-brand-300">
                {{ saving() ? 'Asignando…' : 'Asignar' }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ZoneLeadersComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  // State
  loading = signal(true);
  leaders = signal<ZoneLeader[]>([]);
  zones = signal<PlatformZone[]>([]);

  // Filters
  zoneFilter = '';
  denominationFilter = '';

  readonly denominations = computed(() => {
    const map = new Map<string, { id: string; name: string; code: string }>();
    for (const z of this.zones()) {
      if (!map.has(z.denomination_id)) {
        map.set(z.denomination_id, {
          id: z.denomination_id, name: z.denomination_name, code: z.denomination_code,
        });
      }
    }
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  });

  readonly filteredZones = computed(() => {
    if (!this.denominationFilter) return this.zones();
    return this.zones().filter((z) => z.denomination_id === this.denominationFilter);
  });

  // Assign form
  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  userSearch = '';
  userResults = signal<PlatformUser[]>([]);
  selectedUser = signal<PlatformUser | null>(null);
  formZoneId = '';
  formRole: 'presbitero' | 'lider' = 'presbitero';
  private searchTimer: any;

  ngOnInit(): void {
    this.api.get<PlatformZone[]>('/platform/zones').subscribe({
      next: (z) => this.zones.set(z),
    });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.zoneFilter) params['zone_id'] = this.zoneFilter;
    if (this.denominationFilter && !this.zoneFilter) {
      params['denomination_id'] = this.denominationFilter;
    }
    this.api.get<ZoneLeader[]>('/platform/zone-leaders', params).subscribe({
      next: (data) => {
        this.leaders.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudieron cargar los líderes.' });
      },
    });
  }

  onFilterChange(): void {
    // Reset zone filter if denomination changes
    if (this.zoneFilter) {
      const z = this.zones().find((x) => x.id === this.zoneFilter);
      if (z && z.denomination_id !== this.denominationFilter) {
        this.zoneFilter = '';
      }
    }
    this.load();
  }

  // --- Assign form ---
  openForm(): void {
    this.formOpen.set(true);
    this.formError.set('');
    this.userSearch = '';
    this.userResults.set([]);
    this.selectedUser.set(null);
    this.formZoneId = this.zoneFilter || '';
    this.formRole = 'presbitero';
  }

  closeForm(): void {
    this.formOpen.set(false);
  }

  onUserSearch(): void {
    clearTimeout(this.searchTimer);
    if (this.selectedUser()) this.selectedUser.set(null);
    if (!this.userSearch || this.userSearch.length < 2) {
      this.userResults.set([]);
      return;
    }
    this.searchTimer = setTimeout(() => {
      this.api.get<PlatformUser[]>('/platform/users', { search: this.userSearch }).subscribe({
        next: (users) => this.userResults.set(users.slice(0, 8)),
      });
    }, 250);
  }

  selectUser(u: PlatformUser): void {
    this.selectedUser.set(u);
    this.userSearch = u.name;
    this.userResults.set([]);
  }

  clearUser(): void {
    this.selectedUser.set(null);
    this.userSearch = '';
  }

  submit(): void {
    const u = this.selectedUser();
    if (!u || !this.formZoneId) return;
    this.saving.set(true);
    this.formError.set('');
    this.api.post('/platform/zone-leaders', {
      user_id: u.id,
      zone_id: this.formZoneId,
      role: this.formRole,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({ type: 'success', title: 'Asignado', message: 'Líder de zona asignado.' });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail;
        this.formError.set(typeof detail === 'string' ? detail : 'No se pudo asignar.');
      },
    });
  }

  // --- Revoke ---
  confirmRevoke(l: ZoneLeader): void {
    const ok = confirm(
      `¿Revocar a ${l.user_name} como ${l.role} de Zona ${l.zone_number}?`,
    );
    if (!ok) return;
    this.api.delete(`/platform/zone-leaders/${l.id}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Revocado', message: 'Liderazgo revocado.' });
        this.load();
      },
      error: () => {
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo revocar.' });
      },
    });
  }
}
