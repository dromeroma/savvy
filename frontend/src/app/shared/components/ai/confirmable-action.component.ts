import { Component, computed, inject, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiService, ConfirmableAction } from '../../../core/services/ai.service';

/**
 * Tarjeta "Savvy entendió esto → [Confirmar] [Editar] [Descartar]".
 * Patrón UX de Human-in-the-loop: la IA propone, el usuario confirma.
 * Reutilizable en cualquier app que use SavvyScan.
 */
@Component({
  selector: 'app-confirmable-action',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    @if (action(); as a) {
      <div class="rounded-2xl border border-violet-200 dark:border-violet-900/60 bg-gradient-to-br from-violet-50 via-white to-white dark:from-violet-950/30 dark:via-slate-900 dark:to-slate-900 overflow-hidden">
        <!-- Header -->
        <div class="px-5 py-4 flex items-start justify-between gap-3 border-b border-violet-100 dark:border-violet-900/40">
          <div class="flex items-start gap-3">
            <div class="w-9 h-9 rounded-xl bg-violet-500/15 text-violet-600 dark:text-violet-300 flex items-center justify-center text-lg shrink-0">🤖</div>
            <div>
              <h3 class="text-sm font-semibold text-slate-900 dark:text-white">{{ a.title }}</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">{{ a.summary }}</p>
            </div>
          </div>
          @if (a.confidence !== null) {
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full shrink-0" [class]="confClass(a.confidence)">
              {{ a.confidence | number:'1.0-0' }}% confianza
            </span>
          }
        </div>

        <!-- Campos -->
        <div class="px-5 py-4 grid gap-3 sm:grid-cols-2">
          @for (f of a.fields; track f.key) {
            <label class="block">
              <span class="text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                {{ f.label }}
                @if (f.confidence !== null && f.confidence < 70) {
                  <span class="text-amber-500" title="Confianza baja — revisa este campo">⚠</span>
                }
              </span>
              <input [ngModel]="edited()[f.key]" (ngModelChange)="setField(f.key, $event)"
                [disabled]="a.status !== 'pending_review' || !f.editable"
                class="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 disabled:opacity-60"
                [class.border-amber-300]="f.confidence !== null && f.confidence < 70"
                [class.border-slate-300]="!(f.confidence !== null && f.confidence < 70)"
                [class.dark:border-slate-600]="true" />
            </label>
          }
        </div>

        <!-- Ítems -->
        @if (a.line_items.length > 0) {
          <div class="px-5 pb-4">
            <div class="text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
              Ítems detectados ({{ a.line_items.length }})
            </div>
            <div class="rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
              <table class="min-w-full text-xs">
                <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                  <tr>
                    <th class="text-left px-3 py-1.5 font-medium">Descripción</th>
                    <th class="text-right px-3 py-1.5 font-medium">Cant.</th>
                    <th class="text-right px-3 py-1.5 font-medium">Costo unit.</th>
                    <th class="text-right px-3 py-1.5 font-medium">Total</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                  @for (it of a.line_items; track $index) {
                    <tr class="text-slate-700 dark:text-slate-300">
                      <td class="px-3 py-1.5">{{ it['description'] }}</td>
                      <td class="px-3 py-1.5 text-right tabular-nums">{{ it['quantity'] }}</td>
                      <td class="px-3 py-1.5 text-right tabular-nums">{{ it['unit_cost'] ?? '—' }}</td>
                      <td class="px-3 py-1.5 text-right tabular-nums">{{ it['line_total'] ?? '—' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>
        }

        <!-- Acciones -->
        @if (a.status === 'pending_review') {
          <div class="px-5 py-3 flex items-center justify-between gap-2 border-t border-violet-100 dark:border-violet-900/40 bg-white/60 dark:bg-slate-900/40">
            <button (click)="onDiscard()" [disabled]="busy()"
              class="text-xs text-rose-600 hover:underline disabled:opacity-50">Descartar</button>
            <div class="flex gap-2">
              <span class="text-[11px] text-slate-400 self-center mr-1">Edita lo que necesites y confirma</span>
              <button (click)="onConfirm()" [disabled]="busy()"
                class="rounded-md bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white px-4 py-2 text-sm font-medium">
                {{ busy() ? '…' : '✓ Confirmar y guardar' }}
              </button>
            </div>
          </div>
        } @else {
          <div class="px-5 py-3 border-t border-slate-100 dark:border-slate-800 text-xs"
            [class]="a.status === 'confirmed' ? 'text-emerald-600' : 'text-slate-400'">
            {{ a.status === 'confirmed' ? '✓ Confirmado y guardado' : 'Descartado' }}
          </div>
        }
      </div>
    }
  `,
})
export class ConfirmableActionComponent {
  private readonly ai = inject(AiService);

  action = input.required<ConfirmableAction>();
  confirmed = output<ConfirmableAction>();
  discarded = output<string>();

  busy = signal(false);
  private readonly _edited = signal<Record<string, unknown>>({});

  edited = computed(() => {
    // Inicializa el buffer de edición con los valores actuales la primera vez.
    if (Object.keys(this._edited()).length === 0) {
      const init: Record<string, unknown> = {};
      for (const f of this.action().fields) init[f.key] = f.value;
      return init;
    }
    return this._edited();
  });

  setField(key: string, value: unknown): void {
    this._edited.set({ ...this.edited(), [key]: value });
  }

  onConfirm(): void {
    const a = this.action();
    this.busy.set(true);
    // Reconstruye el payload editado: campos + line_items originales.
    const payload: Record<string, unknown> = { ...this.edited() };
    if (a.line_items.length) payload['line_items'] = a.line_items;
    this.ai.confirm(a.extraction_id, payload).subscribe({
      next: (res) => { this.busy.set(false); this.confirmed.emit(res); },
      error: () => this.busy.set(false),
    });
  }

  onDiscard(): void {
    const a = this.action();
    this.busy.set(true);
    this.ai.discard(a.extraction_id).subscribe({
      next: () => { this.busy.set(false); this.discarded.emit(a.extraction_id); },
      error: () => this.busy.set(false),
    });
  }

  confClass(c: number): string {
    if (c >= 85) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300';
    if (c >= 70) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300';
    return 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300';
  }
}
