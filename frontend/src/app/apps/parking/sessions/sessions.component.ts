import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-sessions',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Sesiones de Parqueo</h2><p class="text-sm text-gray-500 dark:text-gray-400">Entradas y salidas</p></div>
        <button (click)="showEntryModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Registrar Entrada</button>
      </div>

      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Activos ({{ activeSessions().length }})</h3>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Placa</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Tipo</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Entrada</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Método</th><th class="px-4 py-3"></th></tr></thead>
          <tbody>@for (s of activeSessions(); track s.id) {
            <tr class="border-b border-gray-100 dark:border-gray-700/50">
              <td class="px-4 py-3 font-mono font-bold text-gray-800 dark:text-white/90">{{ s.plate }}</td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ s.vehicle_type }}</td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ s.entry_time | date:'short' }}</td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ s.entry_method }}</td>
              <td class="px-4 py-3"><button (click)="exitSession(s)" class="px-3 py-1 text-xs font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition">Salida</button></td>
            </tr>
          }</tbody></table>
        </div>
        @if (activeSessions().length === 0) { <p class="text-sm text-gray-400 text-center py-6">No hay vehículos estacionados</p> }
      </div>

      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Completados Hoy</h3>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Placa</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Duración</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Total</th><th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Pago</th></tr></thead>
          <tbody>@for (s of completedSessions(); track s.id) {
            <tr class="border-b border-gray-100 dark:border-gray-700/50">
              <td class="px-4 py-3 font-mono text-gray-800 dark:text-white/90">{{ s.plate }}</td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ s.duration_minutes }} min</td>
              <td class="px-4 py-3 font-mono font-bold text-green-600 dark:text-green-400">$ {{ s.total | number:'1.0-0' }}</td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ s.payment_method || '-' }}</td>
            </tr>
          }</tbody></table>
        </div>
        @if (completedSessions().length === 0) { <p class="text-sm text-gray-400 text-center py-6">No hay sesiones completadas hoy</p> }
      </div>

      @if (showEntryModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showEntryModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Registrar Entrada</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Placa</label><input [(ngModel)]="entryForm.plate" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm uppercase text-center text-lg font-mono" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="entryForm.vehicle_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="car">Carro</option><option value="motorcycle">Moto</option><option value="truck">Camión</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Sede</label><select [(ngModel)]="entryForm.location_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (l of locations(); track l.id) { <option [value]="l.id">{{ l.name }}</option> }</select></div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showEntryModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="registerEntry()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Registrar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class SessionsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  activeSessions = signal<any[]>([]); completedSessions = signal<any[]>([]); locations = signal<any[]>([]);
  showEntryModal = false;
  entryForm: any = { plate: '', vehicle_type: 'car', location_id: '' };
  ngOnInit(): void { this.load(); this.api.get<any[]>('/parking/locations').subscribe({ next: (r) => { this.locations.set(r); if (r.length) this.entryForm.location_id = r[0].id; } }); }
  load(): void {
    this.api.get<any[]>('/parking/sessions/active').subscribe({ next: (r) => this.activeSessions.set(r) });
    this.api.get<any[]>('/parking/sessions/completed').subscribe({ next: (r) => this.completedSessions.set(r) });
  }
  registerEntry(): void {
    this.api.post('/parking/sessions/entry', this.entryForm).subscribe({
      next: () => { this.showEntryModal = false; this.entryForm.plate = ''; this.notify.show({ type: 'success', title: 'Entrada', message: 'Vehículo registrado' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo registrar' }),
    });
  }
  exitSession(s: any): void {
    this.api.post(`/parking/sessions/${s.id}/exit`, { payment_method: 'cash' }).subscribe({
      next: (r: any) => { this.notify.show({ type: 'success', title: 'Salida', message: `${s.plate} — $ ${r.total}` }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo registrar salida' }),
    });
  }
}
