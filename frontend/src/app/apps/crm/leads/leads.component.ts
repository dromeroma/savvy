import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-crm-leads',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Leads</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Prospectos y su estado</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Lead</button>
      </div>
      <div class="space-y-3">
        @for (l of leads(); track l.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 flex justify-between items-center">
            <div>
              <p class="text-sm text-gray-800 dark:text-white/90">Contact: {{ l.contact_id | slice:0:8 }}...</p>
              <div class="flex gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
                <span>Score: {{ l.score }}</span>
                @if (l.source) { <span>Fuente: {{ l.source }}</span> }
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-1 text-xs rounded-full" [class]="statusClass(l.status)">{{ statusLabel(l.status) }}</span>
              @if (l.status === 'new') { <button (click)="qualify(l)" class="px-3 py-1 text-xs rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition">Calificar</button> }
            </div>
          </div>
        }
        @if (leads().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay leads</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Lead</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Contacto</label><select [(ngModel)]="form.contact_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">--</option>@for (c of contacts(); track c.id) { <option [value]="c.id">{{ c.first_name }} {{ c.last_name }}</option> }</select></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fuente</label><input [(ngModel)]="form.source" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Score</label><input type="number" [(ngModel)]="form.score" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CrmLeadsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  leads = signal<any[]>([]);
  contacts = signal<any[]>([]);
  showModal = false;
  form: any = { contact_id: '', source: '', score: 0 };
  ngOnInit(): void {
    this.load();
    this.api.get<any>('/crm/contacts', { page_size: 500 }).subscribe({ next: (r) => this.contacts.set(r.items || []) });
  }
  load(): void { this.api.get<any[]>('/crm/leads').subscribe({ next: (r) => this.leads.set(r) }); }
  save(): void {
    this.api.post('/crm/leads', this.form).subscribe({
      next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Lead creado' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
  qualify(l: any): void {
    this.api.patch(`/crm/leads/${l.id}`, { status: 'qualified' }).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Calificado', message: 'Lead calificado' }); this.load(); },
    });
  }
  statusLabel(s: string): string { return { new: 'Nuevo', contacted: 'Contactado', qualified: 'Calificado', unqualified: 'No calificado', converted: 'Convertido', lost: 'Perdido' }[s] || s; }
  statusClass(s: string): string { return { new: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', qualified: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', converted: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', lost: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' }[s] || 'bg-gray-100 text-gray-600'; }
}
