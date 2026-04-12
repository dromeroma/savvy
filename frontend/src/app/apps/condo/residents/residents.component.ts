import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-condo-residents',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Residentes y Visitantes</h2></div>
      </div>
      <div class="flex gap-1 mb-6 border-b border-gray-200 dark:border-gray-700">
        <button (click)="tab = 'residents'" class="px-4 py-2.5 text-sm font-medium transition" [class]="tab === 'residents' ? 'text-brand-600 dark:text-brand-400 border-b-2 border-brand-600' : 'text-gray-500'">Residentes</button>
        <button (click)="tab = 'visitors'" class="px-4 py-2.5 text-sm font-medium transition" [class]="tab === 'visitors' ? 'text-brand-600 dark:text-brand-400 border-b-2 border-brand-600' : 'text-gray-500'">Visitantes</button>
      </div>
      @if (tab === 'residents') {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Unidad</th><th class="px-4 py-3 font-medium text-gray-500">Persona</th><th class="px-4 py-3 font-medium text-gray-500">Tipo</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th></tr></thead>
          <tbody>@for (r of residents(); track r.id) { <tr class="border-b border-gray-100 dark:border-gray-700/50"><td class="px-4 py-3 font-mono text-xs text-gray-500">{{ r.unit_id | slice:0:8 }}</td><td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ r.person_id | slice:0:8 }}</td><td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ r.resident_type }}</td><td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">{{ r.status }}</span></td></tr> }</tbody></table></div>
          @if (residents().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay residentes</p> }
        </div>
      }
      @if (tab === 'visitors') {
        <div class="flex justify-end mb-4"><button (click)="showVisitorModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Registrar Visitante</button></div>
        <div class="space-y-3">
          @for (v of visitors(); track v.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex justify-between items-center">
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-white/90">{{ v.visitor_name }}</p>
                <div class="flex gap-3 text-xs text-gray-500 mt-1">
                  @if (v.document_number) { <span>Doc: {{ v.document_number }}</span> }
                  @if (v.vehicle_plate) { <span>Placa: {{ v.vehicle_plate }}</span> }
                  @if (v.purpose) { <span>{{ v.purpose }}</span> }
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="px-2 py-1 text-xs rounded-full" [class]="v.status === 'inside' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-gray-100 text-gray-600'">{{ v.status === 'inside' ? 'Adentro' : 'Salio' }}</span>
                @if (v.status === 'inside') { <button (click)="exitVisitor(v.id)" class="px-3 py-1 text-xs rounded-lg bg-red-600 text-white hover:bg-red-700 transition">Salida</button> }
              </div>
            </div>
          }
          @if (visitors().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay visitantes</p> }
        </div>
      }
      @if (showVisitorModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showVisitorModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Registrar Visitante</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="vForm.visitor_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Documento</label><input [(ngModel)]="vForm.document_number" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Placa</label><input [(ngModel)]="vForm.vehicle_plate" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm uppercase" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Motivo</label><input [(ngModel)]="vForm.purpose" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showVisitorModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="saveVisitor()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Registrar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CondoResidentsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  residents = signal<any[]>([]); visitors = signal<any[]>([]); tab = 'residents'; showVisitorModal = false;
  vForm: any = { visitor_name: '', document_number: '', vehicle_plate: '', purpose: '' };
  ngOnInit(): void { this.load(); }
  load(): void {
    this.api.get<any[]>('/condo/residents').subscribe({ next: (r) => this.residents.set(r) });
    this.api.get<any[]>('/condo/visitors').subscribe({ next: (r) => this.visitors.set(r) });
  }
  saveVisitor(): void { this.api.post('/condo/visitors', this.vForm).subscribe({ next: () => { this.showVisitorModal = false; this.vForm = { visitor_name: '', document_number: '', vehicle_plate: '', purpose: '' }; this.notify.show({ type: 'success', title: 'Listo', message: 'Visitante registrado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo registrar' }) }); }
  exitVisitor(id: string): void { this.api.post(`/condo/visitors/${id}/exit`, {}).subscribe({ next: () => { this.notify.show({ type: 'success', title: 'Salida', message: 'Visitante salio' }); this.load(); } }); }
}
