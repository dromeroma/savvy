import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import {
  DashboardMetric,
  DashboardService,
  DashboardSummaryResponse,
} from '../../core/services/dashboard.service';

interface AppWithMetrics {
  code: string;
  name: string;
  description: string | null;
  color: string | null;
  status: string;
  user_role: string | null;
  metrics: DashboardMetric[];
}

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, DatePipe, RouterLink],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly dashboard = inject(DashboardService);
  private readonly router = inject(Router);

  loading = signal(true);
  error = signal('');
  data = signal<DashboardSummaryResponse | null>(null);

  /** Apps merged with their headline metrics, ready to render as rich cards. */
  readonly appsWithMetrics = computed<AppWithMetrics[]>(() => {
    const d = this.data();
    if (!d) return [];
    const byApp = new Map<string, DashboardMetric[]>();
    for (const m of d.metrics) {
      if (!m.app_code) continue;
      if (!byApp.has(m.app_code)) byApp.set(m.app_code, []);
      byApp.get(m.app_code)!.push(m);
    }
    return d.active_apps.map((a) => ({
      code: a.code,
      name: a.name,
      description: a.description,
      color: a.color,
      status: a.status,
      user_role: a.user_role,
      metrics: byApp.get(a.code) ?? [],
    }));
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set('');
    this.dashboard.getSummary().subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail || 'No se pudo cargar el resumen.');
      },
    });
  }

  openApp(code: string): void {
    this.router.navigate([`/${code}`]);
  }
}
