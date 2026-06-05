import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import { HrPayroll, HrPayrollPeriod } from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-hr-payroll-period-detail',
  imports: [CommonModule, RouterLink],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      @if (loading()) {
        <p class="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
      } @else if (period(); as p) {
        <header class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <a routerLink="/hr/payroll/periods" class="text-xs text-brand-600 hover:underline">← Volver a períodos</a>
            <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100 mt-1">{{ p.name }}</h1>
            <p class="text-sm text-slate-600 dark:text-slate-400">
              <span class="font-mono">{{ p.code }}</span> · {{ p.start_date }} → {{ p.end_date }}
              @if (p.payment_date) { · Pago {{ p.payment_date }} }
            </p>
          </div>
          <span class="text-xs px-3 py-1 rounded-md self-start" [class]="statusClass(p.status)">
            {{ p.status }}
          </span>
        </header>

        <!-- Totales -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
            <p class="text-xs text-slate-500 dark:text-slate-400">Empleados</p>
            <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{{ p.employee_count }}</p>
          </div>
          <div class="rounded-2xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20 p-4">
            <p class="text-xs text-emerald-700 dark:text-emerald-300">Total devengado</p>
            <p class="text-2xl font-bold text-emerald-800 dark:text-emerald-200 mt-1">$ {{ (+p.total_gross) | number:'1.0-0' }}</p>
          </div>
          <div class="rounded-2xl border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-900/20 p-4">
            <p class="text-xs text-rose-700 dark:text-rose-300">Total deducciones</p>
            <p class="text-2xl font-bold text-rose-800 dark:text-rose-200 mt-1">$ {{ (+p.total_deductions) | number:'1.0-0' }}</p>
          </div>
          <div class="rounded-2xl border border-brand-200 dark:border-brand-800 bg-brand-50 dark:bg-brand-900/20 p-4">
            <p class="text-xs text-brand-700 dark:text-brand-300">Neto a pagar</p>
            <p class="text-2xl font-bold text-brand-700 dark:text-brand-300 mt-1">$ {{ (+p.total_net) | number:'1.0-0' }}</p>
          </div>
        </section>

        <!-- Lista de liquidaciones -->
        <section class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 overflow-x-auto">
          <div class="px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
            <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Empleados liquidados ({{ payrolls().length }})
            </h2>
          </div>
          @if (payrolls().length === 0) {
            <p class="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
              Aún no se ha calculado este período. Ve a la lista y dale "Calcular".
            </p>
          } @else {
            <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-4 py-2 font-medium">Código</th>
                  <th class="text-left px-4 py-2 font-medium">Empleado</th>
                  <th class="text-left px-4 py-2 font-medium">Departamento</th>
                  <th class="text-right px-4 py-2 font-medium">Días</th>
                  <th class="text-right px-4 py-2 font-medium">Salario base</th>
                  <th class="text-right px-4 py-2 font-medium">Devengado</th>
                  <th class="text-right px-4 py-2 font-medium">Deducciones</th>
                  <th class="text-right px-4 py-2 font-medium">Neto</th>
                  <th class="text-right px-4 py-2 font-medium">PDF</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @for (pr of payrolls(); track pr.id) {
                  <tr>
                    <td class="px-4 py-2 font-mono text-xs">{{ pr.employee_code }}</td>
                    <td class="px-4 py-2 font-medium">{{ pr.employee_name }}</td>
                    <td class="px-4 py-2 text-xs text-slate-600 dark:text-slate-400">{{ pr.department_name || '—' }}</td>
                    <td class="px-4 py-2 text-right">{{ pr.worked_days }}</td>
                    <td class="px-4 py-2 text-right font-mono text-xs">$ {{ (+pr.base_salary) | number:'1.0-0' }}</td>
                    <td class="px-4 py-2 text-right font-mono text-xs">$ {{ (+pr.total_earnings) | number:'1.0-0' }}</td>
                    <td class="px-4 py-2 text-right font-mono text-xs text-rose-600">$ {{ (+pr.total_deductions) | number:'1.0-0' }}</td>
                    <td class="px-4 py-2 text-right font-mono text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                      $ {{ (+pr.net_amount) | number:'1.0-0' }}
                    </td>
                    <td class="px-4 py-2 text-right">
                      <button (click)="downloadPdf(pr)" type="button" class="text-xs text-brand-600 hover:underline">PDF</button>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          }
        </section>
      }
    </div>
  `,
})
export class HrPayrollPeriodDetailComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  loading = signal(true);
  period = signal<HrPayrollPeriod | null>(null);
  payrolls = signal<HrPayroll[]>([]);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) { this.router.navigate(['/hr/payroll/periods']); return; }
    this.load(id);
  }

  private load(id: string): void {
    this.loading.set(true);
    this.hr.getPayrollPeriod(id).subscribe({
      next: (p) => { this.period.set(p); this.loading.set(false); },
      error: () => { this.loading.set(false); this.router.navigate(['/hr/payroll/periods']); },
    });
    this.hr.listPayrollsByPeriod(id).subscribe({
      next: (r) => this.payrolls.set(r),
    });
  }

  downloadPdf(pr: HrPayroll): void {
    this.hr.downloadPayrollPdf(pr.id).subscribe({
      next: ({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `desprendible-${pr.employee_code}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo descargar.' }),
    });
  }

  statusClass(s: string): string {
    const map: Record<string, string> = {
      draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      calculating: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      calculated: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      approved: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
      paid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      closed: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    };
    return map[s] || '';
  }
}
