import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';

interface TitheOfTithe {
  total_tithes: number;
  total_offerings: number;
  base_amount: number;
  tithe_of_tithe: number;
}

interface MonthlySummary {
  total_income: number;
  total_expenses: number;
  net: number;
  tithe_of_tithe: TitheOfTithe | null;
}

@Component({
  selector: 'app-reports-dashboard',
  imports: [CommonModule, FormsModule],
  templateUrl: './reports-dashboard.component.html',
})
export class ReportsDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  currentYear = new Date().getFullYear();
  currentMonth = new Date().getMonth() + 1;

  selectedYear = signal(this.currentYear);
  selectedMonth = signal(this.currentMonth);
  summary = signal<MonthlySummary | null>(null);
  loading = signal(true);
  error = signal('');

  years: number[] = [];
  months = [
    { value: 1, label: 'Enero' },
    { value: 2, label: 'Febrero' },
    { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Mayo' },
    { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' },
    { value: 11, label: 'Noviembre' },
    { value: 12, label: 'Diciembre' },
  ];

  constructor() {
    for (let y = this.currentYear; y >= this.currentYear - 5; y--) {
      this.years.push(y);
    }
  }

  ngOnInit(): void {
    this.loadSummary();
  }

  loadSummary(): void {
    this.loading.set(true);
    this.error.set('');

    this.api
      .get<MonthlySummary>('/church/reports/monthly-summary', {
        year: this.selectedYear(),
        month: this.selectedMonth(),
      })
      .subscribe({
        next: (data) => {
          this.summary.set(data);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('Error al cargar el reporte.');
          this.summary.set(null);
          this.loading.set(false);
        },
      });
  }

  onPeriodChange(): void {
    this.loadSummary();
  }

  fmt(value: number | undefined | null): string {
    if (value == null) return '$0';
    return '$' + Number(value).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }

  exportCSV(): void {
    const s = this.summary();
    if (!s) return;
    const monthLabel = this.months.find(m => m.value === this.selectedMonth())?.label || '';
    const lines: string[] = [];
    lines.push(`Reporte Financiero - ${monthLabel} ${this.selectedYear()}`);
    lines.push('');
    lines.push('Concepto,Monto');
    lines.push(`Ingresos Totales,${s.total_income}`);
    lines.push(`Egresos Totales,${s.total_expenses}`);
    lines.push(`Balance Neto,${s.net}`);
    if (s.tithe_of_tithe) {
      lines.push('');
      lines.push('Diezmo del Diezmo');
      lines.push(`Total Diezmos,${s.tithe_of_tithe.total_tithes}`);
      lines.push(`Total Ofrendas,${s.tithe_of_tithe.total_offerings}`);
      lines.push(`Base,${s.tithe_of_tithe.base_amount}`);
      lines.push(`Diezmo del Diezmo (10%),${s.tithe_of_tithe.tithe_of_tithe}`);
    }

    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reporte_${this.selectedYear()}_${this.selectedMonth()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
