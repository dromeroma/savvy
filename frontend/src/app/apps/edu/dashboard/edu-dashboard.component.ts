import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-edu-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Dashboard Educativo</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Resumen general de la institución</p>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Estudiantes Activos</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ kpis().students }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Docentes Activos</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{{ kpis().teachers }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Programas</p>
          <p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">{{ kpis().programs }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Cursos / Materias</p>
          <p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{{ kpis().courses }}</p>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones rápidas</h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          @for (action of quickActions; track action.label) {
            <a [routerLink]="action.route"
              class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center">
              <span class="text-2xl">{{ action.icon }}</span>
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ action.label }}</span>
            </a>
          }
        </div>
      </div>
    </div>
  `,
})
export class EduDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  kpis = signal({ students: 0, teachers: 0, programs: 0, courses: 0 });

  readonly quickActions = [
    { label: 'Configuración', route: '/edu/config', icon: '⚙️' },
    { label: 'Programas', route: '/edu/programs', icon: '🎓' },
    { label: 'Cursos', route: '/edu/courses', icon: '📚' },
    { label: 'Estudiantes', route: '/edu/students', icon: '👨‍🎓' },
    { label: 'Docentes', route: '/edu/teachers', icon: '👩‍🏫' },
  ];

  ngOnInit(): void {
    this.loadKpis();
  }

  private loadKpis(): void {
    this.api.get<any>('/edu/students', { page_size: 1 }).subscribe({
      next: (r) => this.kpis.update((k) => ({ ...k, students: r.total || 0 })),
    });
    this.api.get<any>('/edu/teachers', { page_size: 1 }).subscribe({
      next: (r) => this.kpis.update((k) => ({ ...k, teachers: r.total || 0 })),
    });
    this.api.get<any[]>('/edu/structure/programs').subscribe({
      next: (r) => this.kpis.update((k) => ({ ...k, programs: r.length || 0 })),
    });
    this.api.get<any>('/edu/structure/courses', { page_size: 1 }).subscribe({
      next: (r) => this.kpis.update((k) => ({ ...k, courses: r.total || 0 })),
    });
  }
}
