import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ZoneOverviewService,
  ZoneOverviewResponse,
} from '../../../core/services/zone-overview.service';

@Component({
  selector: 'app-zone-overview',
  imports: [CommonModule, FormsModule, DecimalPipe],
  templateUrl: './zone-overview.component.html',
})
export class ZoneOverviewComponent implements OnInit {
  private readonly zoneService = inject(ZoneOverviewService);

  loading = signal(true);
  data = signal<ZoneOverviewResponse | null>(null);
  error = signal<string | null>(null);
  selectedZoneId = signal<string>('');

  // Aggregate "zone totals" computed across all churches.
  readonly totals = computed(() => {
    const churches = this.data()?.churches ?? [];
    return churches.reduce(
      (acc, c) => ({
        active: acc.active + c.metrics.active_congregants,
        visitors: acc.visitors + c.metrics.visitors_last_30d,
        events: acc.events + c.metrics.events_last_30d,
        income: acc.income + Number(c.metrics.income_this_month || 0),
      }),
      { active: 0, visitors: 0, events: 0, income: 0 },
    );
  });

  ngOnInit(): void {
    this.fetch();
  }

  fetch(zoneId?: string): void {
    this.loading.set(true);
    this.error.set(null);
    this.zoneService.getOverview(zoneId).subscribe({
      next: (res) => {
        this.data.set(res);
        this.selectedZoneId.set(res.selected_zone?.id ?? '');
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        const detail = err?.error?.detail;
        const status = err?.status;
        if (status === 403) {
          this.error.set(
            detail ||
              'Esta vista es solo para presbíteros y líderes de zona.',
          );
        } else {
          this.error.set(
            typeof detail === 'string' ? detail : 'No se pudo cargar la zona.',
          );
        }
      },
    });
  }

  onZoneChange(zoneId: string): void {
    this.selectedZoneId.set(zoneId);
    this.fetch(zoneId);
  }
}
