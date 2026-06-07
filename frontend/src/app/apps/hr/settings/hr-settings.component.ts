import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import { HrSettings, LiquidationTemplate } from '../../../core/models/hr.model';

const TEMPLATES: { value: LiquidationTemplate; title: string; subtitle: string }[] = [
  { value: 'formal', title: 'Formal', subtitle: 'Conservadora · 2 páginas · sello superior' },
  { value: 'moderna', title: 'Moderna', subtitle: 'Banner color marca · 1 página · 3 totales' },
  { value: 'compacta', title: 'Compacta', subtitle: 'Una sola página · tabla unificada' },
];

@Component({
  selector: 'app-hr-settings',
  imports: [CommonModule, FormsModule],
  template: `
    <div class="space-y-6">
      <header>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Configuración de RRHH</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Plantilla por defecto para liquidaciones, datos del administrador y branding del PDF.
        </p>
      </header>

      @if (loading()) {
        <p class="text-sm text-slate-500 dark:text-slate-400">Cargando…</p>
      } @else {
      <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
        <h2 class="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4">Plantilla PDF de liquidación</h2>
        <p class="text-xs text-slate-500 dark:text-slate-400 mb-3">
          Selecciona la plantilla por defecto. Usa <strong>Vista previa</strong> para descargar un PDF
          de muestra con datos ficticios y comparar antes de guardar.
        </p>
        <div class="grid gap-3 md:grid-cols-3">
          @for (t of templates; track t.value) {
            <div class="rounded-lg border-2 p-4 transition"
              [class.border-brand-600]="settings.default_liquidation_template === t.value"
              [class.bg-brand-50]="settings.default_liquidation_template === t.value"
              [class.dark:bg-brand-900/20]="settings.default_liquidation_template === t.value"
              [class.border-slate-200]="settings.default_liquidation_template !== t.value"
              [class.dark:border-slate-700]="settings.default_liquidation_template !== t.value">
              <button type="button" (click)="settings.default_liquidation_template = t.value"
                class="text-left w-full">
                <div class="font-semibold text-slate-900 dark:text-slate-100">{{ t.title }}</div>
                <div class="text-xs text-slate-500 dark:text-slate-400 mt-1">{{ t.subtitle }}</div>
                @if (settings.default_liquidation_template === t.value) {
                  <div class="text-xs text-brand-600 mt-2 font-medium">✓ Plantilla por defecto</div>
                }
              </button>
              <button type="button" (click)="previewPdf(t.value)" [disabled]="previewing() === t.value"
                class="mt-3 w-full text-xs px-3 py-1.5 rounded-md border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50">
                {{ previewing() === t.value ? 'Generando…' : '↓ Vista previa PDF' }}
              </button>
            </div>
          }
        </div>
      </section>

      <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-6 grid gap-4 md:grid-cols-2">
        <div class="md:col-span-2">
          <h2 class="text-base font-semibold text-slate-900 dark:text-slate-100">Administrador / Representante legal</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Aparecen en el bloque de firmas del PDF.</p>
        </div>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Nombre</span>
          <input [(ngModel)]="settings.admin_name" type="text"
            placeholder="Ej: Roberto Salazar Vega"
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Cargo</span>
          <input [(ngModel)]="settings.admin_title" type="text"
            placeholder="Ej: Director General"
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="block md:col-span-2">
          <span class="text-xs text-slate-600 dark:text-slate-400">URL de la firma (PNG / JPG)</span>
          <input [(ngModel)]="settings.signature_url" type="url"
            placeholder="https://..."
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
          @if (settings.signature_url) {
            <img [src]="settings.signature_url" alt="Firma"
              class="mt-2 max-h-16 border border-slate-200 dark:border-slate-700 rounded bg-white p-1" />
          }
        </label>
      </section>

      <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-6 grid gap-4 md:grid-cols-2">
        <div class="md:col-span-2">
          <h2 class="text-base font-semibold text-slate-900 dark:text-slate-100">Branding del PDF</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Logo y color de marca para todas las plantillas.</p>
        </div>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">URL del logo</span>
          <input [(ngModel)]="settings.logo_url" type="url"
            placeholder="https://..."
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
          @if (settings.logo_url) {
            <img [src]="settings.logo_url" alt="Logo"
              class="mt-2 max-h-12 border border-slate-200 dark:border-slate-700 rounded bg-white p-1" />
          }
        </label>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Color de marca</span>
          <div class="flex items-center gap-2 mt-1">
            <input [(ngModel)]="settings.brand_color" type="color"
              class="h-9 w-12 rounded border border-slate-300 dark:border-slate-600 bg-transparent" />
            <input [(ngModel)]="settings.brand_color" type="text"
              placeholder="#8b5cf6"
              class="flex-1 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
          </div>
        </label>
      </section>

      <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
        <h2 class="text-base font-semibold text-slate-900 dark:text-slate-100 mb-2">Nota por defecto en liquidaciones</h2>
        <p class="text-xs text-slate-500 dark:text-slate-400 mb-3">
          Esta nota se precarga al crear una liquidación nueva. RRHH puede editarla por cada liquidación.
        </p>
        <textarea [(ngModel)]="settings.liquidation_notes_default" rows="3"
          placeholder="Ej: Gracias por su servicio a Funeraria San Rafael."
          class="w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
      </section>

      @if (savedMsg()) { <div class="rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-2 text-sm">{{ savedMsg() }}</div> }
      @if (errorMsg()) { <div class="rounded-md bg-rose-50 border border-rose-200 text-rose-800 px-4 py-2 text-sm">{{ errorMsg() }}</div> }

      <div class="flex justify-end">
        <button (click)="save()" type="button" [disabled]="saving()"
          class="rounded-md bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-5 py-2.5 text-sm font-medium">
          {{ saving() ? 'Guardando…' : 'Guardar configuración' }}
        </button>
      </div>
      }
    </div>
  `,
})
export class HrSettingsComponent implements OnInit {
  private readonly api = inject(HrApiService);
  readonly templates = TEMPLATES;

  loading = signal(true);
  saving = signal(false);
  previewing = signal<LiquidationTemplate | ''>('');
  savedMsg = signal('');
  errorMsg = signal('');

  settings: HrSettings = {
    id: '', organization_id: '',
    default_liquidation_template: 'formal',
    liquidation_notes_default: null,
    admin_name: null, admin_title: null,
    signature_url: null, logo_url: null, brand_color: '#8b5cf6',
    created_at: '', updated_at: '',
  };

  ngOnInit(): void {
    this.api.getSettings().subscribe({
      next: (s) => { this.settings = { ...s, brand_color: s.brand_color || '#8b5cf6' }; this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  previewPdf(t: LiquidationTemplate): void {
    this.previewing.set(t);
    this.api.downloadSettingsPreviewPdf(t).subscribe({
      next: ({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
        // Free after a small delay so the new tab can load the blob
        setTimeout(() => URL.revokeObjectURL(url), 5000);
        this.previewing.set('');
      },
      error: (err) => {
        this.previewing.set('');
        this.errorMsg.set(err?.error?.detail || 'No se pudo generar la vista previa.');
      },
    });
  }

  save(): void {
    this.saving.set(true);
    this.savedMsg.set('');
    this.errorMsg.set('');
    this.api.updateSettings({
      default_liquidation_template: this.settings.default_liquidation_template,
      liquidation_notes_default: this.settings.liquidation_notes_default,
      admin_name: this.settings.admin_name,
      admin_title: this.settings.admin_title,
      signature_url: this.settings.signature_url,
      logo_url: this.settings.logo_url,
      brand_color: this.settings.brand_color,
    }).subscribe({
      next: (s) => {
        this.settings = { ...s, brand_color: s.brand_color || '#8b5cf6' };
        this.saving.set(false);
        this.savedMsg.set('Configuración guardada.');
      },
      error: (err) => {
        this.saving.set(false);
        this.errorMsg.set(err?.error?.detail || 'No se pudo guardar.');
      },
    });
  }
}
