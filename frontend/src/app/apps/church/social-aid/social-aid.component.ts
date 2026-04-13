import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface AidProgram {
  id: string;
  name: string;
  program_type: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  budget_amount: number | null;
  status: string;
  created_at: string;
}

interface Beneficiary {
  id: string;
  program_id: string;
  person_id: string | null;
  external_name: string | null;
  external_document: string | null;
  external_phone: string | null;
  need_category: string | null;
  household_size: number | null;
  notes: string | null;
  status: string;
}

interface Distribution {
  id: string;
  program_id: string;
  beneficiary_id: string;
  distribution_date: string;
  item_description: string;
  quantity: number | null;
  unit: string | null;
  estimated_value: number | null;
}

@Component({
  selector: 'app-church-social-aid',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Ayuda Social</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Programas, beneficiarios y entregas</p>
        </div>
        <button (click)="showProgramModal = true"
          class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition">
          + Nuevo programa
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (programs().length > 0) {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          @for (p of programs(); track p.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-theme-md transition">
              <div class="flex items-start justify-between mb-2">
                <h3 class="text-base font-semibold text-gray-800 dark:text-white/90">{{ p.name }}</h3>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-400">
                  {{ p.program_type }}
                </span>
              </div>
              @if (p.description) { <p class="text-xs text-gray-500 mb-2">{{ p.description }}</p> }
              @if (p.budget_amount) { <p class="text-xs text-gray-600 dark:text-gray-400">Presupuesto: $ {{ p.budget_amount | number:'1.0-0' }}</p> }
              <div class="mt-4 flex gap-2">
                <button (click)="openBeneficiariesPanel(p)" class="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition">
                  Beneficiarios
                </button>
                <button (click)="openDistributionsPanel(p)" class="text-xs px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
                  Entregas
                </button>
              </div>
            </div>
          }
        </div>
      } @else {
        <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p class="text-gray-500 dark:text-gray-400">No hay programas de ayuda social.</p>
        </div>
      }

      <!-- Program modal -->
      @if (showProgramModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nuevo programa</h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                <input type="text" [(ngModel)]="programForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Tipo *</label>
                <select [(ngModel)]="programForm.program_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm">
                  <option value="food">Alimentación</option>
                  <option value="clothing">Ropa</option>
                  <option value="medical">Salud</option>
                  <option value="educational">Educación</option>
                  <option value="housing">Vivienda</option>
                  <option value="emergency">Emergencia</option>
                  <option value="other">Otro</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="programForm.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm resize-none"></textarea>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Presupuesto</label>
                <input type="number" [(ngModel)]="programForm.budget_amount" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm" />
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showProgramModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="createProgram()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Crear</button>
            </div>
          </div>
        </div>
      }

      <!-- Beneficiaries panel -->
      @if (showBeneficiariesPanel && selectedProgram) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl max-h-[85vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Beneficiarios — {{ selectedProgram.name }}</h3>
              <button (click)="closePanels()" class="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div class="p-6 overflow-y-auto flex-1 space-y-3">
              <div class="rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-4">
                <p class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">Agregar beneficiario externo</p>
                <div class="space-y-2">
                  <input type="text" [(ngModel)]="beneficiaryForm.external_name" placeholder="Nombre completo"
                    class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                  <div class="grid grid-cols-2 gap-2">
                    <input type="text" [(ngModel)]="beneficiaryForm.external_document" placeholder="Documento"
                      class="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                    <input type="text" [(ngModel)]="beneficiaryForm.external_phone" placeholder="Teléfono"
                      class="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                  </div>
                  <button (click)="addBeneficiary()" class="w-full px-3 py-1.5 bg-brand-500 hover:bg-brand-600 text-white text-sm rounded-lg">Agregar</button>
                </div>
              </div>
              @if (beneficiaries().length > 0) {
                @for (b of beneficiaries(); track b.id) {
                  <div class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <p class="text-sm font-medium text-gray-800 dark:text-white/90">{{ b.external_name || '[Miembro]' }}</p>
                    @if (b.external_document) { <p class="text-xs text-gray-500">Doc: {{ b.external_document }}</p> }
                  </div>
                }
              } @else {
                <p class="text-center text-sm text-gray-400 py-4">Sin beneficiarios.</p>
              }
            </div>
          </div>
        </div>
      }

      <!-- Distributions panel -->
      @if (showDistributionsPanel && selectedProgram) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl max-h-[85vh] flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Entregas — {{ selectedProgram.name }}</h3>
              <button (click)="closePanels()" class="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div class="p-6 overflow-y-auto flex-1 space-y-3">
              <div class="rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-4 space-y-2">
                <p class="text-xs font-medium text-gray-600 dark:text-gray-400">Registrar entrega</p>
                <select [(ngModel)]="distForm.beneficiary_id" class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm">
                  <option value="">Beneficiario...</option>
                  @for (b of beneficiaries(); track b.id) {
                    <option [value]="b.id">{{ b.external_name || b.person_id }}</option>
                  }
                </select>
                <input type="date" [(ngModel)]="distForm.distribution_date" class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                <input type="text" [(ngModel)]="distForm.item_description" placeholder="Descripción (ej: bolsa de mercado)"
                  class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                <div class="grid grid-cols-3 gap-2">
                  <input type="number" [(ngModel)]="distForm.quantity" placeholder="Cantidad" class="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                  <input type="text" [(ngModel)]="distForm.unit" placeholder="Unidad" class="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                  <input type="number" [(ngModel)]="distForm.estimated_value" placeholder="Valor est." class="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm" />
                </div>
                <button (click)="addDistribution()" class="w-full px-3 py-1.5 bg-brand-500 hover:bg-brand-600 text-white text-sm rounded-lg">Registrar</button>
              </div>
              @for (d of distributions(); track d.id) {
                <div class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div class="flex justify-between">
                    <p class="text-sm font-medium text-gray-800 dark:text-white/90">{{ d.item_description }}</p>
                    <span class="text-xs text-gray-500">{{ d.distribution_date }}</span>
                  </div>
                  @if (d.quantity) { <p class="text-xs text-gray-500">{{ d.quantity }} {{ d.unit || '' }}</p> }
                </div>
              }
              @if (distributions().length === 0) {
                <p class="text-center text-sm text-gray-400 py-4">Sin entregas registradas.</p>
              }
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ChurchSocialAidComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  programs = signal<AidProgram[]>([]);
  beneficiaries = signal<Beneficiary[]>([]);
  distributions = signal<Distribution[]>([]);

  showProgramModal = false;
  programForm: any = { name: '', program_type: 'food', description: '', budget_amount: null };

  selectedProgram: AidProgram | null = null;
  showBeneficiariesPanel = false;
  showDistributionsPanel = false;

  beneficiaryForm: any = { external_name: '', external_document: '', external_phone: '' };
  distForm: any = {
    beneficiary_id: '', distribution_date: new Date().toISOString().split('T')[0],
    item_description: '', quantity: null, unit: '', estimated_value: null,
  };

  ngOnInit(): void {
    this.loadPrograms();
  }

  loadPrograms(): void {
    this.loading.set(true);
    this.api.get<AidProgram[]>('/church/social-aid/programs').subscribe({
      next: (p) => { this.programs.set(p); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  createProgram(): void {
    if (!this.programForm.name) return;
    const payload: any = { ...this.programForm };
    Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === null) delete payload[k]; });
    this.api.post<AidProgram>('/church/social-aid/programs', payload).subscribe({
      next: () => {
        this.showProgramModal = false;
        this.programForm = { name: '', program_type: 'food', description: '', budget_amount: null };
        this.loadPrograms();
        this.notify.show({ type: 'success', title: 'Creado', message: 'Programa creado' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }

  openBeneficiariesPanel(p: AidProgram): void {
    this.selectedProgram = p;
    this.showBeneficiariesPanel = true;
    this.loadBeneficiaries(p.id);
  }

  openDistributionsPanel(p: AidProgram): void {
    this.selectedProgram = p;
    this.showDistributionsPanel = true;
    this.loadBeneficiaries(p.id);
    this.loadDistributions(p.id);
  }

  closePanels(): void {
    this.showBeneficiariesPanel = false;
    this.showDistributionsPanel = false;
    this.selectedProgram = null;
  }

  private loadBeneficiaries(programId: string): void {
    this.api.get<Beneficiary[]>(`/church/social-aid/programs/${programId}/beneficiaries`).subscribe({
      next: (b) => this.beneficiaries.set(b),
    });
  }

  private loadDistributions(programId: string): void {
    this.api.get<Distribution[]>(`/church/social-aid/programs/${programId}/distributions`).subscribe({
      next: (d) => this.distributions.set(d),
    });
  }

  addBeneficiary(): void {
    if (!this.selectedProgram || !this.beneficiaryForm.external_name) return;
    this.api.post<Beneficiary>('/church/social-aid/beneficiaries', {
      program_id: this.selectedProgram.id,
      ...this.beneficiaryForm,
    }).subscribe({
      next: () => {
        this.beneficiaryForm = { external_name: '', external_document: '', external_phone: '' };
        this.loadBeneficiaries(this.selectedProgram!.id);
        this.notify.show({ type: 'success', title: 'Agregado', message: 'Beneficiario agregado' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo agregar' }),
    });
  }

  addDistribution(): void {
    if (!this.selectedProgram || !this.distForm.beneficiary_id || !this.distForm.item_description) return;
    const payload: any = {
      program_id: this.selectedProgram.id,
      ...this.distForm,
    };
    Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === null) delete payload[k]; });
    this.api.post<Distribution>('/church/social-aid/distributions', payload).subscribe({
      next: () => {
        this.distForm = {
          beneficiary_id: '', distribution_date: new Date().toISOString().split('T')[0],
          item_description: '', quantity: null, unit: '', estimated_value: null,
        };
        this.loadDistributions(this.selectedProgram!.id);
        this.notify.show({ type: 'success', title: 'Registrada', message: 'Entrega registrada' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo registrar' }),
    });
  }
}
