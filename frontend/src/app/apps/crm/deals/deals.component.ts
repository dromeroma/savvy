import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-deals',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Deals / Oportunidades</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Negocios en tu pipeline</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Deal</button>
      </div>

      <!-- Pipeline selector -->
      <div class="mb-4">
        <select [(ngModel)]="selectedPipeline" (ngModelChange)="loadDeals()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos los pipelines</option>
          @for (p of pipelines(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }
        </select>
      </div>

      <!-- Deals grouped by stage (Kanban-like) -->
      @if (selectedPipeline && selectedPipelineData()) {
        <div class="flex gap-4 overflow-x-auto custom-scrollbar pb-4">
          @for (stage of selectedPipelineData()!.stages; track stage.id) {
            <div class="min-w-[280px] max-w-[320px] flex-shrink-0">
              <div class="flex items-center gap-2 mb-3">
                <div class="w-3 h-3 rounded-full" [style.background-color]="stage.color || '#9ca3af'"></div>
                <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ stage.name }}</h3>
                <span class="text-xs text-gray-400">({{ dealsForStage(stage.id).length }})</span>
              </div>
              <div class="space-y-2">
                @for (deal of dealsForStage(stage.id); track deal.id) {
                  <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3">
                    <h4 class="text-sm font-medium text-gray-800 dark:text-white/90">{{ deal.title }}</h4>
                    <p class="text-xs font-mono text-green-600 dark:text-green-400 mt-1">$ {{ deal.value | number:'1.0-0' }}</p>
                    @if (deal.expected_close_date) { <p class="text-xs text-gray-400 mt-1">Cierre: {{ deal.expected_close_date }}</p> }
                  </div>
                }
              </div>
            </div>
          }
        </div>
      } @else {
        <!-- List view -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Título</th>
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Valor</th>
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Prob.</th>
                <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
              </tr></thead>
              <tbody>
                @for (d of deals(); track d.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                    <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ d.title }}</td>
                    <td class="px-4 py-3 font-mono text-green-600 dark:text-green-400">$ {{ d.value | number:'1.0-0' }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ d.probability }}%</td>
                    <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full" [class]="d.status === 'won' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : d.status === 'lost' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'">{{ d.status }}</span></td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (deals().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay deals</p> }
        </div>
      }

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Deal</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título</label><input [(ngModel)]="dealForm.title" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pipeline</label><select [(ngModel)]="dealForm.pipeline_id" (ngModelChange)="onPipelineChange()" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">--</option>@for (p of pipelines(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }</select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Etapa</label><select [(ngModel)]="dealForm.stage_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">--</option>@for (s of modalStages(); track s.id) { <option [value]="s.id">{{ s.name }}</option> }</select></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor</label><input type="number" [(ngModel)]="dealForm.value" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Contacto</label><select [(ngModel)]="dealForm.contact_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="">-- Sin contacto --</option>@for (c of contacts(); track c.id) { <option [value]="c.id">{{ c.first_name }} {{ c.last_name }}</option> }</select></div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="saveDeal()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class DealsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  deals = signal<any[]>([]);
  pipelines = signal<any[]>([]);
  contacts = signal<any[]>([]);
  modalStages = signal<any[]>([]);
  showModal = false;
  selectedPipeline = '';
  dealForm: any = { title: '', pipeline_id: '', stage_id: '', value: 0, contact_id: '' };

  ngOnInit(): void {
    this.api.get<any[]>('/crm/pipelines').subscribe({ next: (r) => this.pipelines.set(r) });
    this.api.get<any>('/crm/contacts', { page_size: 500 }).subscribe({ next: (r) => this.contacts.set(r.items || []) });
    this.loadDeals();
  }
  loadDeals(): void {
    const p: any = {};
    if (this.selectedPipeline) p.pipeline_id = this.selectedPipeline;
    this.api.get<any[]>('/crm/deals', p).subscribe({ next: (r) => this.deals.set(r) });
  }
  selectedPipelineData(): any { return this.pipelines().find(p => p.id === this.selectedPipeline); }
  dealsForStage(stageId: string): any[] { return this.deals().filter(d => d.stage_id === stageId); }
  onPipelineChange(): void {
    const p = this.pipelines().find(pl => pl.id === this.dealForm.pipeline_id);
    this.modalStages.set(p?.stages || []);
    this.dealForm.stage_id = '';
  }
  saveDeal(): void {
    const payload: any = { title: this.dealForm.title, pipeline_id: this.dealForm.pipeline_id, stage_id: this.dealForm.stage_id, value: this.dealForm.value };
    if (this.dealForm.contact_id) payload.contact_id = this.dealForm.contact_id;
    this.api.post('/crm/deals', payload).subscribe({
      next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Deal creado' }); this.loadDeals(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
}
