import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-condo-governance',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Asambleas y Votacion</h2></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nueva Asamblea</button>
      </div>
      <div class="space-y-4">
        @for (a of assemblies(); track a.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between mb-2">
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ a.title }}</h4>
                <div class="flex gap-3 text-xs text-gray-500 mt-1">
                  <span>{{ a.assembly_type === 'ordinary' ? 'Ordinaria' : 'Extraordinaria' }}</span>
                  <span>Quorum req: {{ a.quorum_required }}%</span>
                  <span>Presente: {{ a.quorum_present }}%</span>
                </div>
              </div>
              <span class="px-2 py-1 text-xs rounded-full" [class]="a.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : a.status === 'in_progress' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'">{{ statusLabel(a.status) }}</span>
            </div>
            @if (a.proposals && a.proposals.length > 0) {
              <div class="mt-3 space-y-1">
                @for (p of a.proposals; track $index) {
                  <div class="text-xs text-gray-600 dark:text-gray-400 flex items-center gap-2">
                    <span class="font-mono text-gray-400">{{ $index + 1 }}.</span>
                    <span>{{ p.title }}</span>
                  </div>
                }
              </div>
            }
          </div>
        }
        @if (assemblies().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay asambleas</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Asamblea</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Titulo</label><input [(ngModel)]="form.title" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.assembly_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="ordinary">Ordinaria</option><option value="extraordinary">Extraordinaria</option></select></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quorum (%)</label><input type="number" [(ngModel)]="form.quorum_required" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Propiedad</label><select [(ngModel)]="form.property_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (p of properties(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }</select></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Crear</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CondoGovernanceComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  assemblies = signal<any[]>([]); properties = signal<any[]>([]); showModal = false;
  form: any = { title: '', assembly_type: 'ordinary', quorum_required: 51, property_id: '', scheduled_at: new Date().toISOString() };
  ngOnInit(): void { this.load(); this.api.get<any[]>('/condo/properties').subscribe({ next: (r) => this.properties.set(r) }); }
  load(): void { this.api.get<any[]>('/condo/governance/assemblies').subscribe({ next: (r) => this.assemblies.set(r) }); }
  save(): void { this.api.post('/condo/governance/assemblies', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Asamblea creada' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
  statusLabel(s: string): string { return { scheduled: 'Programada', in_progress: 'En curso', completed: 'Completada', cancelled: 'Cancelada' }[s] || s; }
}
