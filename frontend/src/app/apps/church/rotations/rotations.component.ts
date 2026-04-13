import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface Rotation {
  id: string;
  name: string;
  rotation_type: string;
  description: string | null;
  frequency: string;
  active: boolean;
  created_at: string;
}

interface Assignment {
  id: string;
  rotation_id: string;
  person_id: string;
  event_id: string | null;
  assignment_date: string;
  role: string | null;
  status: string;
  notes: string | null;
}

interface PersonLite {
  person_id: string;
  first_name: string;
  last_name: string;
}

@Component({
  selector: 'app-church-rotations',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Rotaciones Operativas</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Ujieres, adoración, limpieza y asignaciones por culto</p>
        </div>
        <button (click)="showRotationModal = true"
          class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">
          + Nueva rotación
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (rotations().length > 0) {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          @for (r of rotations(); track r.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-theme-md transition">
              <div class="flex items-start justify-between mb-2">
                <div>
                  <h3 class="text-base font-semibold text-gray-800 dark:text-white/90">{{ r.name }}</h3>
                  <p class="text-xs text-gray-500 capitalize">{{ r.rotation_type }} · {{ r.frequency }}</p>
                </div>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  [ngClass]="r.active ? 'bg-success-100 text-success-700 dark:bg-success-500/20 dark:text-success-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                  {{ r.active ? 'Activa' : 'Inactiva' }}
                </span>
              </div>
              @if (r.description) { <p class="text-xs text-gray-500 mb-3">{{ r.description }}</p> }
              <button (click)="openAssignmentsPanel(r)" class="mt-2 text-xs px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
                Ver asignaciones
              </button>
            </div>
          }
        </div>
      } @else {
        <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p class="text-gray-500 dark:text-gray-400">No hay rotaciones creadas.</p>
        </div>
      }

      <!-- Rotation modal -->
      @if (showRotationModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nueva rotación</h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                <input type="text" [(ngModel)]="rotForm.name" placeholder="Ujieres domingo mañana"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Tipo *</label>
                <select [(ngModel)]="rotForm.rotation_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm">
                  <option value="ushers">Ujieres</option>
                  <option value="worship_team">Adoración</option>
                  <option value="cleaning">Limpieza</option>
                  <option value="security">Seguridad</option>
                  <option value="kids">Niños</option>
                  <option value="welcome">Recepción</option>
                  <option value="other">Otro</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Frecuencia</label>
                <select [(ngModel)]="rotForm.frequency" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm">
                  <option value="weekly">Semanal</option>
                  <option value="biweekly">Quincenal</option>
                  <option value="monthly">Mensual</option>
                  <option value="event_based">Por evento</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="rotForm.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm resize-none"></textarea>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showRotationModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="createRotation()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Crear</button>
            </div>
          </div>
        </div>
      }

      <!-- Assignments panel -->
      @if (showAssignmentsPanel && selectedRotation) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl max-h-[85vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Asignaciones — {{ selectedRotation.name }}</h3>
              <button (click)="closePanels()" class="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div class="p-6 overflow-y-auto flex-1 space-y-3">
              <div class="rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-4 space-y-2">
                <p class="text-xs font-medium text-gray-600 dark:text-gray-400">Nueva asignación</p>
                <div class="relative">
                  <input type="text" [(ngModel)]="personSearch" (input)="searchPersons()" placeholder="Buscar persona..."
                    class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                  @if (personResults().length > 0) {
                    <div class="absolute z-10 top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                      @for (p of personResults(); track p.person_id) {
                        <button (click)="selectPerson(p)" class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-white/90">
                          {{ p.first_name }} {{ p.last_name }}
                        </button>
                      }
                    </div>
                  }
                </div>
                @if (assignForm.person_id) {
                  <p class="text-xs text-gray-500">Seleccionado: {{ getPersonName(assignForm.person_id) }}</p>
                }
                <input type="date" [(ngModel)]="assignForm.assignment_date" class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                <input type="text" [(ngModel)]="assignForm.role" placeholder="Rol (opcional)" class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                <button (click)="createAssignment()" [disabled]="!assignForm.person_id" class="w-full px-3 py-1.5 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-sm rounded-lg">
                  Asignar
                </button>
              </div>
              @if (assignments().length > 0) {
                @for (a of assignments(); track a.id) {
                  <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <div>
                      <p class="text-sm font-medium text-gray-800 dark:text-white/90">{{ getPersonName(a.person_id) }}</p>
                      <p class="text-xs text-gray-500">{{ a.assignment_date }} · {{ a.role || 'Sin rol' }}</p>
                    </div>
                    <span class="text-xs px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-400 capitalize">{{ a.status }}</span>
                  </div>
                }
              } @else {
                <p class="text-center text-sm text-gray-400 py-4">Sin asignaciones.</p>
              }
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ChurchRotationsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  rotations = signal<Rotation[]>([]);
  assignments = signal<Assignment[]>([]);

  showRotationModal = false;
  rotForm: any = { name: '', rotation_type: 'ushers', frequency: 'weekly', description: '' };

  selectedRotation: Rotation | null = null;
  showAssignmentsPanel = false;

  personSearch = '';
  personResults = signal<PersonLite[]>([]);
  private personCache: Record<string, PersonLite> = {};
  private searchTimeout: ReturnType<typeof setTimeout> | null = null;

  assignForm: any = { person_id: '', assignment_date: new Date().toISOString().split('T')[0], role: '' };

  ngOnInit(): void {
    this.loadRotations();
  }

  loadRotations(): void {
    this.loading.set(true);
    this.api.get<Rotation[]>('/church/rotations').subscribe({
      next: (r) => { this.rotations.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  createRotation(): void {
    if (!this.rotForm.name) return;
    this.api.post<Rotation>('/church/rotations', this.rotForm).subscribe({
      next: () => {
        this.showRotationModal = false;
        this.rotForm = { name: '', rotation_type: 'ushers', frequency: 'weekly', description: '' };
        this.loadRotations();
        this.notify.show({ type: 'success', title: 'Creada', message: 'Rotación creada' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }

  openAssignmentsPanel(r: Rotation): void {
    this.selectedRotation = r;
    this.showAssignmentsPanel = true;
    this.assignForm = { person_id: '', assignment_date: new Date().toISOString().split('T')[0], role: '' };
    this.loadAssignments(r.id);
  }

  closePanels(): void {
    this.showAssignmentsPanel = false;
    this.selectedRotation = null;
  }

  private loadAssignments(rotationId: string): void {
    this.api.get<Assignment[]>('/church/rotations/assignments/list', { rotation_id: rotationId }).subscribe({
      next: (a) => {
        this.assignments.set(a);
        a.forEach(x => this.cachePerson(x.person_id));
      },
    });
  }

  private cachePerson(personId: string): void {
    if (this.personCache[personId]) return;
    this.api.get<any>(`/people/${personId}`).subscribe({
      next: (p) => {
        this.personCache[personId] = { person_id: p.id, first_name: p.first_name, last_name: p.last_name };
      },
    });
  }

  getPersonName(personId: string): string {
    const p = this.personCache[personId];
    return p ? `${p.first_name} ${p.last_name}` : '...';
  }

  searchPersons(): void {
    if (this.searchTimeout) clearTimeout(this.searchTimeout);
    if (this.personSearch.length < 2) { this.personResults.set([]); return; }
    this.searchTimeout = setTimeout(() => {
      this.api.get<any>('/church/congregants', { search: this.personSearch, page_size: 5 }).subscribe({
        next: (res) => {
          const items = res.items || res;
          this.personResults.set(
            items.map((c: any) => ({ person_id: c.person_id, first_name: c.first_name, last_name: c.last_name })),
          );
        },
      });
    }, 300);
  }

  selectPerson(p: PersonLite): void {
    this.assignForm.person_id = p.person_id;
    this.personCache[p.person_id] = p;
    this.personSearch = `${p.first_name} ${p.last_name}`;
    this.personResults.set([]);
  }

  createAssignment(): void {
    if (!this.selectedRotation || !this.assignForm.person_id) return;
    this.api.post<Assignment>('/church/rotations/assignments', {
      rotation_id: this.selectedRotation.id,
      ...this.assignForm,
    }).subscribe({
      next: () => {
        this.personSearch = '';
        this.assignForm = { person_id: '', assignment_date: new Date().toISOString().split('T')[0], role: '' };
        this.loadAssignments(this.selectedRotation!.id);
        this.notify.show({ type: 'success', title: 'Asignado', message: 'Asignación creada' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo asignar' }),
    });
  }
}
