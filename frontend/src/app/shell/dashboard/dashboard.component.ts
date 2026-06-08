import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import {
  DashboardMetric,
  DashboardService,
  DashboardSummaryResponse,
} from '../../core/services/dashboard.service';
import {
  HeroMetricCardComponent,
  KpiCardComponent,
} from '../../shared/components/bento';
import { AiService, BriefingResponse } from '../../core/services/ai.service';

interface AppWithMetrics {
  code: string;
  name: string;
  description: string | null;
  color: string | null;
  status: string;
  user_role: string | null;
  metrics: DashboardMetric[];
}

interface DashboardError {
  message: string;
  status: number | null;
  detail: string | null;
}

@Component({
  selector: 'app-dashboard',
  imports: [
    CommonModule, DatePipe, RouterLink,
    HeroMetricCardComponent, KpiCardComponent,
  ],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly dashboard = inject(DashboardService);
  private readonly router = inject(Router);
  private readonly ai = inject(AiService);

  loading = signal(true);
  error = signal<DashboardError | null>(null);
  data = signal<DashboardSummaryResponse | null>(null);
  briefing = signal<BriefingResponse | null>(null);

  /** Serie histórica para el sparkline del HERO. Null hasta que el backend
   *  exponga datos de tendencia — preferimos no inventar números. */
  readonly incomeSeries = computed<number[] | null>(() => null);

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
    this.ai.briefing().subscribe({
      next: (b) => this.briefing.set(b),
      error: () => this.briefing.set(null),
    });
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.dashboard.getSummary().subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse | unknown) => {
        this.loading.set(false);
        const e = err as HttpErrorResponse;
        let detail: string | null = null;
        if (e?.error) {
          if (typeof e.error === 'string') {
            detail = e.error.slice(0, 300);
          } else if (typeof e.error === 'object' && 'detail' in e.error) {
            detail = String((e.error as { detail: unknown }).detail);
          }
        }
        let message = 'No se pudo cargar el resumen.';
        if (e?.status === 0) {
          message = 'No hay conexión con el backend. Verifica que el servidor esté corriendo.';
        } else if (e?.status === 401) {
          message = 'Sesión expirada o inválida. Vuelve a iniciar sesión.';
        } else if (e?.status === 403) {
          message = 'No tienes permiso para ver el resumen de esta organización.';
        } else if (e?.status && e.status >= 500) {
          message = 'El servidor falló al generar el resumen.';
        }
        this.error.set({
          message,
          status: e?.status ?? null,
          detail,
        });
      },
    });
  }

  openApp(code: string): void {
    this.router.navigate([`/${code}`]);
  }
}
