import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrPayrollPeriod,
  HrReportAbsenteeismResponse,
  HrReportCostResponse,
  HrReportHeadcountResponse,
  HrReportTenureResponse,
  HrReportTrainingSummary,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-hr-reports',
  imports: [CommonModule, FormsModule],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-6">
      <header>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Reportes HR</h1>
        <p class="text-sm text-slate-600 dark:text-slate-400">Plantilla, antigüedad, costo, ausentismo y capacitación.</p>
      </header>

      <!-- Headcount + Tenure (2 columnas) -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Plantilla por departamento</h2>
          @if (headcount(); as h) {
            <p class="text-xs text-slate-500 dark:text-slate-400 mb-3">Total: <span class="font-mono text-slate-900 dark:text-slate-100">{{ h.total }}</span></p>
            <div class="space-y-2">
              @for (r of h.rows; track r.label) {
                <div>
                  <div class="flex justify-between text-xs text-slate-700 dark:text-slate-300 mb-1">
                    <span>{{ r.label }}</span>
                    <span class="font-mono">{{ r.count }} ({{ r.percentage }}%)</span>
                  </div>
                  <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div class="h-full bg-brand-500" [style.width.%]="r.percentage"></div>
                  </div>
                </div>
              }
            </div>
          } @else {
            <p class="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
          }
        </div>

        <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Antigüedad de empleados</h2>
          @if (tenure(); as t) {
            <div class="flex justify-between mb-3 text-xs">
              <span class="text-slate-500 dark:text-slate-400">Total: <span class="font-mono text-slate-900 dark:text-slate-100">{{ t.total }}</span></span>
              <span class="text-slate-500 dark:text-slate-400">Promedio: <span class="font-mono text-slate-900 dark:text-slate-100">{{ t.avg_years }} años</span></span>
            </div>
            <div class="space-y-2">
              @for (b of t.buckets; track b.label) {
                <div>
                  <div class="flex justify-between text-xs text-slate-700 dark:text-slate-300 mb-1">
                    <span>{{ b.label }}</span>
                    <span class="font-mono">{{ b.count }}</span>
                  </div>
                  <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div class="h-full bg-emerald-500"
                      [style.width.%]="t.total > 0 ? (b.count / t.total * 100) : 0"></div>
                  </div>
                </div>
              }
            </div>
          } @else {
            <p class="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
          }
        </div>
      </section>

      <!-- Costo por departamento -->
      <section class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
          <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Costo de nómina por departamento</h2>
          <label class="flex items-center gap-2 text-xs">
            <span class="text-slate-600 dark:text-slate-400">Período:</span>
            <select [(ngModel)]="selectedPeriodId" (change)="loadCost()"
              class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1 text-xs">
              <option value="">— Selecciona período —</option>
              @for (p of periods(); track p.id) {
                <option [value]="p.id">{{ p.code }} — {{ p.name }}</option>
              }
            </select>
          </label>
        </div>
        @if (cost(); as c) {
          <p class="text-sm text-slate-600 dark:text-slate-400 mb-3">
            Total: <span class="font-mono text-lg font-bold text-emerald-700 dark:text-emerald-300">$ {{ (+c.total) | number:'1.0-0' }}</span>
          </p>
          <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
            <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
              <tr>
                <th class="text-left px-3 py-2 font-medium">Departamento</th>
                <th class="text-right px-3 py-2 font-medium">Empleados</th>
                <th class="text-right px-3 py-2 font-medium">Costo total</th>
                <th class="text-right px-3 py-2 font-medium">% del total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              @for (r of c.rows; track r.department_name) {
                <tr>
                  <td class="px-3 py-2">{{ r.department_name }}</td>
                  <td class="px-3 py-2 text-right">{{ r.employee_count }}</td>
                  <td class="px-3 py-2 text-right font-mono">$ {{ (+r.total_cost) | number:'1.0-0' }}</td>
                  <td class="px-3 py-2 text-right">{{ ((+r.total_cost) / (+c.total) * 100) | number:'1.0-2' }}%</td>
                </tr>
              }
            </tbody>
          </table>
        } @else if (!selectedPeriodId) {
          <p class="text-sm text-slate-500 dark:text-slate-400">Selecciona un período de nómina para ver el desglose.</p>
        } @else {
          <p class="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
        }
      </section>

      <!-- Ausentismo -->
      <section class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
          <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Ausentismo</h2>
          <div class="flex gap-2 items-end text-xs">
            <label class="flex flex-col text-slate-600 dark:text-slate-400">
              <span class="mb-1">Desde</span>
              <input type="date" [(ngModel)]="absFrom" (change)="loadAbs()"
                class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1 text-xs" />
            </label>
            <label class="flex flex-col text-slate-600 dark:text-slate-400">
              <span class="mb-1">Hasta</span>
              <input type="date" [(ngModel)]="absTo" (change)="loadAbs()"
                class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1 text-xs" />
            </label>
          </div>
        </div>
        @if (absent(); as a) {
          @if (a.rows.length === 0) {
            <p class="text-sm text-slate-500 dark:text-slate-400">Sin ausencias en el período.</p>
          } @else {
            <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-3 py-2 font-medium">Empleado</th>
                  <th class="text-right px-3 py-2 font-medium">Ausencias</th>
                  <th class="text-right px-3 py-2 font-medium">Tardanzas</th>
                  <th class="text-right px-3 py-2 font-medium">Licencias</th>
                  <th class="text-right px-3 py-2 font-medium">Total</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @for (r of a.rows; track r.employee_id) {
                  <tr>
                    <td class="px-3 py-2">
                      <span class="font-medium">{{ r.employee_name }}</span>
                      <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono ml-2">{{ r.employee_code }}</span>
                    </td>
                    <td class="px-3 py-2 text-right">{{ r.absent_days }}</td>
                    <td class="px-3 py-2 text-right">{{ r.late_days }}</td>
                    <td class="px-3 py-2 text-right">{{ r.leave_days }}</td>
                    <td class="px-3 py-2 text-right font-mono font-semibold">{{ r.total_days }}</td>
                  </tr>
                }
              </tbody>
            </table>
          }
        }
      </section>

      <!-- Resumen capacitaciones -->
      <section class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
        <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Resumen de capacitaciones</h2>
        @if (training()?.length) {
          <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
            <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
              <tr>
                <th class="text-left px-3 py-2 font-medium">Curso</th>
                <th class="text-right px-3 py-2 font-medium">Inscritos</th>
                <th class="text-right px-3 py-2 font-medium">Completados</th>
                <th class="text-right px-3 py-2 font-medium">En curso</th>
                <th class="text-right px-3 py-2 font-medium">Prom. puntaje</th>
                <th class="text-right px-3 py-2 font-medium">Costo total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              @for (r of training(); track r.course_id) {
                <tr>
                  <td class="px-3 py-2">{{ r.course_name }} <span class="text-[11px] font-mono text-slate-500 dark:text-slate-400">[{{ r.course_code }}]</span></td>
                  <td class="px-3 py-2 text-right">{{ r.enrollments }}</td>
                  <td class="px-3 py-2 text-right text-emerald-700 dark:text-emerald-300">{{ r.completed }}</td>
                  <td class="px-3 py-2 text-right text-amber-700 dark:text-amber-300">{{ r.in_progress }}</td>
                  <td class="px-3 py-2 text-right font-mono">{{ r.avg_score ?? '—' }}</td>
                  <td class="px-3 py-2 text-right font-mono">$ {{ (+r.total_cost) | number:'1.0-0' }}</td>
                </tr>
              }
            </tbody>
          </table>
        } @else {
          <p class="text-sm text-slate-500 dark:text-slate-400">Sin datos de capacitación.</p>
        }
      </section>
    </div>
  `,
})
export class HrReportsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  headcount = signal<HrReportHeadcountResponse | null>(null);
  tenure = signal<HrReportTenureResponse | null>(null);
  cost = signal<HrReportCostResponse | null>(null);
  absent = signal<HrReportAbsenteeismResponse | null>(null);
  training = signal<HrReportTrainingSummary[] | null>(null);

  periods = signal<HrPayrollPeriod[]>([]);
  selectedPeriodId = '';

  absFrom = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
  absTo = new Date().toISOString().slice(0, 10);

  ngOnInit(): void {
    this.hr.reportHeadcountByDepartment().subscribe({ next: (r) => this.headcount.set(r) });
    this.hr.reportTenureDistribution().subscribe({ next: (r) => this.tenure.set(r) });
    this.hr.reportTrainingSummary().subscribe({ next: (r) => this.training.set(r) });
    this.hr.listPayrollPeriods({ status: 'paid' }).subscribe({
      next: (r) => {
        this.periods.set(r);
        if (r.length > 0) {
          this.selectedPeriodId = r[0].id;
          this.loadCost();
        }
      },
    });
    this.loadAbs();
  }

  loadCost(): void {
    if (!this.selectedPeriodId) { this.cost.set(null); return; }
    this.hr.reportCostByDepartment(this.selectedPeriodId).subscribe({
      next: (r) => this.cost.set(r),
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar.' }),
    });
  }

  loadAbs(): void {
    if (!this.absFrom || !this.absTo) return;
    this.hr.reportAbsenteeism(this.absFrom, this.absTo).subscribe({
      next: (r) => this.absent.set(r),
    });
  }
}
