import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-borrowers',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Prestatarios</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Clientes de crédito</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Prestatario</button>
      </div>
      <div class="mb-4">
        <input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar por nombre, documento..." class="w-full sm:w-80 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-sm">
            <thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left">
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Nombre</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Documento</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Activos</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Saldo</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Riesgo</th>
              <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
            </tr></thead>
            <tbody>
              @for (b of borrowers(); track b.id) {
                <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                  <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ b.first_name }} {{ b.last_name }}</td>
                  <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ b.document_number || '-' }}</td>
                  <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">{{ b.active_loans }}</td>
                  <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">$ {{ b.total_outstanding | number:'1.0-0' }}</td>
                  <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="riskClass(b.risk_level)">{{ riskLabel(b.risk_level) }}</span></td>
                  <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="b.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'">{{ b.status }}</span></td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        @if (borrowers().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay prestatarios</p> }
      </div>

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto custom-scrollbar p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Prestatario</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.first_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Apellido</label><input [(ngModel)]="form.last_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Documento</label><input [(ngModel)]="form.document_number" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Teléfono</label><input [(ngModel)]="form.phone" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Empleador</label><input [(ngModel)]="form.employer" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ingreso mensual</label><input type="number" [(ngModel)]="form.monthly_income" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
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
export class BorrowersComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  borrowers = signal<any[]>([]);
  showModal = false;
  search = '';
  form: any = { first_name: '', last_name: '', document_number: '', phone: '', employer: '', monthly_income: null };

  ngOnInit(): void { this.load(); }
  load(): void {
    const params: any = { page_size: 100 };
    if (this.search) params.search = this.search;
    this.api.get<any>('/credit/borrowers', params).subscribe({ next: (r) => this.borrowers.set(r.items || []) });
  }
  save(): void {
    const p: any = { first_name: this.form.first_name, last_name: this.form.last_name };
    if (this.form.document_number) p.document_number = this.form.document_number;
    if (this.form.phone) p.phone = this.form.phone;
    if (this.form.employer) p.employer = this.form.employer;
    if (this.form.monthly_income) p.monthly_income = this.form.monthly_income;
    this.api.post('/credit/borrowers', p).subscribe({
      next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Prestatario creado' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
  riskLabel(r: string): string { return { low: 'Bajo', medium: 'Medio', high: 'Alto', very_high: 'Muy Alto' }[r] || r; }
  riskClass(r: string): string {
    return { low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400', very_high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' }[r] || '';
  }
}
