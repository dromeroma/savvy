import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface ChurchEvent {
  id: string;
  name: string;
  type: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  location: string | null;
  description: string | null;
  is_recurring: boolean;
  expected_attendance: number | null;
  status: string;
}

const TYPE_LABELS: Record<string, string> = {
  service: 'Culto',
  event: 'Evento',
  campaign: 'Campaña',
  meeting: 'Reunión',
};

const STATUS_LABELS: Record<string, string> = {
  scheduled: 'Programado',
  completed: 'Completado',
  cancelled: 'Cancelado',
};

@Component({
  selector: 'app-events',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Eventos y Cultos</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Programación de servicios, eventos y actividades</p>
        </div>
        <button (click)="openModal()"
          class="px-4 py-2.5 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition shadow-theme-xs shrink-0">
          + Nuevo evento
        </button>
      </div>

      <!-- Type filters -->
      <div class="flex flex-wrap gap-2 mb-6">
        <button (click)="typeFilter = ''; loadEvents()"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
          [ngClass]="typeFilter === '' ? 'bg-brand-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'">
          Todos
        </button>
        @for (t of typeOptions; track t.key) {
          <button (click)="typeFilter = t.key; loadEvents()"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
            [ngClass]="typeFilter === t.key ? 'bg-brand-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'">
            {{ t.label }}
          </button>
        }
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        @if (events().length > 0) {
          <div class="space-y-3">
            @for (ev of events(); track ev.id) {
              <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-theme-md transition">
                <div class="flex items-start justify-between gap-4">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <h3 class="text-base font-semibold text-gray-800 dark:text-white/90">{{ ev.name }}</h3>
                      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-400">
                        {{ getTypeLabel(ev.type) }}
                      </span>
                    </div>
                    <div class="flex flex-wrap gap-4 text-sm text-gray-500 dark:text-gray-400">
                      <span>{{ ev.date }}</span>
                      @if (ev.start_time) {
                        <span>{{ ev.start_time }}{{ ev.end_time ? ' - ' + ev.end_time : '' }}</span>
                      }
                      @if (ev.location) {
                        <span>{{ ev.location }}</span>
                      }
                    </div>
                    @if (ev.description) {
                      <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">{{ ev.description }}</p>
                    }
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <select [(ngModel)]="ev.status" (ngModelChange)="updateEventStatus(ev)"
                      class="text-xs px-2 py-1 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300">
                      <option value="scheduled">Programado</option>
                      <option value="completed">Completado</option>
                      <option value="cancelled">Cancelado</option>
                    </select>
                  </div>
                </div>
              </div>
            }
          </div>
        } @else {
          <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <p class="text-gray-500 dark:text-gray-400">No hay eventos programados.</p>
          </div>
        }
      }

      <!-- Create Modal -->
      @if (showModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nuevo evento</h3>
            </div>
            <div class="p-6 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                <input type="text" [(ngModel)]="form.name"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Tipo *</label>
                  <select [(ngModel)]="form.type"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition">
                    @for (t of typeOptions; track t.key) {
                      <option [value]="t.key">{{ t.label }}</option>
                    }
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Fecha *</label>
                  <input type="date" [(ngModel)]="form.date"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Hora inicio</label>
                  <input type="time" [(ngModel)]="form.start_time"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Hora fin</label>
                  <input type="time" [(ngModel)]="form.end_time"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Ubicación</label>
                <input type="text" [(ngModel)]="form.location"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="form.description" rows="2"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition resize-none"></textarea>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showModal = false"
                class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">Cancelar</button>
              <button (click)="createEvent()" [disabled]="!form.name || !form.date"
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition disabled:opacity-50">Crear</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class EventsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  events = signal<ChurchEvent[]>([]);
  showModal = false;
  typeFilter = '';

  typeOptions = [
    { key: 'service', label: 'Culto' },
    { key: 'event', label: 'Evento' },
    { key: 'campaign', label: 'Campaña' },
    { key: 'meeting', label: 'Reunión' },
  ];

  form = { name: '', type: 'service' as string, date: '', start_time: '', end_time: '', location: '', description: '' };

  ngOnInit(): void {
    this.loadEvents();
  }

  loadEvents(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.typeFilter) params['type'] = this.typeFilter;
    this.api.get<ChurchEvent[]>('/church/events/', params).subscribe({
      next: (data) => { this.events.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openModal(): void {
    this.form = { name: '', type: 'service', date: new Date().toISOString().split('T')[0], start_time: '', end_time: '', location: '', description: '' };
    this.showModal = true;
  }

  createEvent(): void {
    const body: Record<string, any> = { name: this.form.name, type: this.form.type, date: this.form.date };
    if (this.form.start_time) body['start_time'] = this.form.start_time;
    if (this.form.end_time) body['end_time'] = this.form.end_time;
    if (this.form.location) body['location'] = this.form.location;
    if (this.form.description) body['description'] = this.form.description;

    this.api.post('/church/events/', body).subscribe({
      next: () => {
        this.showModal = false;
        this.loadEvents();
        this.notify.show({ type: 'success', title: 'Creado', message: 'Evento creado correctamente' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'Error al crear evento' }),
    });
  }

  updateEventStatus(ev: ChurchEvent): void {
    this.api.patch(`/church/events/${ev.id}`, { status: ev.status }).subscribe({
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'Error al actualizar estado' }),
    });
  }

  getTypeLabel(type: string): string {
    return TYPE_LABELS[type] || type;
  }
}
