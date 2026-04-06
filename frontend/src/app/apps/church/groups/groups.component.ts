import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface GroupType {
  id: string;
  name: string;
  code: string;
}

interface Group {
  id: string;
  group_type_id: string;
  name: string;
  description: string | null;
  leader_id: string | null;
  status: string;
  created_at: string;
}

interface GroupMember {
  id: string;
  person_id: string;
  role: string;
  joined_at: string;
}

interface PersonResult {
  id: string;
  first_name: string;
  last_name: string;
}

@Component({
  selector: 'app-groups',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Grupos y Ministerios</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Gestión de ministerios, células y comités</p>
        </div>
        <div class="flex gap-2">
          <button (click)="showTypeModal = true"
            class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-sm font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition">
            + Tipo de grupo
          </button>
          <button (click)="openGroupModal()"
            class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">
            + Nuevo grupo
          </button>
        </div>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <!-- Filter by type -->
        @if (groupTypes().length > 0) {
          <div class="flex flex-wrap gap-2 mb-6">
            <button (click)="filterType.set(null); loadGroups()"
              class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
              [ngClass]="filterType() === null ? 'bg-brand-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'">
              Todos
            </button>
            @for (gt of groupTypes(); track gt.id) {
              <button (click)="filterType.set(gt.code); loadGroups()"
                class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
                [ngClass]="filterType() === gt.code ? 'bg-brand-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'">
                {{ gt.name }}
              </button>
            }
          </div>
        }

        <!-- Groups grid -->
        @if (groups().length > 0) {
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            @for (group of groups(); track group.id) {
              <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-theme-md transition">
                <div class="flex items-start justify-between mb-3">
                  <div>
                    <h3 class="text-base font-semibold text-gray-800 dark:text-white/90">{{ group.name }}</h3>
                    @if (group.description) {
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ group.description }}</p>
                    }
                  </div>
                  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                    [ngClass]="group.status === 'active' ? 'bg-success-100 text-success-700 dark:bg-success-500/20 dark:text-success-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                    {{ group.status === 'active' ? 'Activo' : 'Inactivo' }}
                  </span>
                </div>
                <div class="flex items-center justify-between mt-4">
                  <span class="text-xs text-gray-400 dark:text-gray-500">
                    {{ getTypeName(group.group_type_id) }}
                  </span>
                  <button (click)="openMembersPanel(group)" class="text-sm text-brand-600 dark:text-brand-400 hover:underline">
                    Ver miembros
                  </button>
                </div>
              </div>
            }
          </div>
        } @else {
          <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <p class="text-gray-500 dark:text-gray-400">No hay grupos creados.</p>
            <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Crea un tipo de grupo primero y luego agrega grupos.</p>
          </div>
        }
      }

      <!-- Create Group Type Modal -->
      @if (showTypeModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nuevo tipo de grupo</h3>
            </div>
            <div class="p-6 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre</label>
                <input type="text" [(ngModel)]="typeForm.name" placeholder="Ej: Ministerio, Célula, Comité"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Código</label>
                <input type="text" [(ngModel)]="typeForm.code" placeholder="Ej: ministry, cell, committee"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showTypeModal = false"
                class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">Cancelar</button>
              <button (click)="createGroupType()"
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">Crear</button>
            </div>
          </div>
        </div>
      }

      <!-- Create Group Modal -->
      @if (showGroupModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nuevo grupo</h3>
            </div>
            <div class="p-6 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Tipo de grupo *</label>
                <select [(ngModel)]="groupForm.group_type_id"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition">
                  <option value="">Seleccionar...</option>
                  @for (gt of groupTypes(); track gt.id) {
                    <option [value]="gt.id">{{ gt.name }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                <input type="text" [(ngModel)]="groupForm.name" placeholder="Ej: Ministerio de Alabanza"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="groupForm.description" rows="2" placeholder="Descripción opcional..."
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition resize-none"></textarea>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showGroupModal = false"
                class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">Cancelar</button>
              <button (click)="createGroup()"
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">Crear</button>
            </div>
          </div>
        </div>
      }

      <!-- Members Panel Modal -->
      @if (showMembersPanel) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl max-h-[80vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Miembros de {{ selectedGroup?.name }}</h3>
              <button (click)="showMembersPanel = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto flex-1 min-h-0">
              <!-- Add member -->
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Agregar congregante</label>
                <div class="relative">
                  <input type="text" [(ngModel)]="memberSearch" (input)="searchPersons()" placeholder="Buscar por nombre..."
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                  @if (personResults().length > 0) {
                    <div class="absolute z-10 top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                      @for (p of personResults(); track p.id) {
                        <button (click)="addMember(p.id)" class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-white/90 transition">
                          {{ p.first_name }} {{ p.last_name }}
                        </button>
                      }
                    </div>
                  }
                </div>
              </div>

              <!-- Members list -->
              @if (loadingMembers()) {
                <div class="flex justify-center py-8">
                  <div class="animate-spin rounded-full h-6 w-6 border-2 border-brand-200 border-t-brand-600"></div>
                </div>
              } @else if (members().length > 0) {
                <div class="space-y-2">
                  @for (m of members(); track m.id) {
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-500/20 flex items-center justify-center text-xs font-bold text-brand-600 dark:text-brand-400">
                          {{ getMemberInitials(m.person_id) }}
                        </div>
                        <div>
                          <p class="text-sm font-medium text-gray-800 dark:text-white/90">{{ getMemberName(m.person_id) }}</p>
                          <p class="text-xs text-gray-400 dark:text-gray-500 capitalize">{{ m.role }}</p>
                        </div>
                      </div>
                      <button (click)="removeMember(m.person_id)"
                        class="text-error-500 hover:text-error-600 dark:text-error-400 transition">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                      </button>
                    </div>
                  }
                </div>
              } @else {
                <p class="text-center text-sm text-gray-400 dark:text-gray-500 py-6">Este grupo no tiene miembros aún.</p>
              }
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class GroupsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  groupTypes = signal<GroupType[]>([]);
  groups = signal<Group[]>([]);
  filterType = signal<string | null>(null);

  // Group type modal
  showTypeModal = false;
  typeForm = { name: '', code: '' };

  // Group modal
  showGroupModal = false;
  groupForm = { group_type_id: '', name: '', description: '' };

  // Members panel
  showMembersPanel = false;
  selectedGroup: Group | null = null;
  members = signal<GroupMember[]>([]);
  loadingMembers = signal(false);
  memberSearch = '';
  personResults = signal<PersonResult[]>([]);
  private personCache: Record<string, PersonResult> = {};
  private searchTimeout: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.loadGroupTypes();
    this.loadGroups();
  }

  private loadGroupTypes(): void {
    this.api.get<GroupType[]>('/groups/types').subscribe({
      next: (types) => this.groupTypes.set(types),
    });
  }

  loadGroups(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.filterType()) params['type_code'] = this.filterType()!;

    this.api.get<Group[]>('/groups/', params).subscribe({
      next: (groups) => {
        this.groups.set(groups);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  getTypeName(typeId: string): string {
    return this.groupTypes().find(t => t.id === typeId)?.name || '';
  }

  // --- Group Type ---
  createGroupType(): void {
    if (!this.typeForm.name || !this.typeForm.code) return;
    this.api.post<GroupType>('/groups/types', { ...this.typeForm, app_code: 'church' }).subscribe({
      next: (gt) => {
        this.groupTypes.update(list => [...list, gt]);
        this.showTypeModal = false;
        this.typeForm = { name: '', code: '' };
        this.notify.show({ type: 'success', title: 'Creado', message: 'Tipo de grupo creado' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el tipo' }),
    });
  }

  // --- Group ---
  openGroupModal(): void {
    this.groupForm = { group_type_id: '', name: '', description: '' };
    this.showGroupModal = true;
  }

  createGroup(): void {
    if (!this.groupForm.group_type_id || !this.groupForm.name) return;
    this.api.post<Group>('/groups/', this.groupForm).subscribe({
      next: () => {
        this.showGroupModal = false;
        this.loadGroups();
        this.notify.show({ type: 'success', title: 'Creado', message: 'Grupo creado correctamente' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el grupo' }),
    });
  }

  // --- Members ---
  openMembersPanel(group: Group): void {
    this.selectedGroup = group;
    this.showMembersPanel = true;
    this.memberSearch = '';
    this.personResults.set([]);
    this.loadMembers(group.id);
  }

  private loadMembers(groupId: string): void {
    this.loadingMembers.set(true);
    this.api.get<GroupMember[]>(`/groups/${groupId}/members`).subscribe({
      next: (members) => {
        this.members.set(members);
        this.loadingMembers.set(false);
        // Cache person names
        members.forEach(m => this.cachePersonName(m.person_id));
      },
      error: () => this.loadingMembers.set(false),
    });
  }

  private cachePersonName(personId: string): void {
    if (this.personCache[personId]) return;
    this.api.get<any>(`/people/${personId}`).subscribe({
      next: (p) => {
        this.personCache[personId] = { id: p.id, first_name: p.first_name, last_name: p.last_name };
      },
    });
  }

  getMemberName(personId: string): string {
    const p = this.personCache[personId];
    return p ? `${p.first_name} ${p.last_name}` : '...';
  }

  getMemberInitials(personId: string): string {
    const p = this.personCache[personId];
    if (!p) return '..';
    return (p.first_name[0] + p.last_name[0]).toUpperCase();
  }

  searchPersons(): void {
    if (this.searchTimeout) clearTimeout(this.searchTimeout);
    if (this.memberSearch.length < 2) {
      this.personResults.set([]);
      return;
    }
    this.searchTimeout = setTimeout(() => {
      this.api.get<any>('/church/congregants', { search: this.memberSearch, page_size: 5 }).subscribe({
        next: (res) => {
          const items = res.items || res;
          this.personResults.set(
            items.map((c: any) => ({ id: c.person_id, first_name: c.first_name, last_name: c.last_name })),
          );
        },
      });
    }, 300);
  }

  addMember(personId: string): void {
    if (!this.selectedGroup) return;
    this.api.post<GroupMember>(`/groups/${this.selectedGroup.id}/members`, { person_id: personId }).subscribe({
      next: () => {
        this.loadMembers(this.selectedGroup!.id);
        this.memberSearch = '';
        this.personResults.set([]);
        this.notify.show({ type: 'success', title: 'Agregado', message: 'Miembro agregado al grupo' });
      },
      error: (err) => {
        const msg = err.error?.detail || 'No se pudo agregar el miembro';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
      },
    });
  }

  removeMember(personId: string): void {
    if (!this.selectedGroup) return;
    this.api.delete(`/groups/${this.selectedGroup.id}/members/${personId}`).subscribe({
      next: () => {
        this.loadMembers(this.selectedGroup!.id);
        this.notify.show({ type: 'success', title: 'Eliminado', message: 'Miembro removido del grupo' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo remover el miembro' }),
    });
  }
}
