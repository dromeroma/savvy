import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrDepartment,
  HrEmployeeListItem,
  HrEvaluationCycle,
  HrLeave,
  HrPosition,
  HrTrainingEnrollment,
  HrVacationRequest,
} from '../../../core/models/hr.model';
import {
  BarChartComponent,
  BarRow,
  ChartCardComponent,
  DonutChartComponent,
  DonutSlice,
  HeroMetricCardComponent,
  KpiCardComponent,
} from '../../../shared/components/bento';

@Component({
  selector: 'app-hr-dashboard',
  imports: [
    CommonModule, RouterLink,
    HeroMetricCardComponent, KpiCardComponent, ChartCardComponent,
    DonutChartComponent, BarChartComponent,
  ],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-7">
      <header class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2">
        <div>
          <p class="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-medium">
            SavvyHR · Talento Humano
          </p>
          <h1 class="text-3xl font-bold text-slate-900 dark:text-white mt-1">
            Resumen ejecutivo
          </h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Headcount, ausentismo, evaluaciones y capacitaciones.
          </p>
        </div>
        <div class="text-right">
          <div class="text-[11px] uppercase tracking-wider text-slate-400">Última actualización</div>
          <div class="text-xs text-slate-600 dark:text-slate-300 tabular-nums">{{ now }}</div>
        </div>
      </header>

      <!-- ============== BENTO superior: HERO + 4 KPIs ============== -->
      <section class="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
        <!-- HERO: Headcount activo -->
        <div class="lg:col-span-7 lg:row-span-2">
          <app-hero-metric-card
            label="Empleados activos"
            [value]="activeCount()"
            tone="violet"
            icon="👥"
            [subtitle]="totalLabel()"
            [hint]="onLeaveCount() > 0 ? onLeaveCount() + ' en licencia o suspendidos' : 'sin ausencias'"
            link="/hr/employees" />
        </div>

        <div class="lg:col-span-5 grid grid-cols-2 gap-4">
          <app-kpi-card
            label="Departamentos"
            [value]="departments().length"
            hint="unidades organizacionales"
            tone="info"
            link="/hr/departments" />

          <app-kpi-card
            label="Cargos"
            [value]="positions().length"
            hint="posiciones definidas"
            tone="default"
            link="/hr/positions" />

          <app-kpi-card
            label="Vacaciones pendientes"
            [value]="pendingVacations()"
            hint="de aprobar"
            [tone]="pendingVacations() > 0 ? 'warn' : 'default'"
            link="/hr/vacations" />

          <app-kpi-card
            label="Incapacidades activas"
            [value]="activeLeaves()"
            hint="vigentes"
            [tone]="activeLeaves() > 0 ? 'info' : 'default'"
            link="/hr/leaves" />
        </div>
      </section>

      <!-- ============== BENTO de capas: charts ============== -->
      <section class="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
        <!-- Distribución por departamento -->
        <div class="lg:col-span-7">
          <app-chart-card title="Distribución por departamento"
            subtitle="empleados activos por unidad"
            [action]="{ label: 'Ver detalle', link: '/hr/departments' }">
            <app-bar-chart [data]="byDepartment()" tone="violet" />
          </app-chart-card>
        </div>

        <!-- Donut: estado de evaluaciones -->
        <div class="lg:col-span-5">
          <app-chart-card title="Evaluaciones de desempeño"
            [subtitle]="evaluationCyclesActive() + ' ciclo(s) abierto(s)'"
            [action]="{ label: 'Ver evaluaciones', link: '/hr/evaluations' }">
            @if (evaluationStatus().length > 0) {
              <app-donut-chart [data]="evaluationStatus()" totalLabel="evaluaciones en curso" />
            } @else {
              <div class="text-center py-8">
                <p class="text-xs text-slate-400 dark:text-slate-500">
                  Sin ciclos abiertos. <a routerLink="/hr/evaluations" class="text-brand-600 hover:underline">Iniciar uno</a>.
                </p>
              </div>
            }
          </app-chart-card>
        </div>

        <!-- Donut: vacaciones por estado -->
        <div class="lg:col-span-5">
          <app-chart-card title="Vacaciones por estado"
            subtitle="último periodo"
            [action]="{ label: 'Gestionar', link: '/hr/vacations' }">
            <app-donut-chart [data]="vacationStatus()" totalLabel="solicitudes" />
          </app-chart-card>
        </div>

        <!-- Capacitaciones -->
        <div class="lg:col-span-7">
          <app-chart-card title="Capacitaciones — progreso"
            [subtitle]="trainingsTotal() + ' inscripciones'"
            [action]="{ label: 'Ver cursos', link: '/hr/training' }">
            <app-bar-chart [data]="trainingProgress()" tone="emerald" />
          </app-chart-card>
        </div>
      </section>

      <!-- ============== Acciones rápidas ============== -->
      <section>
        <h2 class="text-base font-semibold text-slate-900 dark:text-white mb-3">Atajos</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          @for (link of quickLinks; track link.route) {
            <a [routerLink]="link.route"
              class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 hover:ring-2 hover:ring-brand-300 dark:hover:ring-brand-700 transition group">
              <div class="text-2xl mb-1">{{ link.icon }}</div>
              <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ link.label }}</div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{{ link.hint }}</div>
            </a>
          }
        </div>
      </section>
    </div>
  `,
})
export class HrDashboardComponent implements OnInit {
  private readonly hr = inject(HrApiService);

  employees = signal<HrEmployeeListItem[]>([]);
  departments = signal<HrDepartment[]>([]);
  positions = signal<HrPosition[]>([]);
  vacations = signal<HrVacationRequest[]>([]);
  leaves = signal<HrLeave[]>([]);
  evaluationCycles = signal<HrEvaluationCycle[]>([]);
  trainings = signal<HrTrainingEnrollment[]>([]);

  readonly now = new Date().toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

  readonly quickLinks = [
    { route: '/hr/employees', icon: '👤', label: 'Empleados', hint: 'lista y detalle' },
    { route: '/hr/payroll/periods', icon: '💵', label: 'Nómina', hint: 'períodos · desprendibles' },
    { route: '/hr/liquidations', icon: '🧾', label: 'Liquidaciones', hint: 'cese de contrato' },
    { route: '/hr/reports', icon: '📊', label: 'Reportes', hint: 'antigüedad · costo · ausentismo' },
  ];

  activeCount = computed(() => this.employees().filter((e) => e.status === 'active').length);
  onLeaveCount = computed(
    () => this.employees().filter((e) => e.status === 'on_leave' || e.status === 'suspended').length,
  );
  pendingVacations = computed(() => this.vacations().filter((v) => v.status === 'pending').length);
  activeLeaves = computed(() => this.leaves().filter((l) => l.status === 'active').length);
  evaluationCyclesActive = computed(() => this.evaluationCycles().filter((c) => c.status === 'open').length);
  trainingsTotal = computed(() => this.trainings().length);

  totalLabel = computed(() => {
    const total = this.employees().length;
    if (total === 0) return 'sin empleados todavía';
    return `de ${total} ${total === 1 ? 'registrado' : 'registrados'}`;
  });

  byDepartment = computed<BarRow[]>(() => {
    const counts = new Map<string, number>();
    for (const e of this.employees()) {
      if (e.status !== 'active') continue;
      const key = e.department_name || 'Sin departamento';
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  });

  evaluationStatus = computed<DonutSlice[]>(() => {
    // No tenemos lista de evaluaciones a este nivel — usamos los ciclos como proxy.
    const cycles = this.evaluationCycles();
    if (cycles.length === 0) return [];
    const buckets = { open: 0, closed: 0, draft: 0 };
    for (const c of cycles) {
      if (c.status === 'open') buckets.open++;
      else if (c.status === 'closed') buckets.closed++;
      else if (c.status === 'draft') buckets.draft++;
    }
    const out: DonutSlice[] = [];
    if (buckets.open > 0) out.push({ label: 'Abiertos', value: buckets.open, color: '#6366f1' });
    if (buckets.draft > 0) out.push({ label: 'Borrador', value: buckets.draft, color: '#94a3b8' });
    if (buckets.closed > 0) out.push({ label: 'Cerrados', value: buckets.closed, color: '#10b981' });
    return out;
  });

  vacationStatus = computed<DonutSlice[]>(() => {
    const counts = { pending: 0, approved: 0, rejected: 0, cancelled: 0, completed: 0 };
    for (const v of this.vacations()) {
      if (v.status in counts) counts[v.status as keyof typeof counts]++;
    }
    return [
      { label: 'Pendientes', value: counts.pending, color: '#f59e0b' },
      { label: 'Aprobadas', value: counts.approved, color: '#10b981' },
      { label: 'Completadas', value: counts.completed, color: '#06b6d4' },
      { label: 'Rechazadas', value: counts.rejected, color: '#ef4444' },
      { label: 'Canceladas', value: counts.cancelled, color: '#94a3b8' },
    ].filter((s) => s.value > 0);
  });

  trainingProgress = computed<BarRow[]>(() => {
    const counts = { enrolled: 0, in_progress: 0, completed: 0, failed: 0, cancelled: 0 };
    for (const t of this.trainings()) {
      if (t.completion_status in counts) counts[t.completion_status as keyof typeof counts]++;
    }
    const labels: Record<string, string> = {
      enrolled: 'Inscritas',
      in_progress: 'En curso',
      completed: 'Completadas',
      failed: 'No aprobadas',
      cancelled: 'Canceladas',
    };
    return Object.entries(counts)
      .filter(([, v]) => v > 0)
      .map(([key, value]) => ({ label: labels[key], value }))
      .sort((a, b) => b.value - a.value);
  });

  ngOnInit(): void {
    this.hr.listEmployees().subscribe({ next: (r) => this.employees.set(r) });
    this.hr.listDepartments().subscribe({ next: (r) => this.departments.set(r) });
    this.hr.listPositions().subscribe({ next: (r) => this.positions.set(r) });
    this.hr.listVacationRequests().subscribe({ next: (r) => this.vacations.set(r) });
    this.hr.listLeaves().subscribe({ next: (r) => this.leaves.set(r) });
    this.hr.listEvaluationCycles().subscribe({ next: (r) => this.evaluationCycles.set(r) });
    this.hr.listTrainingEnrollments().subscribe({ next: (r) => this.trainings.set(r) });
  }
}
