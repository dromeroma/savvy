import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-health-appointments',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Citas Medicas</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Cita</button>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Fecha</th><th class="px-4 py-3 font-medium text-gray-500">Hora</th><th class="px-4 py-3 font-medium text-gray-500">Paciente</th><th class="px-4 py-3 font-medium text-gray-500">Motivo</th><th class="px-4 py-3 font-medium text-gray-500">Monto</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th><th class="px-4 py-3"></th></tr></thead>
        <tbody>@for (a of appointments(); track a.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50">
            <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ a.appointment_date }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ a.start_time }} - {{ a.end_time }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ a.patient_id | slice:0:8 }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ a.reason || '-' }}</td>
            <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">$ {{ a.amount | number:'1.0-0' }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="statusClass(a.status)">{{ statusLabel(a.status) }}</span></td>
            <td class="px-4 py-3">@if (a.status === 'scheduled') { <button (click)="complete(a)" class="px-3 py-1 text-xs rounded-lg bg-green-600 text-white hover:bg-green-700 transition">Completar</button> }</td>
          </tr>
        }</tbody></table></div>
        @if (appointments().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay citas</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Cita</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente</label><select [(ngModel)]="aptForm.patient_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (p of patients(); track p.id) { <option [value]="p.id">{{ p.first_name }} {{ p.last_name }}</option> }</select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profesional</label><select [(ngModel)]="aptForm.provider_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (pr of providers(); track pr.id) { <option [value]="pr.id">Dr. {{ pr.first_name }} {{ pr.last_name }} - {{ pr.specialty }}</option> }</select></div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fecha</label><input type="date" [(ngModel)]="aptForm.appointment_date" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Inicio</label><input [(ngModel)]="aptForm.start_time" placeholder="08:00" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fin</label><input [(ngModel)]="aptForm.end_time" placeholder="08:30" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Motivo</label><input [(ngModel)]="aptForm.reason" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Agendar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class HealthAppointmentsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  appointments = signal<any[]>([]); patients = signal<any[]>([]); providers = signal<any[]>([]); showModal = false;
  aptForm: any = { patient_id: '', provider_id: '', appointment_date: '', start_time: '', end_time: '', reason: '' };
  ngOnInit(): void { this.load(); this.api.get<any>('/health/patients', { page_size: 500 }).subscribe({ next: (r) => this.patients.set(r.items || []) }); this.api.get<any[]>('/health/providers').subscribe({ next: (r) => this.providers.set(r) }); }
  load(): void { this.api.get<any[]>('/health/appointments').subscribe({ next: (r) => this.appointments.set(r) }); }
  save(): void { this.api.post('/health/appointments', this.aptForm).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Agendada', message: 'Cita creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
  complete(a: any): void { this.api.patch(`/health/appointments/${a.id}`, { status: 'completed' }).subscribe({ next: () => { this.notify.show({ type: 'success', title: 'Completada', message: 'Cita completada' }); this.load(); } }); }
  statusLabel(s: string): string { return { scheduled: 'Agendada', confirmed: 'Confirmada', in_progress: 'En curso', completed: 'Completada', cancelled: 'Cancelada', no_show: 'No asistio' }[s] || s; }
  statusClass(s: string): string { return { scheduled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', no_show: 'bg-gray-100 text-gray-600' }[s] || 'bg-yellow-100 text-yellow-700'; }
}
