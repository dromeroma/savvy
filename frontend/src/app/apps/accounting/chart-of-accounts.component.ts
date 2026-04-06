import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

interface Account {
  id: string;
  code: string;
  name: string;
  type: string;
  is_active: boolean;
  is_system: boolean;
}

@Component({
  selector: 'app-chart-of-accounts',
  imports: [CommonModule],
  template: `
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Catálogo de Cuentas</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Plan contable de la organización</p>
        </div>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Código</th>
                <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Nombre</th>
                <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden sm:table-cell">Tipo</th>
                <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden md:table-cell">Estado</th>
              </tr>
            </thead>
            <tbody>
              @for (acct of accounts(); track acct.id) {
                <tr class="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                  <td class="px-6 py-4 font-mono text-gray-800 dark:text-white/90 font-medium">{{ acct.code }}</td>
                  <td class="px-6 py-4 text-gray-800 dark:text-white/90" [class.font-semibold]="acct.code.length <= 2" [class.pl-10]="acct.code.length > 3">{{ acct.name }}</td>
                  <td class="px-6 py-4 hidden sm:table-cell">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      [ngClass]="{
                        'bg-blue-light-50 text-blue-light-700 dark:bg-blue-light-500/20 dark:text-blue-light-400': acct.type === 'asset',
                        'bg-error-50 text-error-700 dark:bg-error-500/20 dark:text-error-400': acct.type === 'liability',
                        'bg-brand-50 text-brand-700 dark:bg-brand-500/20 dark:text-brand-400': acct.type === 'equity',
                        'bg-success-50 text-success-700 dark:bg-success-500/20 dark:text-success-400': acct.type === 'revenue',
                        'bg-warning-50 text-warning-700 dark:bg-warning-500/20 dark:text-warning-400': acct.type === 'expense'
                      }">{{ acct.type }}</span>
                  </td>
                  <td class="px-6 py-4 hidden md:table-cell">
                    @if (acct.is_active) {
                      <span class="w-2 h-2 rounded-full bg-success-500 inline-block"></span>
                    } @else {
                      <span class="w-2 h-2 rounded-full bg-gray-300 inline-block"></span>
                    }
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="4" class="px-6 py-12 text-center text-gray-400 dark:text-gray-500">
                    No hay cuentas registradas. Se crearán al activar una app.
                  </td>
                </tr>
              }
            </tbody>
          </table>
          </div>
        </div>
      }
    </div>
  `,
})
export class ChartOfAccountsComponent implements OnInit {
  private readonly api = inject(ApiService);
  accounts = signal<Account[]>([]);
  loading = signal(true);

  ngOnInit() {
    this.api.get<Account[]>('/accounting/chart-of-accounts').subscribe({
      next: (data) => { this.accounts.set(data); this.loading.set(false); },
      error: () => { this.accounts.set([]); this.loading.set(false); },
    });
  }
}
