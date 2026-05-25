import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { WaterExtrasService } from '../../../core/services/water-extras.service';
import {
  MonthlyPoint,
  WaterAnalyticsResponse,
} from '../../../core/models/water-phase6.model';

@Component({
  selector: 'app-water-analytics',
  imports: [CommonModule, DecimalPipe],
  templateUrl: './analytics.component.html',
})
export class WaterAnalyticsComponent implements OnInit {
  private readonly extras = inject(WaterExtrasService);

  loading = signal(true);
  data = signal<WaterAnalyticsResponse | null>(null);

  readonly billedMax = computed(() =>
    Math.max(...(this.data()?.billed_trend ?? []).map((p) => +p.amount), 1),
  );
  readonly collectedMax = computed(() =>
    Math.max(...(this.data()?.collected_trend ?? []).map((p) => +p.amount), 1),
  );
  readonly consMax = computed(() =>
    Math.max(...(this.data()?.consumption_trend ?? []).map((p) => +p.amount), 1),
  );

  ngOnInit(): void {
    this.extras.analyticsOverview().subscribe({
      next: (d) => {
        this.data.set(d);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  pct(p: MonthlyPoint, max: number): number {
    if (max <= 0) return 0;
    return Math.min(100, (+p.amount / max) * 100);
  }

  /** "2026-05" → "May" (short Spanish month label). */
  shortMonth(yyyymm: string): string {
    const m = parseInt(yyyymm.slice(5, 7), 10);
    return ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][m - 1] ?? '';
  }
}
