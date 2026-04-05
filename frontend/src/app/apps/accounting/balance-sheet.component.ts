import { Component } from '@angular/core';

@Component({
  selector: 'app-balance-sheet',
  imports: [],
  template: `
    <div>
      <h2 class="text-xl font-bold text-gray-800 dark:text-white/90 mb-2">Balance General</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Activos, pasivos y patrimonio</p>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 border-dashed p-12 text-center">
        <svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
        </svg>
        <p class="text-gray-400 dark:text-gray-500 text-sm">Disponible cuando haya transacciones registradas.</p>
      </div>
    </div>
  `,
})
export class BalanceSheetComponent {}
