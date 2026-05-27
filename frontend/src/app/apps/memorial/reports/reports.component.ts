import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  EmployeeRankingReport,
  IncomeReport,
  OperationalKpis,
  PlanRankingReport,
  ServicesByTypeReport,
} from '../../../core/models/memorial.model';

type Tab = 'overview' | 'income' | 'services' | 'plans' | 'employees';

@Component({
  selector: 'app-memorial-reports',
  imports: [CommonModule, FormsModule, DatePipe, DecimalPipe],
  templateUrl: './reports.component.html',
})
export class MemorialReportsComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);

  readonly tabs: { value: Tab; label: string }[] = [
    { value: 'overview', label: 'KPIs' },
    { value: 'income', label: 'Ingresos' },
    { value: 'services', label: 'Servicios' },
    { value: 'plans', label: 'Planes' },
    { value: 'employees', label: 'Empleados' },
  ];

  tab = signal<Tab>('overview');

  // Filtros
  dateFrom = '';
  dateTo = '';

  // Data
  kpis = signal<OperationalKpis | null>(null);
  income = signal<IncomeReport | null>(null);
  services = signal<ServicesByTypeReport | null>(null);
  plans = signal<PlanRankingReport | null>(null);
  employees = signal<EmployeeRankingReport | null>(null);
  loading = signal(false);

  // Income chart computed
  incomeChart = computed(() => {
    const r = this.income();
    if (!r || r.points.length === 0) return null;
    const max = Math.max(...r.points.map((p) => +p.total));
    return { max, points: r.points };
  });

  servicesChart = computed(() => {
    const r = this.services();
    if (!r || r.items.length === 0) return null;
    const max = Math.max(...r.items.map((i) => i.count));
    return { max, items: r.items };
  });

  ngOnInit(): void {
    const today = new Date();
    const sixMonthsAgo = new Date(today);
    sixMonthsAgo.setMonth(today.getMonth() - 5);
    sixMonthsAgo.setDate(1);
    this.dateFrom = sixMonthsAgo.toISOString().slice(0, 10);
    this.dateTo = today.toISOString().slice(0, 10);
    this.loadAll();
  }

  setTab(t: Tab): void { this.tab.set(t); }

  loadAll(): void {
    this.loading.set(true);
    const params = { date_from: this.dateFrom, date_to: this.dateTo };
    this.memorial.operationalKpis(30).subscribe({ next: (r) => this.kpis.set(r) });
    this.memorial.incomeReport(params).subscribe({ next: (r) => this.income.set(r) });
    this.memorial.servicesByType(params).subscribe({ next: (r) => this.services.set(r) });
    this.memorial.planRanking().subscribe({ next: (r) => this.plans.set(r) });
    this.memorial.employeeRanking(params).subscribe({
      next: (r) => { this.employees.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  serviceTypeLabel(t: string): string {
    const map: Record<string, string> = {
      velacion: 'Velación',
      cremacion: 'Cremación',
      entierro: 'Entierro',
      velacion_cremacion: 'Velación + Cremación',
      velacion_entierro: 'Velación + Entierro',
      velacion_cremacion_entierro: 'Velación + Cremación + Entierro',
    };
    return map[t] || t;
  }

  exportIncomeCsv(): void {
    const r = this.income();
    if (!r) return;
    const header = 'Periodo,Cuotas exequiales,Ingresos servicios,Total\n';
    const rows = r.points.map((p) =>
      `${p.period},${p.exequial_dues},${p.service_income},${p.total}`,
    ).join('\n');
    const csv = header + rows + `\n,,Total,${r.grand_total}`;
    this.download(csv, `ingresos-${r.date_from}_${r.date_to}.csv`);
  }

  exportServicesCsv(): void {
    const r = this.services();
    if (!r) return;
    const header = 'Tipo,Cantidad,Ingresos\n';
    const rows = r.items.map((i) =>
      `${this.serviceTypeLabel(i.service_type)},${i.count},${i.total_revenue}`,
    ).join('\n');
    const csv = header + rows + `\nTotal,${r.total_count},${r.total_revenue}`;
    this.download(csv, `servicios-${r.date_from}_${r.date_to}.csv`);
  }

  exportPlansCsv(): void {
    const r = this.plans();
    if (!r) return;
    const header = 'Código,Plan,Contratos,Activos,Ingresos\n';
    const rows = r.items.map((i) =>
      `${i.plan_code},${i.plan_name},${i.contracts_count},${i.active_count},${i.total_revenue}`,
    ).join('\n');
    this.download(header + rows, 'ranking-planes.csv');
  }

  exportEmployeesCsv(): void {
    const r = this.employees();
    if (!r) return;
    const header = 'Código,Empleado,Cargo,Días presente,Horas trabajadas\n';
    const rows = r.items.map((i) =>
      `${i.employee_code},${i.employee_name},${i.position_name || '—'},${i.days_present},${i.hours_worked}`,
    ).join('\n');
    this.download(header + rows, `empleados-${r.date_from}_${r.date_to}.csv`);
  }

  private download(content: string, filename: string): void {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}
