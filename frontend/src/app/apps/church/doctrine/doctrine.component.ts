import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface DoctrineGroup {
  id: string;
  name: string;
  teacher_person_id: string | null;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  meeting_day: string | null;
  meeting_time: string | null;
  location: string | null;
  max_students: number | null;
  status: string;
  created_at: string;
}

interface Enrollment {
  id: string;
  doctrine_group_id: string;
  person_id: string;
  enrolled_at: string;
  progress_pct: number;
  result: string | null;
  result_date: string | null;
  notes: string | null;
}

interface AttendanceRow {
  id: string;
  doctrine_group_id: string;
  person_id: string;
  session_date: string;
  present: boolean;
  notes: string | null;
}

interface PersonLite {
  id: string;
  person_id: string;
  first_name: string;
  last_name: string;
}

@Component({
  selector: 'app-church-doctrine',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Grupos de Doctrina</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Clases pre-bautismo con maestro, asistencia y progreso</p>
        </div>
        <button (click)="openGroupModal()"
          class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">
          + Nuevo grupo
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (groups().length > 0) {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          @for (g of groups(); track g.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-theme-md transition">
              <div class="flex items-start justify-between mb-2">
                <h3 class="text-base font-semibold text-gray-800 dark:text-white/90">{{ g.name }}</h3>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  [ngClass]="g.status === 'active' ? 'bg-success-100 text-success-700 dark:bg-success-500/20 dark:text-success-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                  {{ g.status }}
                </span>
              </div>
              @if (g.description) { <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">{{ g.description }}</p> }
              <div class="text-xs text-gray-500 dark:text-gray-400 space-y-0.5">
                @if (g.meeting_day) { <p>📅 {{ g.meeting_day }} {{ g.meeting_time || '' }}</p> }
                @if (g.location) { <p>📍 {{ g.location }}</p> }
                @if (g.start_date) { <p>Inicio: {{ g.start_date }}</p> }
              </div>
              <div class="mt-4 flex gap-2">
                <button (click)="openEnrollPanel(g)" class="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition">
                  Alumnos
                </button>
                <button (click)="openAttendancePanel(g)" class="text-xs px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
                  Asistencia
                </button>
              </div>
            </div>
          }
        </div>
      } @else {
        <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p class="text-gray-500 dark:text-gray-400">No hay grupos de doctrina.</p>
        </div>
      }

      <!-- Group modal -->
      @if (showGroupModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nuevo grupo de doctrina</h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                <input type="text" [(ngModel)]="groupForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="groupForm.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm resize-none"></textarea>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Día</label>
                  <input type="text" [(ngModel)]="groupForm.meeting_day" placeholder="martes" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Hora</label>
                  <input type="time" [(ngModel)]="groupForm.meeting_time" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Ubicación</label>
                <input type="text" [(ngModel)]="groupForm.location" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Inicio</label>
                  <input type="date" [(ngModel)]="groupForm.start_date" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Cupo</label>
                  <input type="number" [(ngModel)]="groupForm.max_students" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                </div>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showGroupModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">Cancelar</button>
              <button (click)="createGroup()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">Crear</button>
            </div>
          </div>
        </div>
      }

      <!-- Enroll / students panel -->
      @if (showEnrollPanel && selectedGroup) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl max-h-[85vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Alumnos — {{ selectedGroup.name }}</h3>
              <button (click)="closePanels()" class="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div class="p-6 overflow-y-auto flex-1">
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Agregar alumno</label>
                <div class="relative">
                  <input type="text" [(ngModel)]="personSearch" (input)="searchPersons()" placeholder="Buscar congregante..."
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                  @if (personResults().length > 0) {
                    <div class="absolute z-10 top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                      @for (p of personResults(); track p.id) {
                        <button (click)="enrollPerson(p)" class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-white/90 transition">
                          {{ p.first_name }} {{ p.last_name }}
                        </button>
                      }
                    </div>
                  }
                </div>
              </div>
              @if (enrollments().length > 0) {
                <div class="space-y-2">
                  @for (e of enrollments(); track e.id) {
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <div>
                        <p class="text-sm font-medium text-gray-800 dark:text-white/90">{{ getPersonName(e.person_id) }}</p>
                        <p class="text-xs text-gray-500">Inscrito: {{ e.enrolled_at }}</p>
                      </div>
                      <div class="flex items-center gap-2">
                        <div class="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div class="bg-brand-500 h-full" [style.width.%]="e.progress_pct"></div>
                        </div>
                        <span class="text-xs text-gray-500 w-8 text-right">{{ e.progress_pct }}%</span>
                      </div>
                    </div>
                  }
                </div>
              } @else {
                <p class="text-center text-sm text-gray-400 py-6">Sin alumnos inscritos.</p>
              }
            </div>
          </div>
        </div>
      }

      <!-- Attendance panel -->
      @if (showAttendancePanel && selectedGroup) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl max-h-[85vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
              <div>
                <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Asistencia — {{ selectedGroup.name }}</h3>
                <input type="date" [(ngModel)]="sessionDate" class="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-2 py-1 text-sm" />
              </div>
              <button (click)="closePanels()" class="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div class="p-6 overflow-y-auto flex-1 space-y-2">
              @for (e of enrollments(); track e.id) {
                <label class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg cursor-pointer">
                  <input type="checkbox" [(ngModel)]="attendanceMap[e.person_id]" class="w-4 h-4 rounded border-gray-300 text-brand-500" />
                  <span class="text-sm text-gray-800 dark:text-white/90">{{ getPersonName(e.person_id) }}</span>
                </label>
              }
              @if (enrollments().length === 0) {
                <p class="text-center text-sm text-gray-400 py-6">Inscribe alumnos primero.</p>
              }
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="closePanels()" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="saveAttendance()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ChurchDoctrineComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  groups = signal<DoctrineGroup[]>([]);
  enrollments = signal<Enrollment[]>([]);

  showGroupModal = false;
  groupForm: any = {
    name: '', description: '', meeting_day: '', meeting_time: '',
    location: '', start_date: '', max_students: null,
  };

  selectedGroup: DoctrineGroup | null = null;
  showEnrollPanel = false;
  showAttendancePanel = false;

  personSearch = '';
  personResults = signal<PersonLite[]>([]);
  private personCache: Record<string, PersonLite> = {};
  private searchTimeout: ReturnType<typeof setTimeout> | null = null;

  sessionDate = new Date().toISOString().split('T')[0];
  attendanceMap: Record<string, boolean> = {};

  ngOnInit(): void {
    this.loadGroups();
  }

  loadGroups(): void {
    this.loading.set(true);
    this.api.get<DoctrineGroup[]>('/church/doctrine/groups').subscribe({
      next: (g) => { this.groups.set(g); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openGroupModal(): void {
    this.groupForm = {
      name: '', description: '', meeting_day: '', meeting_time: '',
      location: '', start_date: '', max_students: null,
    };
    this.showGroupModal = true;
  }

  createGroup(): void {
    if (!this.groupForm.name) return;
    const payload: any = { ...this.groupForm };
    Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === null) delete payload[k]; });
    this.api.post<DoctrineGroup>('/church/doctrine/groups', payload).subscribe({
      next: () => {
        this.showGroupModal = false;
        this.loadGroups();
        this.notify.show({ type: 'success', title: 'Creado', message: 'Grupo de doctrina creado' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }

  openEnrollPanel(g: DoctrineGroup): void {
    this.selectedGroup = g;
    this.showEnrollPanel = true;
    this.loadEnrollments(g.id);
  }

  openAttendancePanel(g: DoctrineGroup): void {
    this.selectedGroup = g;
    this.showAttendancePanel = true;
    this.attendanceMap = {};
    this.loadEnrollments(g.id);
  }

  closePanels(): void {
    this.showEnrollPanel = false;
    this.showAttendancePanel = false;
    this.selectedGroup = null;
  }

  private loadEnrollments(groupId: string): void {
    this.api.get<Enrollment[]>(`/church/doctrine/groups/${groupId}/enrollments`).subscribe({
      next: (rows) => {
        this.enrollments.set(rows);
        rows.forEach(r => this.cachePerson(r.person_id));
      },
    });
  }

  private cachePerson(personId: string): void {
    if (this.personCache[personId]) return;
    this.api.get<any>(`/people/${personId}`).subscribe({
      next: (p) => {
        this.personCache[personId] = {
          id: p.id, person_id: p.id, first_name: p.first_name, last_name: p.last_name,
        };
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
            items.map((c: any) => ({ id: c.person_id, person_id: c.person_id, first_name: c.first_name, last_name: c.last_name })),
          );
        },
      });
    }, 300);
  }

  enrollPerson(p: PersonLite): void {
    if (!this.selectedGroup) return;
    this.api.post<Enrollment>('/church/doctrine/enrollments', {
      doctrine_group_id: this.selectedGroup.id,
      person_id: p.person_id,
    }).subscribe({
      next: () => {
        this.personSearch = '';
        this.personResults.set([]);
        this.loadEnrollments(this.selectedGroup!.id);
        this.notify.show({ type: 'success', title: 'Inscrito', message: 'Alumno inscrito' });
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo inscribir',
      }),
    });
  }

  saveAttendance(): void {
    if (!this.selectedGroup) return;
    const entries = this.enrollments().map(e => ({
      person_id: e.person_id,
      present: !!this.attendanceMap[e.person_id],
    }));
    this.api.post('/church/doctrine/attendance/bulk', {
      doctrine_group_id: this.selectedGroup.id,
      session_date: this.sessionDate,
      entries,
    }).subscribe({
      next: () => {
        this.closePanels();
        this.notify.show({ type: 'success', title: 'Guardado', message: 'Asistencia registrada' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo guardar' }),
    });
  }
}
