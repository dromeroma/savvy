import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-contacts',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Contactos</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Personas en tu CRM</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Contacto</button>
      </div>
      <div class="flex gap-3 mb-4">
        <input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar..." class="w-full sm:w-80 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
        <select [(ngModel)]="lifecycle" (ngModelChange)="load()" class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos</option>
          <option value="subscriber">Suscriptor</option>
          <option value="lead">Lead</option>
          <option value="qualified_lead">Calificado</option>
          <option value="opportunity">Oportunidad</option>
          <option value="customer">Cliente</option>
        </select>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-sm">
            <thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left">
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Nombre</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Email</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Fuente</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Etapa</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Score</th>
            </tr></thead>
            <tbody>
              @for (c of contacts(); track c.id) {
                <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                  <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ c.first_name }} {{ c.last_name }}</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ c.email || '-' }}</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ c.source || '-' }}</td>
                  <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">{{ stageLabel(c.lifecycle_stage) }}</span></td>
                  <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">{{ c.lead_score }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        @if (contacts().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay contactos</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Contacto</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.first_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Apellido</label><input [(ngModel)]="form.last_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label><input [(ngModel)]="form.email" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Teléfono</label><input [(ngModel)]="form.phone" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fuente</label><select [(ngModel)]="form.source" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">--</option><option value="website">Website</option><option value="referral">Referido</option><option value="social_media">Redes</option><option value="cold_call">Llamada</option><option value="event">Evento</option><option value="advertising">Publicidad</option></select></div>
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
export class ContactsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  contacts = signal<any[]>([]);
  showModal = false;
  search = '';
  lifecycle = '';
  form: any = { first_name: '', last_name: '', email: '', phone: '', source: '' };

  ngOnInit(): void { this.load(); }
  load(): void {
    const p: any = { page_size: 100 };
    if (this.search) p.search = this.search;
    if (this.lifecycle) p.lifecycle = this.lifecycle;
    this.api.get<any>('/crm/contacts', p).subscribe({ next: (r) => this.contacts.set(r.items || []) });
  }
  save(): void {
    const payload: any = { first_name: this.form.first_name, last_name: this.form.last_name };
    if (this.form.email) payload.email = this.form.email;
    if (this.form.phone) payload.phone = this.form.phone;
    if (this.form.source) payload.source = this.form.source;
    this.api.post('/crm/contacts', payload).subscribe({
      next: () => { this.showModal = false; this.form = { first_name: '', last_name: '', email: '', phone: '', source: '' }; this.notify.show({ type: 'success', title: 'Listo', message: 'Contacto creado' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
  stageLabel(s: string): string { return { subscriber: 'Suscriptor', lead: 'Lead', qualified_lead: 'Calificado', opportunity: 'Oportunidad', customer: 'Cliente', evangelist: 'Evangelista' }[s] || s; }
}
