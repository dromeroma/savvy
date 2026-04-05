import { Component } from '@angular/core';

@Component({
  selector: 'app-fiscal-periods',
  imports: [],
  template: `
    <div>
      <h2 class="text-xl font-bold text-gray-800 dark:text-white/90 mb-2">Períodos Fiscales</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Gestión de períodos contables mensuales</p>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 border-dashed p-12 text-center">
        <svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p class="text-gray-400 dark:text-gray-500 text-sm">Los períodos se crean automáticamente al registrar transacciones.</p>
      </div>
    </div>
  `,
})
export class FiscalPeriodsComponent {}
