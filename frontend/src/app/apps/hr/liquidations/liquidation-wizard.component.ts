import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrEmployee,
  LiquidationCalculationInput,
  LiquidationCreate,
  LiquidationItem,
  LiquidationPreview,
  LiquidationTemplate,
  TerminationReason,
} from '../../../core/models/hr.model';

const REASONS: { value: TerminationReason; label: string }[] = [
  { value: 'voluntary', label: 'Renuncia voluntaria' },
  { value: 'mutual', label: 'Mutuo acuerdo' },
  { value: 'with_cause', label: 'Despido con justa causa' },
  { value: 'without_cause', label: 'Despido sin justa causa' },
  { value: 'end_of_contract', label: 'Vencimiento del contrato' },
  { value: 'retirement', label: 'Pensión / jubilación' },
  { value: 'death', label: 'Fallecimiento' },
  { value: 'other', label: 'Otra causa' },
];

@Component({
  selector: 'app-hr-liquidation-wizard',
  imports: [CommonModule, FormsModule, DecimalPipe],
  template: `
    <div class="space-y-5 max-w-5xl">
      <header>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Nueva liquidación</h1>
        @if (employee()) {
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Empleado: <strong>{{ employee()!.first_name }} {{ employee()!.last_name }}</strong>
            · <span class="font-mono">{{ employee()!.employee_code }}</span>
          </p>
        }
      </header>

      <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-5 grid gap-4 md:grid-cols-2">
        <div class="md:col-span-2">
          <h2 class="text-base font-semibold text-slate-900 dark:text-slate-100">Datos de terminación</h2>
        </div>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Causa *</span>
          <select [(ngModel)]="input.termination_reason" (ngModelChange)="recalc()"
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
            @for (r of reasons; track r.value) { <option [value]="r.value">{{ r.label }}</option> }
          </select>
        </label>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Fecha de terminación *</span>
          <input [(ngModel)]="input.termination_date" (ngModelChange)="recalc()" type="date" required
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Último día laborado</span>
          <input [(ngModel)]="input.last_worked_date" (ngModelChange)="recalc()" type="date"
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Días pendientes del último período</span>
          <input [(ngModel)]="input.pending_period_days" (ngModelChange)="recalc()" type="number" min="0"
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="block">
          <span class="text-xs text-slate-600 dark:text-slate-400">Días vacaciones pendientes (0 = auto-calcular)</span>
          <input [(ngModel)]="input.vacation_days_pending" (ngModelChange)="recalc()" type="number" min="0" step="0.5"
            class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
        </label>
        <label class="flex items-center gap-2 mt-6">
          <input [(ngModel)]="input.has_legal_protection" (ngModelChange)="recalc()" type="checkbox" class="h-4 w-4" />
          <span class="text-sm text-slate-700 dark:text-slate-300">Empleado con fuero (sindical o maternal)</span>
        </label>
      </section>

      <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-base font-semibold text-slate-900 dark:text-slate-100">Cálculo</h2>
          <button (click)="recalc()" type="button" class="text-xs text-brand-600 hover:underline">↻ Recalcular</button>
        </div>

        @if (calculating()) {
          <p class="text-sm text-slate-500 dark:text-slate-400">Calculando…</p>
        } @else if (!preview()) {
          <p class="text-sm text-slate-500 dark:text-slate-400">Completa los datos para previsualizar el cálculo.</p>
        } @else {
          <div class="grid gap-3 md:grid-cols-4 mb-4">
            <div class="bg-slate-50 dark:bg-slate-800/50 rounded p-3">
              <div class="text-xs text-slate-500 dark:text-slate-400">Salario base</div>
              <div class="font-mono text-lg font-semibold">$ {{ +preview()!.base_salary | number:'1.0-0' }}</div>
            </div>
            <div class="bg-slate-50 dark:bg-slate-800/50 rounded p-3">
              <div class="text-xs text-slate-500 dark:text-slate-400">IBC</div>
              <div class="font-mono text-lg font-semibold">$ {{ +preview()!.average_salary | number:'1.0-0' }}</div>
            </div>
            <div class="bg-slate-50 dark:bg-slate-800/50 rounded p-3">
              <div class="text-xs text-slate-500 dark:text-slate-400">Días totales</div>
              <div class="font-mono text-lg font-semibold">{{ preview()!.days_worked_total }}</div>
            </div>
            <div class="bg-emerald-50 dark:bg-emerald-900/30 rounded p-3 border border-emerald-200 dark:border-emerald-800">
              <div class="text-xs text-emerald-700 dark:text-emerald-300">Neto a pagar</div>
              <div class="font-mono text-lg font-bold text-emerald-700 dark:text-emerald-300">$ {{ +preview()!.net_amount | number:'1.0-0' }}</div>
            </div>
          </div>

          <table class="w-full text-sm">
            <thead class="text-xs text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
              <tr>
                <th class="text-left py-2 pl-1">Concepto</th>
                <th class="text-right py-2">Cantidad</th>
                <th class="text-right py-2">Base</th>
                <th class="text-right py-2 pr-1">Valor</th>
                <th class="w-10"></th>
              </tr>
            </thead>
            <tbody>
              @for (it of items(); track $index; let i = $index) {
                <tr [class.bg-rose-50/30]="it.kind === 'deduction'" [class.dark:bg-rose-900/10]="it.kind === 'deduction'" class="border-b border-slate-100 dark:border-slate-800">
                  <td class="py-1 pl-1">
                    <input [(ngModel)]="it.concept_name" class="w-full bg-transparent px-1 py-0.5 text-sm border border-transparent focus:border-brand-300 rounded" />
                    @if (it.notes) { <div class="text-xs text-slate-500 dark:text-slate-400 pl-1">{{ it.notes }}</div> }
                  </td>
                  <td class="py-1 text-right"><input [(ngModel)]="it.quantity" type="number" step="0.01" class="w-20 bg-transparent text-right font-mono text-sm border border-transparent focus:border-brand-300 rounded px-1" /></td>
                  <td class="py-1 text-right"><input [(ngModel)]="it.base_amount" type="number" class="w-28 bg-transparent text-right font-mono text-sm border border-transparent focus:border-brand-300 rounded px-1" /></td>
                  <td class="py-1 pr-1 text-right">
                    <input [(ngModel)]="it.amount" (ngModelChange)="recomputeTotals()" type="number"
                      class="w-32 bg-transparent text-right font-mono text-sm font-semibold border border-transparent focus:border-brand-300 rounded px-1"
                      [class.text-rose-600]="it.kind === 'deduction'" />
                  </td>
                  <td class="py-1 text-right">
                    <button (click)="removeItem(i)" type="button" class="text-rose-500 hover:text-rose-700 text-xs">×</button>
                  </td>
                </tr>
              }
            </tbody>
            <tfoot class="text-sm">
              <tr><td colspan="3" class="text-right py-1 pr-2">Devengado:</td><td class="text-right font-mono font-semibold">$ {{ totalEarnings() | number:'1.0-0' }}</td><td></td></tr>
              <tr><td colspan="3" class="text-right py-1 pr-2 text-rose-600">Deducciones:</td><td class="text-right font-mono text-rose-600">- $ {{ totalDeductions() | number:'1.0-0' }}</td><td></td></tr>
              <tr><td colspan="3" class="text-right py-2 pr-2 font-bold border-t border-slate-200">NETO:</td><td class="text-right font-mono text-base font-bold text-emerald-700 dark:text-emerald-300 border-t border-slate-200">$ {{ netAmount() | number:'1.0-0' }}</td><td></td></tr>
            </tfoot>
          </table>

          <div class="flex flex-wrap gap-2 mt-3">
            <button (click)="addItem('earning')" type="button" class="text-xs px-3 py-1 rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800">+ Devengado manual</button>
            <button (click)="addItem('deduction')" type="button" class="text-xs px-3 py-1 rounded border border-rose-300 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-900/20">+ Deducción manual</button>
          </div>
        }
      </section>

      <section class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-5 space-y-3">
        <div>
          <label class="block">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Observaciones</span>
            <textarea [(ngModel)]="notes" rows="3"
              placeholder="Información adicional, nota interna, etc."
              class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
          </label>
        </div>
        <div>
          <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Plantilla PDF</span>
          <div class="flex gap-2 mt-1">
            @for (t of templates; track t) {
              <button type="button" (click)="pdfTemplate = t"
                class="px-3 py-1 rounded text-xs border"
                [class.bg-brand-600]="pdfTemplate === t" [class.text-white]="pdfTemplate === t"
                [class.border-brand-600]="pdfTemplate === t"
                [class.border-slate-300]="pdfTemplate !== t" [class.dark:border-slate-600]="pdfTemplate !== t">
                {{ t }}
              </button>
            }
          </div>
        </div>
      </section>

      @if (errorMsg()) { <div class="rounded-md bg-rose-50 border border-rose-200 text-rose-800 px-4 py-2 text-sm">{{ errorMsg() }}</div> }

      <div class="flex justify-end gap-2">
        <button (click)="cancel()" type="button"
          class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
        <button (click)="save()" type="button" [disabled]="saving() || !preview()"
          class="rounded-md bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-5 py-2 text-sm font-medium">
          {{ saving() ? 'Guardando…' : 'Crear liquidación (borrador)' }}
        </button>
      </div>
    </div>
  `,
})
export class HrLiquidationWizardComponent implements OnInit {
  private readonly api = inject(HrApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly reasons = REASONS;
  readonly templates: LiquidationTemplate[] = ['formal', 'moderna', 'compacta'];

  employee = signal<HrEmployee | null>(null);
  preview = signal<LiquidationPreview | null>(null);
  items = signal<LiquidationItem[]>([]);
  calculating = signal(false);
  saving = signal(false);
  errorMsg = signal('');

  input = {
    employee_id: '',
    termination_date: new Date().toISOString().slice(0, 10),
    termination_reason: 'voluntary' as TerminationReason,
    last_worked_date: '',
    pending_period_days: 0,
    vacation_days_pending: '0',
    has_legal_protection: false,
  };
  notes = '';
  pdfTemplate: LiquidationTemplate = 'formal';

  ngOnInit(): void {
    this.input.employee_id = this.route.snapshot.paramMap.get('employeeId') || '';
    this.api.getEmployee(this.input.employee_id).subscribe({
      next: (e) => {
        this.employee.set(e);
        if (!this.input.last_worked_date) this.input.last_worked_date = this.input.termination_date;
        this.recalc();
      },
      error: () => this.errorMsg.set('No se pudo cargar el empleado.'),
    });
    this.api.getSettings().subscribe((s) => {
      this.pdfTemplate = s.default_liquidation_template;
      if (s.liquidation_notes_default) this.notes = s.liquidation_notes_default;
    });
  }

  recalc(): void {
    if (!this.input.employee_id || !this.input.termination_date) return;
    this.calculating.set(true);
    this.errorMsg.set('');
    const payload: LiquidationCalculationInput = {
      employee_id: this.input.employee_id,
      termination_date: this.input.termination_date,
      termination_reason: this.input.termination_reason,
      last_worked_date: this.input.last_worked_date || this.input.termination_date,
      pending_period_days: Number(this.input.pending_period_days) || 0,
      vacation_days_pending: String(this.input.vacation_days_pending || 0),
      has_legal_protection: !!this.input.has_legal_protection,
    };
    this.api.calculateLiquidation(payload).subscribe({
      next: (p) => {
        this.preview.set(p);
        this.items.set(p.items.map((i) => ({ ...i })));
        this.calculating.set(false);
      },
      error: (err) => {
        this.errorMsg.set(err?.error?.detail || 'Error en el cálculo.');
        this.calculating.set(false);
      },
    });
  }

  addItem(kind: 'earning' | 'deduction'): void {
    const max = this.items().reduce((m, i) => Math.max(m, i.sort_order || 0), 0);
    this.items.update((arr) => [
      ...arr,
      {
        concept_code: kind === 'earning' ? 'manual_earning' : 'manual_deduction',
        concept_name: kind === 'earning' ? 'Bonificación manual' : 'Deducción manual',
        kind, quantity: '1', base_amount: '0', rate: null, amount: '0',
        is_manual: true, sort_order: max + 1, notes: null,
      },
    ]);
    this.recomputeTotals();
  }

  removeItem(i: number): void {
    this.items.update((arr) => arr.filter((_, idx) => idx !== i));
    this.recomputeTotals();
  }

  totalEarnings(): number {
    return this.items().filter((i) => i.kind === 'earning').reduce((sum, i) => sum + (+i.amount || 0), 0);
  }
  totalDeductions(): number {
    return this.items().filter((i) => i.kind === 'deduction').reduce((sum, i) => sum + (+i.amount || 0), 0);
  }
  netAmount(): number {
    return this.totalEarnings() - this.totalDeductions();
  }
  recomputeTotals(): void { /* signals re-evaluate automatically; method kept for ngModelChange hook */ }

  save(): void {
    if (!this.preview()) return;
    this.saving.set(true);
    this.errorMsg.set('');
    const payload: LiquidationCreate = {
      employee_id: this.input.employee_id,
      termination_date: this.input.termination_date,
      termination_reason: this.input.termination_reason,
      last_worked_date: this.input.last_worked_date || this.input.termination_date,
      pending_period_days: Number(this.input.pending_period_days) || 0,
      vacation_days_pending: String(this.input.vacation_days_pending || 0),
      has_legal_protection: !!this.input.has_legal_protection,
      notes: this.notes || null,
      pdf_template: this.pdfTemplate,
      items_override: this.items().map((i) => ({
        ...i,
        quantity: String(i.quantity),
        base_amount: String(i.base_amount),
        amount: String(i.amount),
      })),
    };
    this.api.createLiquidation(payload).subscribe({
      next: (liq) => this.router.navigate(['../../liquidations', liq.id], { relativeTo: this.route }),
      error: (err) => {
        this.errorMsg.set(err?.error?.detail || 'No se pudo crear la liquidación.');
        this.saving.set(false);
      },
    });
  }

  cancel(): void {
    this.router.navigate(['../../employees', this.input.employee_id], { relativeTo: this.route });
  }
}
