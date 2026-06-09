import { Component, inject, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AiService } from '../../../core/services/ai.service';

/**
 * Scan-to-prefill REUTILIZABLE y TRANSVERSAL a todas las apps.
 *
 * Botón "✨ Escanear documento" → modal con dropzone → la IA extrae los datos →
 * emite un objeto {campo: valor} que el formulario padre usa para prellenarse.
 * No escribe en BD: solo entrega los datos al formulario (Zero-Form).
 *
 * @example  (en Memorial, para prellenar el titular desde una cédula)
 *   <app-scan-prefill prompt-key="extraction.id_card" target-app="memorial"
 *     document-type="id_card" label="Escanear cédula"
 *     (prefill)="applyCedula($event)" />
 */
@Component({
  selector: 'app-scan-prefill',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button type="button" (click)="open.set(true)"
      class="inline-flex items-center gap-1.5 rounded-md border border-violet-300 dark:border-violet-700 text-violet-700 dark:text-violet-300 px-3 py-1.5 text-xs font-medium hover:bg-violet-50 dark:hover:bg-violet-500/10">
      ✨ {{ label() }}
    </button>

    @if (open()) {
      <div class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4"
        (click)="$event.target === $event.currentTarget && close()">
        <div class="w-full max-w-md rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-2xl">
          <div class="px-5 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-900 dark:text-white">✨ {{ label() }}</h3>
            <button type="button" (click)="close()" class="text-slate-400 text-lg leading-none">×</button>
          </div>
          <div class="p-5">
            @if (!loading() && !error()) {
              <div (click)="fileInput.click()"
                (dragover)="$event.preventDefault(); dragging.set(true)" (dragleave)="dragging.set(false)" (drop)="onDrop($event)"
                class="rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition"
                [class.border-violet-400]="dragging()" [class.bg-violet-50]="dragging()" [class.dark:bg-violet-500/10]="dragging()"
                [class.border-slate-300]="!dragging()" [class.dark:border-slate-700]="!dragging()">
                <div class="text-3xl mb-2">📷</div>
                <p class="text-sm text-slate-700 dark:text-slate-200">Toma o arrastra la foto del documento</p>
                <p class="text-xs text-slate-400 mt-1">La IA lee los datos y prellena el formulario</p>
                <input #fileInput type="file" accept="image/*,application/pdf" capture="environment" class="hidden" (change)="onPick($event)" />
              </div>
            }
            @if (loading()) {
              <div class="flex items-center gap-2 text-sm text-violet-600 dark:text-violet-400 py-6 justify-center">
                <div class="animate-spin rounded-full h-5 w-5 border-2 border-violet-200 border-t-violet-600"></div>
                Leyendo el documento…
              </div>
            }
            @if (error()) {
              <div class="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-500/5 p-3 text-sm text-amber-800 dark:text-amber-300">
                {{ error() }}
              </div>
            }
          </div>
        </div>
      </div>
    }
  `,
})
export class ScanPrefillComponent {
  private readonly ai = inject(AiService);

  promptKey = input.required<string>({ alias: 'prompt-key' });
  targetApp = input.required<string>({ alias: 'target-app' });
  documentType = input.required<string>({ alias: 'document-type' });
  label = input<string>('Escanear documento');

  /** Emite los campos extraídos {clave: valor} para prellenar el formulario. */
  prefill = output<Record<string, unknown>>();

  open = signal(false);
  dragging = signal(false);
  loading = signal(false);
  error = signal('');

  close(): void { this.open.set(false); this.error.set(''); }
  onDrop(ev: DragEvent): void { ev.preventDefault(); this.dragging.set(false); const f = ev.dataTransfer?.files?.[0]; if (f) this.scan(f); }
  onPick(ev: Event): void { const f = (ev.target as HTMLInputElement).files?.[0]; if (f) this.scan(f); }

  scan(file: File): void {
    this.loading.set(true);
    this.error.set('');
    this.ai.scan(file, {
      prompt_key: this.promptKey(),
      target_app: this.targetApp(),
      document_type: this.documentType(),
    }).subscribe({
      next: (a) => {
        this.loading.set(false);
        const data: Record<string, unknown> = {};
        for (const f of a.fields) data[f.key] = f.value;
        this.prefill.emit(data);
        this.open.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail || 'No se pudo leer el documento. La IA puede no estar configurada todavía.');
      },
    });
  }
}
