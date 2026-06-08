import { Component, inject, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

interface PlateScan {
  plate: string | null;
  vehicle_type: string | null;
  color: string | null;
  brand: string | null;
  looks_dirty: boolean;
  plate_confidence: number | null;
  known_vehicle: { brand?: string; model?: string; color?: string } | null;
  open_session: { id: string; entry_time: string } | null;
  suggested_action: string;
  suggestion_text: string;
  wash_suggestion: { text: string; service: { name: string; price: number } | null } | null;
}

@Component({
  selector: 'app-plate-scan',
  imports: [CommonModule, RouterLink, DatePipe],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-6 max-w-2xl">
      <header>
        <p class="text-xs uppercase tracking-wider text-violet-600 dark:text-violet-400 font-medium">SavvyVision ✨</p>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white mt-1">Escanear placa</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Toma una foto del vehículo. La IA lee la placa, te dice si debe entrar o salir, y si está sucio sugiere lavado.
        </p>
      </header>

      @if (!result()) {
        <div (click)="fileInput.click()"
          (dragover)="$event.preventDefault(); dragging.set(true)" (dragleave)="dragging.set(false)" (drop)="onDrop($event)"
          class="rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition"
          [class.border-violet-400]="dragging()" [class.bg-violet-50]="dragging()" [class.dark:bg-violet-500/10]="dragging()"
          [class.border-slate-300]="!dragging()" [class.dark:border-slate-700]="!dragging()">
          <div class="text-4xl mb-3">📸</div>
          <p class="text-sm font-medium text-slate-700 dark:text-slate-200">Toma o arrastra la foto del vehículo</p>
          <p class="text-xs text-slate-400 mt-1">La cámara funciona en celular</p>
          <input #fileInput type="file" accept="image/*" capture="environment" class="hidden" (change)="onPick($event)" />
        </div>

        @if (loading()) {
          <div class="flex items-center gap-3 text-sm text-violet-600 dark:text-violet-400">
            <div class="animate-spin rounded-full h-5 w-5 border-2 border-violet-200 border-t-violet-600"></div>
            Leyendo la placa…
          </div>
        }
        @if (error()) {
          <div class="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-500/5 p-4 text-sm text-amber-800 dark:text-amber-300">
            {{ error() }}
          </div>
        }
      } @else {
        @let r = result()!;
        <div class="rounded-2xl border border-violet-200 dark:border-violet-900/60 bg-white dark:bg-slate-900 overflow-hidden">
          <div class="px-5 py-6 text-center bg-gradient-to-br from-violet-50 to-white dark:from-violet-950/30 dark:to-slate-900">
            @if (r.plate) {
              <div class="inline-block px-6 py-3 rounded-xl bg-slate-900 text-white font-mono text-3xl font-bold tracking-widest border-4 border-slate-700">
                {{ r.plate }}
              </div>
              @if (r.plate_confidence !== null) {
                <p class="text-xs text-slate-400 mt-2">Confianza: {{ r.plate_confidence }}%</p>
              }
              <p class="text-sm text-slate-600 dark:text-slate-300 mt-2">
                {{ r.brand || '' }} {{ r.color || '' }} {{ r.vehicle_type ? '· ' + typeLabel(r.vehicle_type) : '' }}
              </p>
            } @else {
              <p class="text-sm text-amber-700 dark:text-amber-300">No se pudo leer la placa. Ingrésala manualmente.</p>
            }
          </div>

          @if (r.plate) {
            <div class="p-5 space-y-3">
              <div class="rounded-xl p-4 border"
                [class]="r.suggested_action === 'exit' ? 'border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-500/5' : 'border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-500/5'">
                <p class="text-sm font-medium text-slate-900 dark:text-white">{{ r.suggestion_text }}</p>
                @if (r.known_vehicle) {
                  <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">✓ Vehículo registrado: {{ r.known_vehicle.brand }} {{ r.known_vehicle.model }}</p>
                }
                @if (r.open_session) {
                  <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Entró: {{ r.open_session.entry_time | date:'short' }}</p>
                }
                <a [routerLink]="['/parking/sessions']" class="inline-block mt-2 text-xs rounded-md px-3 py-1.5 font-medium"
                  [class]="r.suggested_action === 'exit' ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white'">
                  {{ r.suggested_action === 'exit' ? '→ Registrar salida' : '→ Registrar entrada' }}
                </a>
              </div>

              @if (r.wash_suggestion) {
                <div class="rounded-xl p-4 border border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-500/5">
                  <p class="text-sm font-medium text-amber-800 dark:text-amber-300">🧽 {{ r.wash_suggestion.text }}</p>
                  @if (r.wash_suggestion.service) {
                    <a [routerLink]="['/parking/services']" class="inline-block mt-2 text-xs rounded-md bg-amber-600 text-white px-3 py-1.5 font-medium">→ Agregar lavado</a>
                  }
                </div>
              }
            </div>
          }
        </div>
        <button (click)="reset()" class="rounded-md bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 text-sm font-medium">Escanear otro</button>
      }
    </div>
  `,
})
export class PlateScanComponent {
  private readonly api = inject(ApiService);
  dragging = signal(false);
  loading = signal(false);
  error = signal('');
  result = signal<PlateScan | null>(null);

  onDrop(ev: DragEvent): void { ev.preventDefault(); this.dragging.set(false); const f = ev.dataTransfer?.files?.[0]; if (f) this.scan(f); }
  onPick(ev: Event): void { const f = (ev.target as HTMLInputElement).files?.[0]; if (f) this.scan(f); }

  scan(file: File): void {
    this.loading.set(true); this.error.set('');
    this.api.postFile<PlateScan>('/parking/scan-plate', file).subscribe({
      next: (r) => { this.result.set(r); this.loading.set(false); },
      error: (err) => { this.loading.set(false); this.error.set(err?.error?.detail || 'No se pudo procesar la imagen. La IA puede no estar configurada.'); },
    });
  }
  reset(): void { this.result.set(null); this.error.set(''); }
  typeLabel(t: string): string { return ({ car: 'Auto', motorcycle: 'Moto', truck: 'Camión', van: 'Camioneta' } as Record<string, string>)[t] || t; }
}
