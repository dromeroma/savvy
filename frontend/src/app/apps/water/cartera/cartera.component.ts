import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { WaterService } from '../../../core/services/water.service';
import {
  CarteraAgingReport,
  CarteraOverdueSubscriber,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-cartera',
  imports: [CommonModule, DecimalPipe],
  templateUrl: './cartera.component.html',
})
export class CarteraComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  recalcLoading = signal(false);
  aging = signal<CarteraAgingReport | null>(null);
  overdue = signal<CarteraOverdueSubscriber[]>([]);

  readonly bucketLabels: Record<string, string> = {
    current: 'Al día (vigente)',
    '0_30': '1-30 días',
    '31_60': '31-60 días',
    '61_90': '61-90 días',
    '90_plus': 'Más de 90 días',
  };

  readonly bucketColors: Record<string, string> = {
    current: 'bg-emerald-500',
    '0_30': 'bg-amber-400',
    '31_60': 'bg-orange-500',
    '61_90': 'bg-red-500',
    '90_plus': 'bg-red-800',
  };

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.water.carteraAging().subscribe({
      next: (r) => this.aging.set(r),
      error: () => {},
    });
    this.water.carteraOverdue(100).subscribe({
      next: (r) => {
        this.overdue.set(r);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  runRecalc(): void {
    if (this.recalcLoading()) return;
    this.recalcLoading.set(true);
    this.water.recalcCartera().subscribe({
      next: (res) => {
        this.recalcLoading.set(false);
        this.notify.show({
          type: 'success',
          title: 'Cartera actualizada',
          message: `${res.invoices_marked_overdue} marcadas vencidas, ${res.invoices_with_interest_applied} con interés aplicado.`,
        });
        this.load();
      },
      error: (err) => {
        this.recalcLoading.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo recalcular.',
        });
      },
    });
  }

  /** Percentage of a bucket relative to total balance — for the bar widths. */
  pct(bucket: string): number {
    const a = this.aging();
    if (!a) return 0;
    const total = parseFloat(a.total_balance);
    if (total <= 0) return 0;
    const bal = parseFloat(a.buckets.find((b) => b.bucket === bucket)?.balance || '0');
    return (bal / total) * 100;
  }

  daysBadge(d: number): string {
    if (d <= 30) return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
    if (d <= 60) return 'bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300';
    if (d <= 90) return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
    return 'bg-red-200 text-red-800 dark:bg-red-700/40 dark:text-red-200';
  }
}
