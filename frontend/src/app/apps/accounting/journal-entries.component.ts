import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface JournalLine {
  id: string;
  account_id: string;
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  description?: string;
}

interface JournalEntry {
  id: string;
  entry_number: number;
  date: string;
  description: string;
  source_app: string;
  status: string;
  lines: JournalLine[];
}

@Component({
  selector: 'app-journal-entries',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Asientos Contables</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Registro de transacciones contables</p>
        </div>
      </div>

      <!-- Filter Bar -->
      <div class="flex flex-col sm:flex-row gap-3 mb-4">
        <select [(ngModel)]="filterApp" (ngModelChange)="applyFilter()"
          class="px-4 py-2.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white/90 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition">
          <option value="">Todas las apps</option>
          <option value="church">Church</option>
          <option value="pos">POS</option>
          <option value="manual">Manual</option>
        </select>
      </div>

      <!-- Loading -->
      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          @if (filteredEntries().length > 0) {
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 w-10"></th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">#</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Fecha</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Descripción</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden sm:table-cell">App</th>
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden md:table-cell">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  @for (entry of filteredEntries(); track entry.id) {
                    <!-- Entry Row -->
                    <tr class="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 transition cursor-pointer"
                      (click)="toggleEntry(entry.id)">
                      <td class="px-6 py-4">
                        <svg class="w-4 h-4 text-gray-400 transition-transform duration-200"
                          [class.rotate-90]="expandedEntries().has(entry.id)"
                          fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                        </svg>
                      </td>
                      <td class="px-6 py-4 font-mono text-gray-800 dark:text-white/90 font-medium">{{ entry.entry_number }}</td>
                      <td class="px-6 py-4 text-gray-600 dark:text-gray-300">{{ entry.date | date:'dd/MM/yyyy' }}</td>
                      <td class="px-6 py-4 text-gray-800 dark:text-white/90">{{ entry.description }}</td>
                      <td class="px-6 py-4 hidden sm:table-cell">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                          [ngClass]="getAppBadgeClasses(entry.source_app)">
                          {{ entry.source_app }}
                        </span>
                      </td>
                      <td class="px-6 py-4 hidden md:table-cell">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                          [ngClass]="getStatusBadgeClasses(entry.status)">
                          {{ getStatusLabel(entry.status) }}
                        </span>
                      </td>
                    </tr>

                    <!-- Expanded Lines -->
                    @if (expandedEntries().has(entry.id)) {
                      <tr>
                        <td colspan="6" class="px-0 py-0">
                          <div class="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                            <table class="w-full text-sm">
                              <thead>
                                <tr>
                                  <th class="text-left px-8 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Código</th>
                                  <th class="text-left px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Cuenta</th>
                                  <th class="text-right px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Débito</th>
                                  <th class="text-right px-8 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Crédito</th>
                                </tr>
                              </thead>
                              <tbody>
                                @for (line of entry.lines; track line.id) {
                                  <tr class="border-t border-gray-200/50 dark:border-gray-700/50">
                                    <td class="px-8 py-2 font-mono text-xs text-gray-600 dark:text-gray-400">{{ line.account_code }}</td>
                                    <td class="px-4 py-2 text-gray-700 dark:text-gray-300">{{ line.account_name }}</td>
                                    <td class="px-4 py-2 text-right font-mono" [class]="line.debit > 0 ? 'text-blue-600 dark:text-blue-400' : 'text-gray-300 dark:text-gray-600'">
                                      {{ line.debit | number:'1.2-2' }}
                                    </td>
                                    <td class="px-8 py-2 text-right font-mono" [class]="line.credit > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-300 dark:text-gray-600'">
                                      {{ line.credit | number:'1.2-2' }}
                                    </td>
                                  </tr>
                                }
                                <!-- Totals row -->
                                <tr class="border-t-2 border-gray-300 dark:border-gray-600">
                                  <td class="px-8 py-2"></td>
                                  <td class="px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Total</td>
                                  <td class="px-4 py-2 text-right font-mono font-semibold text-blue-700 dark:text-blue-400">
                                    {{ getEntryTotalDebit(entry) | number:'1.2-2' }}
                                  </td>
                                  <td class="px-8 py-2 text-right font-mono font-semibold text-red-700 dark:text-red-400">
                                    {{ getEntryTotalCredit(entry) | number:'1.2-2' }}
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </td>
                      </tr>
                    }
                  }
                </tbody>
              </table>
            </div>
          } @else {
            <div class="px-6 py-12 text-center">
              <svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              <p class="text-gray-400 dark:text-gray-500 text-sm">Los asientos se generan automáticamente al registrar ingresos y gastos.</p>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class JournalEntriesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  entries = signal<JournalEntry[]>([]);
  filteredEntries = signal<JournalEntry[]>([]);
  loading = signal(true);
  expandedEntries = signal<Set<string>>(new Set());

  filterApp = '';

  ngOnInit(): void {
    this.loadEntries();
  }

  loadEntries(): void {
    this.loading.set(true);
    this.api.get<JournalEntry[]>('/accounting/journal-entries').subscribe({
      next: (data) => {
        // Parse debit/credit from strings to numbers
        for (const entry of data) {
          if (entry.lines) {
            for (const line of entry.lines) {
              line.debit = Number(line.debit) || 0;
              line.credit = Number(line.credit) || 0;
            }
          }
        }
        this.entries.set(data);
        this.applyFilter();
        this.loading.set(false);
      },
      error: () => {
        this.entries.set([]);
        this.filteredEntries.set([]);
        this.loading.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudieron cargar los asientos contables' });
      },
    });
  }

  applyFilter(): void {
    const app = this.filterApp;
    if (!app) {
      this.filteredEntries.set(this.entries());
    } else {
      this.filteredEntries.set(this.entries().filter(e => e.source_app === app));
    }
  }

  toggleEntry(id: string): void {
    const current = new Set(this.expandedEntries());
    if (current.has(id)) {
      current.delete(id);
    } else {
      current.add(id);
    }
    this.expandedEntries.set(current);
  }

  getEntryTotalDebit(entry: JournalEntry): number {
    return entry.lines?.reduce((sum, l) => sum + (l.debit || 0), 0) ?? 0;
  }

  getEntryTotalCredit(entry: JournalEntry): number {
    return entry.lines?.reduce((sum, l) => sum + (l.credit || 0), 0) ?? 0;
  }

  getAppBadgeClasses(app: string): string {
    switch (app) {
      case 'church': return 'bg-purple-50 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400';
      case 'pos': return 'bg-blue-50 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400';
      case 'manual': return 'bg-gray-100 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400';
    }
  }

  getStatusBadgeClasses(status: string): string {
    switch (status) {
      case 'posted': return 'bg-green-50 text-green-700 dark:bg-green-500/20 dark:text-green-400';
      case 'draft': return 'bg-yellow-50 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400';
      case 'voided': return 'bg-red-50 text-red-700 dark:bg-red-500/20 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'posted': return 'Publicado';
      case 'draft': return 'Borrador';
      case 'voided': return 'Anulado';
      default: return status;
    }
  }

  trackById(_: number, entry: JournalEntry): string {
    return entry.id;
  }
}
