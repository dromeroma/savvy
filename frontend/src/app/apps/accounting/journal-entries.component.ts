import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';
import { DatePickerComponent } from '../../shared/components/form/date-picker/date-picker.component';

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

interface AccountOption {
  id: string;
  code: string;
  name: string;
  type: string;
}

interface NewLine {
  account_code: string;
  debit: number | null;
  credit: number | null;
}

@Component({
  selector: 'app-journal-entries',
  imports: [CommonModule, FormsModule, DatePickerComponent],
  template: `
    <div>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Asientos Contables</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Registro de transacciones contables</p>
        </div>
        <button (click)="openCreateModal()"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg
            bg-brand-600 text-white hover:bg-brand-700
            dark:bg-brand-500 dark:hover:bg-brand-600 transition shadow-theme-xs">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Nuevo Asiento
        </button>
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
                    <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Descripcion</th>
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
                                  <th class="text-left px-8 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Codigo</th>
                                  <th class="text-left px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Cuenta</th>
                                  <th class="text-right px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Debito</th>
                                  <th class="text-right px-8 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Credito</th>
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
              <p class="text-gray-400 dark:text-gray-500 text-sm">Los asientos se generan automaticamente al registrar ingresos y gastos.</p>
            </div>
          }
        </div>
      }

      <!-- Create Journal Entry Modal -->
      @if (showCreateModal()) {
        <div class="fixed inset-0 z-9999 flex items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50 dark:bg-black/70"></div>
          <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <!-- Modal Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nuevo Asiento Contable</h3>
              <button (click)="closeCreateModal()"
                class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6 space-y-5">
              <!-- Date & Description -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-1.5">
                  <app-date-picker
                    id="entry_date"
                    label="Fecha"
                    [defaultDate]="newEntry.date"
                    (dateChange)="newEntry.date = $event"
                  />
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Descripcion</label>
                  <input type="text" [(ngModel)]="newEntry.description" placeholder="Descripcion del asiento"
                    class="h-11 px-4 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-theme-xs text-gray-800 dark:text-white/90 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
                </div>
              </div>

              <!-- Lines Table -->
              <div>
                <div class="flex items-center justify-between mb-3">
                  <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Lineas del asiento</label>
                  <button (click)="addLine()"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg
                      bg-brand-50 text-brand-700 hover:bg-brand-100
                      dark:bg-brand-500/20 dark:text-brand-400 dark:hover:bg-brand-500/30
                      transition">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    Agregar linea
                  </button>
                </div>

                <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                        <th class="text-left px-4 py-2.5 font-medium text-gray-600 dark:text-gray-400 text-xs uppercase">Cuenta</th>
                        <th class="text-right px-4 py-2.5 font-medium text-gray-600 dark:text-gray-400 text-xs uppercase w-36">Debito</th>
                        <th class="text-right px-4 py-2.5 font-medium text-gray-600 dark:text-gray-400 text-xs uppercase w-36">Credito</th>
                        <th class="w-12"></th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (line of newEntry.lines; track $index; let i = $index) {
                        <tr class="border-b border-gray-100 dark:border-gray-700/50">
                          <td class="px-4 py-2">
                            <select [(ngModel)]="line.account_code"
                              class="w-full h-9 px-3 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white/90 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition">
                              <option value="">Seleccionar cuenta...</option>
                              @for (acc of accounts(); track acc.code) {
                                <option [value]="acc.code">{{ acc.code }} - {{ acc.name }}</option>
                              }
                            </select>
                          </td>
                          <td class="px-4 py-2">
                            <input type="number" [(ngModel)]="line.debit" placeholder="0.00" min="0" step="0.01"
                              class="w-full h-9 px-3 text-sm text-right font-mono bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white/90 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
                          </td>
                          <td class="px-4 py-2">
                            <input type="number" [(ngModel)]="line.credit" placeholder="0.00" min="0" step="0.01"
                              class="w-full h-9 px-3 text-sm text-right font-mono bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white/90 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition" />
                          </td>
                          <td class="px-2 py-2 text-center">
                            @if (newEntry.lines.length > 2) {
                              <button (click)="removeLine(i)"
                                class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                              </button>
                            }
                          </td>
                        </tr>
                      }
                      <!-- Totals -->
                      <tr class="bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
                        <td class="px-4 py-2.5 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Totales</td>
                        <td class="px-4 py-2.5 text-right font-mono text-sm font-semibold text-blue-700 dark:text-blue-400">
                          {{ getTotalDebit() | number:'1.2-2' }}
                        </td>
                        <td class="px-4 py-2.5 text-right font-mono text-sm font-semibold text-red-700 dark:text-red-400">
                          {{ getTotalCredit() | number:'1.2-2' }}
                        </td>
                        <td></td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <!-- Balance Warning -->
                @if (!isBalanced()) {
                  <div class="flex items-center gap-2 mt-2 px-2 text-sm text-amber-600 dark:text-amber-400">
                    <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                    </svg>
                    La suma de debitos ({{ getTotalDebit() | number:'1.2-2' }}) no es igual a la suma de creditos ({{ getTotalCredit() | number:'1.2-2' }})
                  </div>
                }
              </div>
            </div>

            <!-- Modal Footer -->
            <div class="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
              <button (click)="closeCreateModal()"
                class="px-4 py-2.5 text-sm font-medium rounded-lg border border-gray-200 dark:border-gray-600
                  text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                Cancelar
              </button>
              <button (click)="saveEntry()" [disabled]="saving() || !isBalanced()"
                class="px-5 py-2.5 text-sm font-medium rounded-lg
                  bg-brand-600 text-white hover:bg-brand-700
                  dark:bg-brand-500 dark:hover:bg-brand-600
                  transition disabled:opacity-50 disabled:cursor-not-allowed shadow-theme-xs">
                @if (saving()) {
                  <div class="flex items-center gap-2">
                    <div class="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>
                    Guardando...
                  </div>
                } @else {
                  Guardar asiento
                }
              </button>
            </div>
          </div>
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

  // Modal state
  showCreateModal = signal(false);
  saving = signal(false);
  accounts = signal<AccountOption[]>([]);

  newEntry = {
    date: '',
    description: '',
    lines: [] as NewLine[],
  };

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

  // --- Create Modal ---

  openCreateModal(): void {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');

    this.newEntry = {
      date: `${y}-${m}-${d}`,
      description: '',
      lines: [
        { account_code: '', debit: null, credit: null },
        { account_code: '', debit: null, credit: null },
      ],
    };
    this.loadAccounts();
    this.showCreateModal.set(true);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
  }

  loadAccounts(): void {
    this.api.get<AccountOption[]>('/accounting/chart-of-accounts').subscribe({
      next: (data) => this.accounts.set(data),
      error: () => this.accounts.set([]),
    });
  }

  addLine(): void {
    this.newEntry.lines = [...this.newEntry.lines, { account_code: '', debit: null, credit: null }];
  }

  removeLine(index: number): void {
    if (this.newEntry.lines.length <= 2) return;
    this.newEntry.lines = this.newEntry.lines.filter((_, i) => i !== index);
  }

  getTotalDebit(): number {
    return this.newEntry.lines.reduce((sum, l) => sum + (Number(l.debit) || 0), 0);
  }

  getTotalCredit(): number {
    return this.newEntry.lines.reduce((sum, l) => sum + (Number(l.credit) || 0), 0);
  }

  isBalanced(): boolean {
    const totalD = this.getTotalDebit();
    const totalC = this.getTotalCredit();
    if (totalD === 0 && totalC === 0) return false;
    return Math.abs(totalD - totalC) < 0.01;
  }

  saveEntry(): void {
    if (!this.newEntry.date) {
      this.notify.show({ type: 'warning', title: 'Fecha requerida', message: 'Seleccione una fecha para el asiento' });
      return;
    }
    if (!this.newEntry.description.trim()) {
      this.notify.show({ type: 'warning', title: 'Descripcion requerida', message: 'Ingrese una descripcion para el asiento' });
      return;
    }

    const validLines = this.newEntry.lines.filter(l => l.account_code && ((Number(l.debit) || 0) > 0 || (Number(l.credit) || 0) > 0));
    if (validLines.length < 2) {
      this.notify.show({ type: 'warning', title: 'Lineas insuficientes', message: 'Se necesitan al menos 2 lineas con cuenta y monto' });
      return;
    }

    if (!this.isBalanced()) {
      this.notify.show({ type: 'warning', title: 'Descuadre', message: 'La suma de debitos debe ser igual a la suma de creditos' });
      return;
    }

    this.saving.set(true);
    const payload = {
      date: this.newEntry.date,
      description: this.newEntry.description.trim(),
      lines: validLines.map(l => ({
        account_code: l.account_code,
        debit: Number(l.debit) || 0,
        credit: Number(l.credit) || 0,
      })),
    };

    this.api.post<JournalEntry>('/accounting/journal-entries', payload).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Asiento creado', message: 'El asiento contable se registro exitosamente' });
        this.saving.set(false);
        this.closeCreateModal();
        this.loadEntries();
      },
      error: (err) => {
        const msg = err?.error?.detail || 'No se pudo crear el asiento contable';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
        this.saving.set(false);
      },
    });
  }
}
