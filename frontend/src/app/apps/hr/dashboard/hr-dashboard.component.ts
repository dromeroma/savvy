import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrDepartment,
  HrEmployeeListItem,
  HrPosition,
} from '../../../core/models/hr.model';

@Component({
  selector: 'app-hr-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-6">
      <header>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">SavvyHR · Talento Humano</h1>
        <p class="text-sm text-slate-600 dark:text-slate-400">
          Empleados, contratos, departamentos y cargos. Fase 1 — núcleo organizacional.
        </p>
      </header>

      <!-- KPIs -->
      <section class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <a routerLink="/hr/employees" class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 hover:border-brand-400 transition">
          <p class="text-xs text-slate-500 dark:text-slate-400">Empleados activos</p>
          <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{{ activeCount() }}</p>
          <p class="text-[11px] text-slate-400 mt-1">de {{ employees().length }} totales</p>
        </a>
        <a routerLink="/hr/departments" class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 hover:border-brand-400 transition">
          <p class="text-xs text-slate-500 dark:text-slate-400">Departamentos</p>
          <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{{ departments().length }}</p>
        </a>
        <a routerLink="/hr/positions" class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 hover:border-brand-400 transition">
          <p class="text-xs text-slate-500 dark:text-slate-400">Cargos</p>
          <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{{ positions().length }}</p>
        </a>
        <div class="rounded-2xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
          <p class="text-xs text-amber-700 dark:text-amber-300">En licencia / suspendidos</p>
          <p class="text-2xl font-bold text-amber-800 dark:text-amber-200 mt-1">{{ onLeaveCount() }}</p>
        </div>
      </section>

      <!-- Distribución por departamento -->
      <section class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
        <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Distribución por departamento</h2>
        @if (byDepartment().length === 0) {
          <p class="text-xs text-slate-500 dark:text-slate-400">Aún no hay empleados activos.</p>
        } @else {
          <div class="space-y-2">
            @for (row of byDepartment(); track row.name) {
              <div>
                <div class="flex justify-between text-xs mb-1 text-slate-700 dark:text-slate-300">
                  <span>{{ row.name }}</span>
                  <span class="font-mono">{{ row.count }}</span>
                </div>
                <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div class="h-full bg-brand-500" [style.width.%]="row.pct"></div>
                </div>
              </div>
            }
          </div>
        }
      </section>

      <!-- Quick links -->
      <section class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <a routerLink="/hr/employees" class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-sm text-slate-700 dark:text-slate-300 hover:border-brand-400">
          → Empleados
        </a>
        <a routerLink="/hr/contracts" class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-sm text-slate-700 dark:text-slate-300 hover:border-brand-400">
          → Contratos
        </a>
        <a routerLink="/hr/departments" class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-sm text-slate-700 dark:text-slate-300 hover:border-brand-400">
          → Departamentos
        </a>
        <a routerLink="/hr/positions" class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-sm text-slate-700 dark:text-slate-300 hover:border-brand-400">
          → Cargos
        </a>
      </section>
    </div>
  `,
})
export class HrDashboardComponent implements OnInit {
  private readonly hr = inject(HrApiService);

  employees = signal<HrEmployeeListItem[]>([]);
  departments = signal<HrDepartment[]>([]);
  positions = signal<HrPosition[]>([]);

  activeCount = computed(() => this.employees().filter((e) => e.status === 'active').length);
  onLeaveCount = computed(
    () => this.employees().filter((e) => e.status === 'on_leave' || e.status === 'suspended').length,
  );

  byDepartment = computed(() => {
    const counts = new Map<string, number>();
    for (const e of this.employees()) {
      if (e.status !== 'active') continue;
      const key = e.department_name || 'Sin departamento';
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    const total = Array.from(counts.values()).reduce((a, b) => a + b, 0);
    return Array.from(counts.entries())
      .map(([name, count]) => ({ name, count, pct: total > 0 ? Math.round((count / total) * 100) : 0 }))
      .sort((a, b) => b.count - a.count);
  });

  ngOnInit(): void {
    this.hr.listEmployees().subscribe({ next: (r) => this.employees.set(r) });
    this.hr.listDepartments().subscribe({ next: (r) => this.departments.set(r) });
    this.hr.listPositions().subscribe({ next: (r) => this.positions.set(r) });
  }
}
