import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-health-clinical',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Historias Clinicas</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Registro</button>
      </div>
      <div class="space-y-4">
        @for (r of records(); track r.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2"><span class="text-sm text-gray-500">{{ r.record_date }}</span><span class="px-2 py-0.5 text-xs rounded-full" [class]="r.status === 'signed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'">{{ r.status }}</span></div>
            </div>
            @if (r.chief_complaint) { <p class="text-sm text-gray-700 dark:text-gray-300"><strong>Motivo:</strong> {{ r.chief_complaint }}</p> }
            @if (r.assessment) { <p class="text-sm text-gray-600 dark:text-gray-400 mt-1"><strong>Valoracion:</strong> {{ r.assessment }}</p> }
            @if (r.plan) { <p class="text-sm text-gray-600 dark:text-gray-400 mt-1"><strong>Plan:</strong> {{ r.plan }}</p> }
          </div>
        }
        @if (records().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay registros clinicos</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto custom-scrollbar p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Registro Clinico</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Paciente</label><select [(ngModel)]="form.patient_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (p of patients(); track p.id) { <option [value]="p.id">{{ p.first_name }} {{ p.last_name }}</option> }</select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fecha</label><input type="date" [(ngModel)]="form.record_date" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Motivo de consulta</label><textarea [(ngModel)]="form.chief_complaint" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Examen fisico</label><textarea [(ngModel)]="form.physical_exam" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valoracion</label><textarea [(ngModel)]="form.assessment" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Plan</label><textarea [(ngModel)]="form.plan" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class HealthClinicalComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  records = signal<any[]>([]); patients = signal<any[]>([]); showModal = false;
  form: any = { patient_id: '', record_date: new Date().toISOString().slice(0, 10), chief_complaint: '', physical_exam: '', assessment: '', plan: '' };
  ngOnInit(): void { this.load(); this.api.get<any>('/health/patients', { page_size: 500 }).subscribe({ next: (r) => this.patients.set(r.items || []) }); }
  load(): void { this.api.get<any[]>('/health/clinical/records').subscribe({ next: (r) => this.records.set(r) }); }
  save(): void { this.api.post('/health/clinical/records', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Registro creado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
