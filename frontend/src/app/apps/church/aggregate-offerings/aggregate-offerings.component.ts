import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface ChurchEvent {
  id: string;
  name: string;
  date: string;
  type: string;
}

interface AggregateOffering {
  id: string;
  event_id: string | null;
  offering_type: string;
  total_amount: number;
  contributor_count: number | null;
  payment_method: string;
  collected_date: string;
  notes: string | null;
  finance_transaction_id: string | null;
  created_at: string;
}

@Component({
  selector: 'app-church-aggregate-offerings',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Ofrendas Agregadas</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Entrada masiva de diezmos/ofrendas restantes por culto</p>
        </div>
        <button (click)="showForm = true"
          class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">
          + Registrar ofrenda
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (offerings().length > 0) {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500">Fecha</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Culto</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Tipo</th>
                  <th class="px-4 py-3 font-medium text-gray-500 text-right">Contribuyentes</th>
                  <th class="px-4 py-3 font-medium text-gray-500 text-right">Total</th>
                  <th class="px-4 py-3 font-medium text-gray-500">Método</th>
                </tr>
              </thead>
              <tbody>
                @for (o of offerings(); track o.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50">
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ o.collected_date }}</td>
                    <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ getEventName(o.event_id) }}</td>
                    <td class="px-4 py-3 capitalize text-gray-600 dark:text-gray-400">{{ o.offering_type }}</td>
                    <td class="px-4 py-3 text-right font-mono text-gray-600 dark:text-gray-400">{{ o.contributor_count || '-' }}</td>
                    <td class="px-4 py-3 text-right font-mono font-bold text-success-600 dark:text-success-400">$ {{ o.total_amount | number:'1.0-0' }}</td>
                    <td class="px-4 py-3 capitalize text-gray-600 dark:text-gray-400">{{ o.payment_method }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      } @else {
        <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p class="text-gray-500 dark:text-gray-400">No hay ofrendas agregadas registradas.</p>
        </div>
      }

      <!-- Form modal -->
      @if (showForm) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Registrar ofrenda agregada</h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Culto / Evento</label>
                <select [(ngModel)]="form.event_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm">
                  <option value="">Sin evento específico</option>
                  @for (e of events(); track e.id) {
                    <option [value]="e.id">{{ e.date }} — {{ e.name }}</option>
                  }
                </select>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Tipo</label>
                  <select [(ngModel)]="form.offering_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm">
                    <option value="tithe">Diezmo</option>
                    <option value="offering">Ofrenda</option>
                    <option value="special">Especial</option>
                    <option value="mission">Misiones</option>
                    <option value="building">Construcción</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Categoría</label>
                  <input type="text" [(ngModel)]="form.category_code" placeholder="TITHE"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm uppercase" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Total *</label>
                  <input type="number" step="0.01" [(ngModel)]="form.total_amount" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1"># Contribuyentes</label>
                  <input type="number" [(ngModel)]="form.contributor_count" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Fecha *</label>
                  <input type="date" [(ngModel)]="form.collected_date" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Método</label>
                  <select [(ngModel)]="form.payment_method" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm">
                    <option value="cash">Efectivo</option>
                    <option value="transfer">Transferencia</option>
                    <option value="card">Tarjeta</option>
                    <option value="check">Cheque</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Notas</label>
                <textarea [(ngModel)]="form.notes" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm resize-none"></textarea>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showForm = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="submit()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ChurchAggregateOfferingsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  offerings = signal<AggregateOffering[]>([]);
  events = signal<ChurchEvent[]>([]);
  eventMap: Record<string, ChurchEvent> = {};

  showForm = false;
  form: any = {
    event_id: '',
    offering_type: 'tithe',
    category_code: 'TITHE',
    total_amount: null,
    contributor_count: null,
    collected_date: new Date().toISOString().split('T')[0],
    payment_method: 'cash',
    notes: '',
  };

  ngOnInit(): void {
    this.loadEvents();
    this.load();
  }

  loadEvents(): void {
    this.api.get<ChurchEvent[]>('/church/events/').subscribe({
      next: (e) => {
        this.events.set(e);
        e.forEach(x => { this.eventMap[x.id] = x; });
      },
    });
  }

  getEventName(eventId: string | null): string {
    if (!eventId) return '—';
    return this.eventMap[eventId]?.name || '—';
  }

  load(): void {
    this.loading.set(true);
    this.api.get<AggregateOffering[]>('/church/finance/aggregate-offerings').subscribe({
      next: (o) => { this.offerings.set(o); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  submit(): void {
    if (!this.form.total_amount || !this.form.collected_date) {
      this.notify.show({ type: 'error', title: 'Falta información', message: 'Total y fecha son obligatorios' });
      return;
    }
    const payload: any = { ...this.form };
    if (!payload.event_id) delete payload.event_id;
    if (!payload.contributor_count) delete payload.contributor_count;
    if (!payload.notes) delete payload.notes;
    this.api.post('/church/finance/aggregate-offerings', payload).subscribe({
      next: () => {
        this.showForm = false;
        this.form.total_amount = null;
        this.form.contributor_count = null;
        this.form.notes = '';
        this.load();
        this.notify.show({ type: 'success', title: 'Registrada', message: 'Ofrenda agregada registrada' });
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo registrar',
      }),
    });
  }
}
