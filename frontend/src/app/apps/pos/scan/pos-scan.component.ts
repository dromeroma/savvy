import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AiService, ConfirmableAction } from '../../../core/services/ai.service';
import { ConfirmableActionComponent } from '../../../shared/components/ai/confirmable-action.component';

@Component({
  selector: 'app-pos-scan',
  imports: [CommonModule, RouterLink, ConfirmableActionComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-6 max-w-3xl">
      <header>
        <p class="text-xs uppercase tracking-wider text-violet-600 dark:text-violet-400 font-medium">SavvyScan ✨</p>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white mt-1">Escanear factura de compra</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Sube una foto o PDF de la factura del proveedor. La IA extrae los productos,
          tú revisas y al confirmar <strong>se actualiza el inventario automáticamente</strong>.
        </p>
      </header>

      @if (!action()) {
        <!-- Dropzone -->
        <div
          (dragover)="$event.preventDefault(); dragging.set(true)"
          (dragleave)="dragging.set(false)"
          (drop)="onDrop($event)"
          class="rounded-2xl border-2 border-dashed p-10 text-center transition cursor-pointer"
          [class.border-violet-400]="dragging()"
          [class.bg-violet-50]="dragging()"
          [class.dark:bg-violet-500/10]="dragging()"
          [class.border-slate-300]="!dragging()"
          [class.dark:border-slate-700]="!dragging()"
          (click)="fileInput.click()">
          <div class="text-4xl mb-3">📄</div>
          <p class="text-sm font-medium text-slate-700 dark:text-slate-200">
            Arrastra la factura aquí o haz clic para elegir
          </p>
          <p class="text-xs text-slate-400 mt-1">JPG, PNG o PDF · una factura por archivo</p>
          <input #fileInput type="file" accept="image/*,application/pdf" class="hidden"
            (change)="onPick($event)" />
        </div>

        @if (loading()) {
          <div class="flex items-center gap-3 text-sm text-violet-600 dark:text-violet-400">
            <div class="animate-spin rounded-full h-5 w-5 border-2 border-violet-200 border-t-violet-600"></div>
            Leyendo la factura con IA…
          </div>
        }

        @if (error()) {
          <div class="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-500/5 p-4">
            <p class="text-sm font-medium text-amber-800 dark:text-amber-300">{{ error() }}</p>
            @if (notConfigured()) {
              <p class="text-xs text-amber-700/80 dark:text-amber-400/80 mt-1">
                La IA aún no está activada. El super administrador debe configurar la API key en
                <span class="font-mono">Plataforma → Inteligencia IA</span>.
              </p>
            }
          </div>
        }
      } @else {
        <!-- Resultado: tarjeta confirmable -->
        <app-confirmable-action
          [action]="action()!"
          (confirmed)="onConfirmed($event)"
          (discarded)="reset()" />

        @if (action()!.status !== 'pending_review') {
          <div class="flex gap-2">
            <button (click)="reset()" type="button"
              class="rounded-md bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 text-sm font-medium">
              Escanear otra factura
            </button>
            <a routerLink="/pos/inventory"
              class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">
              Ver inventario →
            </a>
          </div>
        }
      }

      <!-- Cómo funciona -->
      <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40 p-5">
        <h2 class="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-medium mb-3">Cómo funciona</h2>
        <ol class="space-y-2 text-sm text-slate-600 dark:text-slate-300">
          <li class="flex gap-2"><span class="text-violet-500 font-semibold">1.</span> Subes la factura del proveedor (foto o PDF).</li>
          <li class="flex gap-2"><span class="text-violet-500 font-semibold">2.</span> La IA extrae proveedor, productos, cantidades y costos.</li>
          <li class="flex gap-2"><span class="text-violet-500 font-semibold">3.</span> Revisas y editas lo que necesites (campos de baja confianza se resaltan).</li>
          <li class="flex gap-2"><span class="text-violet-500 font-semibold">4.</span> Al confirmar: se crean/actualizan productos y se suma el stock con un movimiento de compra.</li>
        </ol>
      </div>
    </div>
  `,
})
export class PosScanComponent {
  private readonly ai = inject(AiService);

  dragging = signal(false);
  loading = signal(false);
  error = signal('');
  notConfigured = signal(false);
  action = signal<ConfirmableAction | null>(null);

  onDrop(ev: DragEvent): void {
    ev.preventDefault();
    this.dragging.set(false);
    const file = ev.dataTransfer?.files?.[0];
    if (file) this.scan(file);
  }

  onPick(ev: Event): void {
    const file = (ev.target as HTMLInputElement).files?.[0];
    if (file) this.scan(file);
  }

  scan(file: File): void {
    this.loading.set(true);
    this.error.set('');
    this.notConfigured.set(false);
    this.ai.scan(file, {
      prompt_key: 'extraction.purchase_invoice',
      target_app: 'pos',
      document_type: 'purchase_invoice',
    }).subscribe({
      next: (a) => { this.action.set(a); this.loading.set(false); },
      error: (err) => {
        this.loading.set(false);
        const detail = err?.error?.detail || 'No se pudo procesar la factura.';
        this.error.set(detail);
        this.notConfigured.set(/no est[áa] configurad|API key|activad/i.test(detail));
      },
    });
  }

  onConfirmed(a: ConfirmableAction): void {
    this.action.set(a);
  }

  reset(): void {
    this.action.set(null);
    this.error.set('');
  }
}
