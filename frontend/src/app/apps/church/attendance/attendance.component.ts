import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface ChurchEvent { id: string; name: string; date: string; type: string; status: string; }
interface AttendanceSummary { event_id: string; event_name: string; event_date: string; total: number; present: number; absent: number; late: number; }
interface AttendanceRecord { person_id: string; status: string; }
interface PersonResult { id: string; person_id: string; first_name: string; last_name: string; }

@Component({
  selector: 'app-attendance',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Asistencia</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Registro y seguimiento de asistencia a eventos</p>
        </div>
        <button (click)="openRecordModal()"
          class="px-4 py-2.5 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition shadow-theme-xs shrink-0">
          + Registrar asistencia
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        @if (summaries().length > 0) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Evento</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Fecha</th>
                    <th class="text-center px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Total</th>
                    <th class="text-center px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Presentes</th>
                    <th class="text-center px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden sm:table-cell">Ausentes</th>
                    <th class="text-center px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden sm:table-cell">Tarde</th>
                  </tr>
                </thead>
                <tbody>
                  @for (s of summaries(); track s.event_id) {
                    <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/[0.02]">
                      <td class="px-6 py-4 font-medium text-gray-800 dark:text-white/90">{{ s.event_name }}</td>
                      <td class="px-6 py-4 text-gray-600 dark:text-gray-300">{{ s.event_date }}</td>
                      <td class="px-6 py-4 text-center text-gray-800 dark:text-white/90 font-semibold">{{ s.total }}</td>
                      <td class="px-6 py-4 text-center text-success-600 dark:text-success-400 font-semibold">{{ s.present }}</td>
                      <td class="px-6 py-4 text-center text-error-600 dark:text-error-400 font-semibold hidden sm:table-cell">{{ s.absent }}</td>
                      <td class="px-6 py-4 text-center text-yellow-600 dark:text-yellow-400 font-semibold hidden sm:table-cell">{{ s.late }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>
        } @else {
          <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <p class="text-gray-500 dark:text-gray-400">No hay registros de asistencia.</p>
            <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Crea un evento primero y luego registra la asistencia.</p>
          </div>
        }
      }

      <!-- Record Attendance Modal -->
      @if (showRecordModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl max-h-[85vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 shrink-0">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Registrar asistencia</h3>
            </div>
            <div class="p-6 overflow-y-auto flex-1 min-h-0 space-y-4">
              <!-- Select event -->
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Evento *</label>
                <select [(ngModel)]="selectedEventId"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition">
                  <option value="">Seleccionar evento...</option>
                  @for (ev of availableEvents(); track ev.id) {
                    <option [value]="ev.id">{{ ev.name }} ({{ ev.date }})</option>
                  }
                </select>
              </div>

              <!-- Search and add person -->
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Agregar congregante</label>
                <div class="relative">
                  <input type="text" [(ngModel)]="personSearch" (input)="searchPersons()" placeholder="Buscar por nombre..."
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                  @if (personResults().length > 0) {
                    <div class="absolute z-10 top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                      @for (p of personResults(); track p.id) {
                        <button (click)="addAttendee(p)" class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-white/90">
                          {{ p.first_name }} {{ p.last_name }}
                        </button>
                      }
                    </div>
                  }
                </div>
              </div>

              <!-- Attendees list -->
              @if (attendees.length > 0) {
                <div class="space-y-2">
                  @for (a of attendees; track a.person_id) {
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <span class="text-sm text-gray-800 dark:text-white/90">{{ a.name }}</span>
                      <div class="flex items-center gap-2">
                        <select [(ngModel)]="a.status" class="text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800">
                          <option value="present">Presente</option>
                          <option value="late">Tarde</option>
                          <option value="absent">Ausente</option>
                        </select>
                        <button (click)="removeAttendee(a.person_id)" class="text-error-500 hover:text-error-600">
                          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                        </button>
                      </div>
                    </div>
                  }
                </div>
              }
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3 shrink-0">
              <button (click)="showRecordModal = false"
                class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">Cancelar</button>
              <button (click)="saveAttendance()" [disabled]="!selectedEventId || attendees.length === 0"
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition disabled:opacity-50">
                Guardar ({{ attendees.length }})
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class AttendanceComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  summaries = signal<AttendanceSummary[]>([]);
  availableEvents = signal<ChurchEvent[]>([]);

  showRecordModal = false;
  selectedEventId = '';
  personSearch = '';
  personResults = signal<PersonResult[]>([]);
  attendees: { person_id: string; name: string; status: string }[] = [];
  private searchTimeout: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.loadSummaries();
  }

  private loadSummaries(): void {
    this.api.get<AttendanceSummary[]>('/church/attendance/summary').subscribe({
      next: (data) => { this.summaries.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openRecordModal(): void {
    this.selectedEventId = '';
    this.attendees = [];
    this.personSearch = '';
    this.personResults.set([]);
    this.showRecordModal = true;
    this.api.get<ChurchEvent[]>('/church/events/', { status: 'scheduled' }).subscribe({
      next: (events) => this.availableEvents.set(events),
    });
  }

  searchPersons(): void {
    if (this.searchTimeout) clearTimeout(this.searchTimeout);
    if (this.personSearch.length < 2) { this.personResults.set([]); return; }
    this.searchTimeout = setTimeout(() => {
      this.api.get<any>('/church/congregants', { search: this.personSearch, page_size: 5 }).subscribe({
        next: (res) => {
          const items = res.items || res;
          this.personResults.set(
            items.map((c: any) => ({ id: c.id, person_id: c.person_id, first_name: c.first_name, last_name: c.last_name })),
          );
        },
      });
    }, 300);
  }

  addAttendee(p: PersonResult): void {
    if (this.attendees.some(a => a.person_id === p.person_id)) return;
    this.attendees.push({ person_id: p.person_id, name: `${p.first_name} ${p.last_name}`, status: 'present' });
    this.personSearch = '';
    this.personResults.set([]);
  }

  removeAttendee(personId: string): void {
    this.attendees = this.attendees.filter(a => a.person_id !== personId);
  }

  saveAttendance(): void {
    const body = {
      event_id: this.selectedEventId,
      records: this.attendees.map(a => ({ person_id: a.person_id, status: a.status })),
    };
    this.api.post('/church/attendance/', body).subscribe({
      next: () => {
        this.showRecordModal = false;
        this.loadSummaries();
        this.notify.show({ type: 'success', title: 'Guardado', message: `Asistencia registrada (${this.attendees.length} personas)` });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'Error al guardar asistencia' }),
    });
  }
}
