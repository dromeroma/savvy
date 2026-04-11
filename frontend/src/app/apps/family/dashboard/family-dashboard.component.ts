import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-family-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div>
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">SavvyFamily</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">Familiograma, árbol genealógico y diagnóstico familiar</p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Familias Registradas</p>
          <p class="text-2xl font-bold text-pink-600 dark:text-pink-400 mt-1">{{ totalFamilies() }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Miembros Totales</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ totalMembers() }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400">Anotaciones Activas</p>
          <p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">{{ totalAnnotations() }}</p>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Acciones rápidas</h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <a routerLink="/family/list"
            class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center">
            <span class="text-2xl">👨‍👩‍👧‍👦</span>
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">Ver Familias</span>
          </a>
          <a routerLink="/family/list"
            class="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition text-center">
            <span class="text-2xl">🌳</span>
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">Crear Familiograma</span>
          </a>
        </div>
      </div>
    </div>
  `,
})
export class FamilyDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  totalFamilies = signal(0);
  totalMembers = signal(0);
  totalAnnotations = signal(0);

  ngOnInit(): void {
    this.api.get<any[]>('/family/units').subscribe({
      next: (r) => this.totalFamilies.set(r.length),
    });
  }
}
