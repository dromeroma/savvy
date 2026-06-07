import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import { LiquidationDetail, LiquidationTemplate } from '../../../core/models/hr.model';

const REASON_LABELS: Record<string, string> = {
  voluntary: 'Renuncia voluntaria', mutual: 'Mutuo acuerdo',
  with_cause: 'Despido con justa causa', without_cause: 'Despido sin justa causa',
  end_of_contract: 'Vencimiento del contrato', retirement: 'Pensión / jubilación',
  death: 'Fallecimiento', other: 'Otra causa',
};
const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador', finalized: 'Finalizada', paid: 'Pagada', cancelled: 'Cancelada',
};

@Component({
  selector: 'app-hr-liquidation-detail',
  imports: [CommonModule, FormsModule, RouterLink, DatePipe, DecimalPipe],
  template: `
    @if (loading()) {
      <p class="text-sm text-slate-500 dark:text-slate-400">Cargando…</p>
    } @else if (liq(); as l) {
      <div class="space-y-4 max-w-5xl">
        <header class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <a routerLink=".." class="text-xs text-slate-500 hover:underline">← Liquidaciones</a>
            <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {{ l.liquidation_number }}
            </h1>
            <p class="text-sm text-slate-500 dark:text-slate-400">
              {{ l.employee_name }} · {{ l.employee_code }} ·
              <span class="px-2 py-0.5 rounded-md text-xs" [class]="statusClass(l.status)">{{ statusLabel(l.status) }}</span>
            </p>
          </div>
          <div class="flex gap-2">
            <select [(ngModel)]="pdfTemplate"
              class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
              <option value="formal">PDF · Formal</option>
              <option value="moderna">PDF · Moderna</option>
              <option value="compacta">PDF · Compacta</option>
            </select>
            <button (click)="downloadPdf()" type="button"
              class="rounded-md bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 text-sm font-medium">
              ↓ Descargar PDF
            </button>
          </div>
        </header>

        <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div><div class="text-xs text-slate-500 dark:text-slate-400">Causa</div><div>{{ reasonLabel(l.termination_reason) }}</div></div>
            <div><div class="text-xs text-slate-500 dark:text-slate-400">Terminación</div><div>{{ l.termination_date | date:'mediumDate' }}</div></div>
            <div><div class="text-xs text-slate-500 dark:text-slate-400">Último día</div><div>{{ l.last_worked_date | date:'mediumDate' }}</div></div>
            <div><div class="text-xs text-slate-500 dark:text-slate-400">Ingreso</div><div>{{ l.contract_start_date | date:'mediumDate' }}</div></div>
            <div><div class="text-xs text-slate-500 dark:text-slate-400">Días totales</div><div class="font-mono">{{ l.days_worked_total }}</div></div>
            <div><div class="text-xs text-slate-500 dark:text-slate-400">Salario base</div><div class="font-mono">$ {{ +l.base_salary | number:'1.0-0' }}</div></div>
            <div><div class="text-xs text-slate-500 dark:text-slate-400">IBC</div><div class="font-mono">$ {{ +l.average_salary | number:'1.0-0' }}</div></div>
            <div><div class="text-xs text-slate-500 dark:text-slate-400">Cargo</div><div>{{ l.position_name || '—' }}</div></div>
          </div>
        </section>

        <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
          <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Detalle</h2>
          <table class="w-full text-sm">
            <thead class="text-xs text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
              <tr><th class="text-left py-2">Concepto</th><th class="text-right">Cantidad</th><th class="text-right">Base</th><th class="text-right">Valor</th></tr>
            </thead>
            <tbody>
              @for (it of l.items; track $index) {
                <tr [class.bg-rose-50/30]="it.kind === 'deduction'" [class.dark:bg-rose-900/10]="it.kind === 'deduction'"
                    class="border-b border-slate-100 dark:border-slate-800">
                  <td class="py-2">
                    <div class="font-medium">{{ it.concept_name }}</div>
                    @if (it.notes) { <div class="text-xs text-slate-500 dark:text-slate-400">{{ it.notes }}</div> }
                  </td>
                  <td class="text-right font-mono">{{ +it.quantity | number:'1.0-2' }}</td>
                  <td class="text-right font-mono">$ {{ +it.base_amount | number:'1.0-0' }}</td>
                  <td class="text-right font-mono font-semibold"
                      [class.text-rose-600]="it.kind === 'deduction'">
                    {{ it.kind === 'deduction' ? '-' : '' }}$ {{ +it.amount | number:'1.0-0' }}
                  </td>
                </tr>
              }
            </tbody>
            <tfoot class="text-sm">
              <tr><td colspan="3" class="text-right py-1 pr-2">Devengado</td><td class="text-right font-mono font-semibold">$ {{ +l.total_earnings | number:'1.0-0' }}</td></tr>
              <tr><td colspan="3" class="text-right py-1 pr-2 text-rose-600">Deducciones</td><td class="text-right font-mono text-rose-600">- $ {{ +l.total_deductions | number:'1.0-0' }}</td></tr>
              <tr><td colspan="3" class="text-right py-2 pr-2 font-bold border-t border-slate-200">NETO A PAGAR</td><td class="text-right font-mono text-lg font-bold text-emerald-700 dark:text-emerald-300 border-t border-slate-200">$ {{ +l.net_amount | number:'1.0-0' }} {{ l.currency }}</td></tr>
            </tfoot>
          </table>
        </section>

        @if (l.notes) {
          <section class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <p class="text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">Observaciones</p>
            <p class="text-sm text-amber-900 dark:text-amber-200 whitespace-pre-line">{{ l.notes }}</p>
          </section>
        }

        <div class="flex justify-end gap-2">
          @if (l.status === 'draft') {
            <button (click)="finalize()" type="button" [disabled]="acting()"
              class="rounded-md border border-amber-500 text-amber-700 hover:bg-amber-50 dark:hover:bg-amber-900/20 px-4 py-2 text-sm">
              Finalizar liquidación
            </button>
          } @else if (l.status === 'finalized') {
            <button (click)="markPaid()" type="button" [disabled]="acting()"
              class="rounded-md bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 text-sm font-medium">
              Marcar como pagada
            </button>
          }
        </div>
      </div>
    } @else {
      <p class="text-sm text-rose-600">No se encontró la liquidación.</p>
    }
  `,
})
export class HrLiquidationDetailComponent implements OnInit {
  private readonly api = inject(HrApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  liq = signal<LiquidationDetail | null>(null);
  loading = signal(true);
  acting = signal(false);
  pdfTemplate: LiquidationTemplate = 'formal';

  ngOnInit(): void { this.reload(); }

  reload(): void {
    const id = this.route.snapshot.paramMap.get('id') || '';
    this.api.getLiquidation(id).subscribe({
      next: (l) => {
        this.liq.set(l);
        this.pdfTemplate = (l.pdf_template as LiquidationTemplate) || 'formal';
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  downloadPdf(): void {
    const id = this.liq()!.id;
    this.api.downloadLiquidationPdf(id, this.pdfTemplate).subscribe(({ blob, filename }) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `liquidacion-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  finalize(): void {
    const l = this.liq();
    if (!l) return;
    this.acting.set(true);
    this.api.finalizeLiquidation(l.id).subscribe({
      next: () => { this.acting.set(false); this.reload(); },
      error: () => this.acting.set(false),
    });
  }

  markPaid(): void {
    const l = this.liq();
    if (!l) return;
    this.acting.set(true);
    this.api.markLiquidationPaid(l.id).subscribe({
      next: () => { this.acting.set(false); this.reload(); },
      error: () => this.acting.set(false),
    });
  }

  reasonLabel(r: string): string { return REASON_LABELS[r] || r; }
  statusLabel(s: string): string { return STATUS_LABELS[s] || s; }
  statusClass(s: string): string {
    const map: Record<string, string> = {
      draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      finalized: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      paid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    };
    return map[s] || '';
  }
}
