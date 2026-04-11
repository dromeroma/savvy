import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-scheduling',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Horarios y Salones</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Gestión de espacios y asignación de horarios</p>
        </div>
        <button (click)="showRoomModal = true"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
          + Nuevo Salón
        </button>
      </div>

      <!-- Rooms -->
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Salones</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        @for (room of rooms(); track room.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ room.name }}</h4>
              <span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                {{ roomTypeLabel(room.type) }}
              </span>
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
              @if (room.building) { <p>Edificio: {{ room.building }}</p> }
              <p>Capacidad: {{ room.capacity }} personas</p>
            </div>
          </div>
        }
        @if (rooms().length === 0) {
          <p class="text-sm text-gray-400 dark:text-gray-500 col-span-full text-center py-4">No hay salones registrados</p>
        }
      </div>

      <!-- Schedule Assignment -->
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Horarios por Sección</h3>
        <button (click)="showScheduleModal = true"
          class="px-3 py-1.5 text-xs font-medium rounded-lg border border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition">
          + Asignar Horario
        </button>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Sección</th>
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Día</th>
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Hora</th>
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Salón</th>
                <th class="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              @for (sch of schedules(); track sch.id) {
                <tr class="border-b border-gray-100 dark:border-gray-700/50">
                  <td class="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">{{ getSectionCode(sch.section_id) }}</td>
                  <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ dayLabel(sch.day_of_week) }}</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ sch.start_time }} - {{ sch.end_time }}</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ getRoomName(sch.room_id) }}</td>
                  <td class="px-4 py-3">
                    <button (click)="deleteSchedule(sch.id)" class="text-red-500 hover:text-red-700 text-xs">Eliminar</button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        @if (schedules().length === 0) {
          <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-6">No hay horarios asignados</p>
        }
      </div>

      <!-- Room Modal -->
      @if (showRoomModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showRoomModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Salón</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                <input [(ngModel)]="roomForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Edificio</label>
                  <input [(ngModel)]="roomForm.building" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidad</label>
                  <input type="number" [(ngModel)]="roomForm.capacity" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
                <select [(ngModel)]="roomForm.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="classroom">Aula</option>
                  <option value="lab">Laboratorio</option>
                  <option value="auditorium">Auditorio</option>
                  <option value="virtual">Virtual</option>
                </select>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showRoomModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="saveRoom()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }

      <!-- Schedule Modal -->
      @if (showScheduleModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showScheduleModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Asignar Horario</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Sección</label>
                <select [(ngModel)]="schForm.section_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">-- Seleccionar --</option>
                  @for (s of sections(); track s.id) {
                    <option [value]="s.id">{{ s.code }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Salón</label>
                <select [(ngModel)]="schForm.room_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">-- Sin salón --</option>
                  @for (r of rooms(); track r.id) {
                    <option [value]="r.id">{{ r.name }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Día</label>
                <select [(ngModel)]="schForm.day_of_week" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  @for (d of days; track d.value) {
                    <option [ngValue]="d.value">{{ d.label }}</option>
                  }
                </select>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hora inicio</label>
                  <input [(ngModel)]="schForm.start_time" placeholder="08:00" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hora fin</label>
                  <input [(ngModel)]="schForm.end_time" placeholder="10:00" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showScheduleModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="saveSchedule()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class SchedulingComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  rooms = signal<any[]>([]);
  sections = signal<any[]>([]);
  schedules = signal<any[]>([]);

  showRoomModal = false;
  showScheduleModal = false;

  roomForm: any = { name: '', building: '', capacity: 30, type: 'classroom' };
  schForm: any = { section_id: '', room_id: '', day_of_week: 0, start_time: '', end_time: '' };

  readonly days = [
    { value: 0, label: 'Lunes' }, { value: 1, label: 'Martes' }, { value: 2, label: 'Miércoles' },
    { value: 3, label: 'Jueves' }, { value: 4, label: 'Viernes' }, { value: 5, label: 'Sábado' }, { value: 6, label: 'Domingo' },
  ];

  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.api.get<any[]>('/edu/scheduling/rooms').subscribe({ next: (r) => this.rooms.set(r) });
    this.api.get<any[]>('/edu/enrollment/sections').subscribe({ next: (r) => this.sections.set(r) });
    this.api.get<any[]>('/edu/scheduling/schedules').subscribe({ next: (r) => this.schedules.set(r) });
  }

  saveRoom(): void {
    const payload: any = { name: this.roomForm.name, capacity: this.roomForm.capacity, type: this.roomForm.type };
    if (this.roomForm.building) payload.building = this.roomForm.building;

    this.api.post('/edu/scheduling/rooms', payload).subscribe({
      next: () => {
        this.showRoomModal = false;
        this.roomForm = { name: '', building: '', capacity: 30, type: 'classroom' };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Salón creado' });
        this.loadAll();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el salón' }),
    });
  }

  saveSchedule(): void {
    const payload: any = {
      section_id: this.schForm.section_id,
      day_of_week: this.schForm.day_of_week,
      start_time: this.schForm.start_time,
      end_time: this.schForm.end_time,
    };
    if (this.schForm.room_id) payload.room_id = this.schForm.room_id;

    this.api.post('/edu/scheduling/schedules', payload).subscribe({
      next: () => {
        this.showScheduleModal = false;
        this.schForm = { section_id: '', room_id: '', day_of_week: 0, start_time: '', end_time: '' };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Horario asignado' });
        this.loadAll();
      },
      error: (err: any) => {
        const msg = err?.error?.detail || 'No se pudo asignar el horario';
        this.notify.show({ type: 'error', title: 'Conflicto', message: msg });
      },
    });
  }

  deleteSchedule(id: string): void {
    this.api.delete(`/edu/scheduling/schedules/${id}`).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Listo', message: 'Horario eliminado' }); this.loadAll(); },
    });
  }

  dayLabel(d: number): string { return this.days[d]?.label || ''; }
  roomTypeLabel(t: string): string { return { classroom: 'Aula', lab: 'Lab', auditorium: 'Auditorio', virtual: 'Virtual' }[t] || t; }
  getSectionCode(id: string): string { return this.sections().find((s) => s.id === id)?.code || id; }
  getRoomName(id: string): string { if (!id) return '-'; return this.rooms().find((r) => r.id === id)?.name || '-'; }
}
