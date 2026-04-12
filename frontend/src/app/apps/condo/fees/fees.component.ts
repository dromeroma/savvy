import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-condo-fees',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Cuotas de Administracion</h2></div>
        <button (click)="showGenModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Generar Cuotas</button>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Unidad</th><th class="px-4 py-3 font-medium text-gray-500">Periodo</th><th class="px-4 py-3 font-medium text-gray-500">Total</th><th class="px-4 py-3 font-medium text-gray-500">Pagado</th><th class="px-4 py-3 font-medium text-gray-500">Vence</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th><th class="px-4 py-3"></th></tr></thead>
        <tbody>@for (f of fees(); track f.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50">
            <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ f.unit_id | slice:0:8 }}</td>
            <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ f.period }}</td>
            <td class="px-4 py-3 font-mono text-gray-800 dark:text-white/90">$ {{ f.total | number:'1.0-0' }}</td>
            <td class="px-4 py-3 font-mono text-green-600 dark:text-green-400">$ {{ f.paid_amount | number:'1.0-0' }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ f.due_date }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="f.status === 'paid' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : f.status === 'overdue' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'">{{ statusLabel(f.status) }}</span></td>
            <td class="px-4 py-3">@if (f.status !== 'paid') { <button (click)="payFee(f)" class="px-3 py-1 text-xs rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Pagar</button> }</td>
          </tr>
        }</tbody></table></div>
        @if (fees().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay cuotas</p> }
      </div>
      @if (showGenModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showGenModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Generar Cuotas</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Propiedad</label><select [(ngModel)]="genForm.property_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (p of properties(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }</select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Periodo (YYYY-MM)</label><input [(ngModel)]="genForm.period" placeholder="2026-04" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fecha vencimiento</label><input type="date" [(ngModel)]="genForm.due_date" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showGenModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="generate()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Generar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CondoFeesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  fees = signal<any[]>([]); properties = signal<any[]>([]); showGenModal = false;
  genForm: any = { property_id: '', period: '', due_date: '' };
  ngOnInit(): void { this.load(); this.api.get<any[]>('/condo/properties').subscribe({ next: (r) => this.properties.set(r) }); }
  load(): void { this.api.get<any[]>('/condo/fees').subscribe({ next: (r) => this.fees.set(r) }); }
  generate(): void { this.api.post('/condo/fees/generate', this.genForm).subscribe({ next: (r: any) => { this.showGenModal = false; this.notify.show({ type: 'success', title: 'Listo', message: `${r.length} cuotas generadas` }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo generar' }) }); }
  payFee(f: any): void { this.api.post(`/condo/fees/${f.id}/pay`, { amount: f.total - f.paid_amount }).subscribe({ next: () => { this.notify.show({ type: 'success', title: 'Pagado', message: 'Cuota pagada' }); this.load(); } }); }
  statusLabel(s: string): string { return { pending: 'Pendiente', paid: 'Pagada', partial: 'Parcial', overdue: 'Vencida' }[s] || s; }
}
