import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-health-patients',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Pacientes</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Paciente</button>
      </div>
      <div class="mb-4"><input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar por nombre, documento..." class="w-full sm:w-80 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Nombre</th><th class="px-4 py-3 font-medium text-gray-500">Documento</th><th class="px-4 py-3 font-medium text-gray-500">Sangre</th><th class="px-4 py-3 font-medium text-gray-500">Alergias</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th></tr></thead>
        <tbody>@for (p of patients(); track p.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/5 transition">
            <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ p.first_name }} {{ p.last_name }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ p.document_number || '-' }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ p.blood_type || '-' }}</td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ p.allergies.length > 0 ? p.allergies.join(', ') : 'Ninguna' }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">{{ p.status }}</span></td>
          </tr>
        }</tbody></table></div>
        @if (patients().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay pacientes</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto custom-scrollbar p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Paciente</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.first_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Apellido</label><input [(ngModel)]="form.last_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Documento</label><input [(ngModel)]="form.document_number" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo Sangre</label><select [(ngModel)]="form.blood_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">--</option><option value="O+">O+</option><option value="O-">O-</option><option value="A+">A+</option><option value="A-">A-</option><option value="B+">B+</option><option value="B-">B-</option><option value="AB+">AB+</option><option value="AB-">AB-</option></select></div></div>
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label><input [(ngModel)]="form.email" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefono</label><input [(ngModel)]="form.phone" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class HealthPatientsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  patients = signal<any[]>([]); showModal = false; search = '';
  form: any = { first_name: '', last_name: '', document_number: '', blood_type: '', email: '', phone: '' };
  ngOnInit(): void { this.load(); }
  load(): void { const p: any = { page_size: 100 }; if (this.search) p.search = this.search; this.api.get<any>('/health/patients', p).subscribe({ next: (r) => this.patients.set(r.items || []) }); }
  save(): void { const payload: any = { first_name: this.form.first_name, last_name: this.form.last_name }; if (this.form.document_number) payload.document_number = this.form.document_number; if (this.form.blood_type) payload.blood_type = this.form.blood_type; if (this.form.email) payload.email = this.form.email; if (this.form.phone) payload.phone = this.form.phone; this.api.post('/health/patients', payload).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Paciente creado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
