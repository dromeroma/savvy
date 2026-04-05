import { Component } from '@angular/core';

@Component({
  selector: 'app-journal-entries',
  imports: [],
  template: `
    <div>
      <h2 class="text-xl font-bold text-gray-800 dark:text-white/90 mb-2">Asientos Contables</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Registro de transacciones contables</p>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 border-dashed p-12 text-center">
        <svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-gray-400 dark:text-gray-500 text-sm">Los asientos se generan automáticamente al registrar ingresos y gastos.</p>
      </div>
    </div>
  `,
})
export class JournalEntriesComponent {}
