import { Component } from '@angular/core';

@Component({
  selector: 'app-income-statement',
  imports: [],
  template: `
    <div>
      <h2 class="text-xl font-bold text-gray-800 dark:text-white/90 mb-2">Estado de Resultados</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Ingresos vs gastos del período</p>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 border-dashed p-12 text-center">
        <svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p class="text-gray-400 dark:text-gray-500 text-sm">Disponible cuando haya transacciones registradas.</p>
      </div>
    </div>
  `,
})
export class IncomeStatementComponent {}
