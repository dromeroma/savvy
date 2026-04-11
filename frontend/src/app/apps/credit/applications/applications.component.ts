import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-applications',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Solicitudes de Crédito</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Solicitudes pendientes y procesadas</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nueva Solicitud</button>
      </div>
      <div class="space-y-4">
        @for (a of applications(); track a.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-800 dark:text-white/90">Monto: <span class="font-mono font-bold">$ {{ a.requested_amount | number:'1.0-0' }}</span> · {{ a.requested_term }} cuotas</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ a.purpose || 'Sin propósito especificado' }} · {{ a.application_date }}</p>
              </div>
              <div class="flex items-center gap-2">
                <span class="px-2 py-1 text-xs rounded-full" [class]="statusClass(a.status)">{{ statusLabel(a.status) }}</span>
                @if (a.status === 'pending') {
                  <button (click)="approve(a)" class="px-3 py-1 text-xs font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 transition">Aprobar</button>
                  <button (click)="reject(a)" class="px-3 py-1 text-xs font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition">Rechazar</button>
                }
              </div>
            </div>
          </div>
        }
        @if (applications().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay solicitudes</p> }
      </div>

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Solicitud</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Prestatario</label><select [(ngModel)]="form.borrower_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">-- Seleccionar --</option>@for (b of borrowers(); track b.id) { <option [value]="b.id">{{ b.first_name }} {{ b.last_name }}</option> }</select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Producto</label><select [(ngModel)]="form.product_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">-- Seleccionar --</option>@for (p of products(); track p.id) { <option [value]="p.id">{{ p.code }} - {{ p.name }}</option> }</select></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Monto</label><input type="number" [(ngModel)]="form.requested_amount" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cuotas</label><input type="number" [(ngModel)]="form.requested_term" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Propósito</label><input [(ngModel)]="form.purpose" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Enviar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ApplicationsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  applications = signal<any[]>([]);
  borrowers = signal<any[]>([]);
  products = signal<any[]>([]);
  showModal = false;
  form: any = { borrower_id: '', product_id: '', requested_amount: 0, requested_term: 12, purpose: '' };

  ngOnInit(): void {
    this.load();
    this.api.get<any>('/credit/borrowers', { page_size: 500 }).subscribe({ next: (r) => this.borrowers.set(r.items || []) });
    this.api.get<any[]>('/credit/products').subscribe({ next: (r) => this.products.set(r) });
  }
  load(): void { this.api.get<any[]>('/credit/applications').subscribe({ next: (r) => this.applications.set(r) }); }
  save(): void {
    this.api.post('/credit/applications', this.form).subscribe({
      next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Solicitud creada' }); this.load(); },
      error: (e: any) => this.notify.show({ type: 'error', title: 'Error', message: e?.error?.detail || 'No se pudo crear' }),
    });
  }
  approve(a: any): void {
    this.api.post(`/credit/applications/${a.id}/decide`, { status: 'approved' }).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Aprobada', message: 'Solicitud aprobada' }); this.load(); },
    });
  }
  reject(a: any): void {
    this.api.post(`/credit/applications/${a.id}/decide`, { status: 'rejected' }).subscribe({
      next: () => { this.notify.show({ type: 'warning', title: 'Rechazada', message: 'Solicitud rechazada' }); this.load(); },
    });
  }
  statusLabel(s: string): string { return { pending: 'Pendiente', under_review: 'En revisión', approved: 'Aprobada', rejected: 'Rechazada', cancelled: 'Cancelada' }[s] || s; }
  statusClass(s: string): string {
    return { pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' }[s] || 'bg-gray-100 text-gray-600';
  }
}
