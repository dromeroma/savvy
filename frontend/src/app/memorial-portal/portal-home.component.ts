import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { Router } from '@angular/router';
import {
  MemorialPortalService,
  PortalContract,
  PortalInvoice,
  PortalPayment,
  PortalServiceItem,
} from './portal.service';

type Tab = 'contract' | 'invoices' | 'payments' | 'services';

@Component({
  selector: 'app-memorial-portal-home',
  imports: [CommonModule, DatePipe, DecimalPipe],
  template: `
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950">
      <!-- Top bar -->
      <header class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div class="max-w-5xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <p class="text-xs text-slate-500 dark:text-slate-400">{{ contract()?.organization_name }}</p>
            <h1 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Portal del afiliado</h1>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm text-slate-700 dark:text-slate-300">{{ titularName() }}</span>
            <button (click)="logout()" type="button"
              class="text-xs text-rose-600 hover:underline">Cerrar sesión</button>
          </div>
        </div>
      </header>

      <!-- Tabs -->
      <nav class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div class="max-w-5xl mx-auto px-4 flex gap-1 overflow-x-auto">
          @for (t of tabs; track t.value) {
            <button type="button" (click)="setTab(t.value)"
              class="px-4 py-3 text-sm border-b-2 whitespace-nowrap"
              [class.border-brand-600]="tab() === t.value"
              [class.text-brand-700]="tab() === t.value"
              [class.dark:text-brand-300]="tab() === t.value"
              [class.border-transparent]="tab() !== t.value"
              [class.text-slate-600]="tab() !== t.value"
              [class.dark:text-slate-400]="tab() !== t.value">
              {{ t.label }}
            </button>
          }
        </div>
      </nav>

      <main class="max-w-5xl mx-auto px-4 py-6">

        @if (loading()) {
          <p class="text-slate-500 text-sm">Cargando...</p>
        } @else if (!contract()) {
          <p class="text-rose-600 text-sm">No se pudo cargar la información del contrato.</p>
        } @else {

          @switch (tab()) {

            <!-- ============ Contrato ============ -->
            @case ('contract') {
              <section class="grid gap-4 sm:grid-cols-2">
                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                  <p class="text-xs text-slate-500">Contrato</p>
                  <p class="text-lg font-semibold font-mono">{{ contract()!.code }}</p>
                  <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    Plan: <span class="font-medium">{{ contract()!.plan_name }}</span>
                  </p>
                  <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium mt-2"
                    [class]="contractStatusClass()">{{ contract()!.status }}</span>
                </div>

                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                  <p class="text-xs text-slate-500">Cuota</p>
                  <p class="text-2xl font-semibold">$ {{ contract()!.fee_amount | number:'1.0-0' }}</p>
                  <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    Frecuencia: <span class="capitalize">{{ freqLabel(contract()!.payment_frequency) }}</span>
                  </p>
                  @if (contract()!.next_payment_date) {
                    <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">
                      Próximo pago: <span class="font-medium">{{ contract()!.next_payment_date | date:'mediumDate' }}</span>
                    </p>
                  }
                </div>

                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4 sm:col-span-2">
                  <h2 class="text-sm font-semibold mb-3">Titular</h2>
                  <dl class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                    <div><dt class="text-xs text-slate-500">Nombre</dt><dd>{{ titularName() }}</dd></div>
                    <div><dt class="text-xs text-slate-500">Email</dt><dd>{{ contract()!.titular_email || '—' }}</dd></div>
                    <div><dt class="text-xs text-slate-500">Teléfono</dt><dd>{{ contract()!.titular_phone || contract()!.titular_mobile || '—' }}</dd></div>
                    <div><dt class="text-xs text-slate-500">Dirección</dt><dd>{{ contract()!.titular_address || '—' }}</dd></div>
                  </dl>
                </div>

                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4 sm:col-span-2">
                  <h2 class="text-sm font-semibold mb-3">Beneficiarios ({{ contract()!.beneficiaries.length }})</h2>
                  @if (contract()!.beneficiaries.length === 0) {
                    <p class="text-sm text-slate-500">Sin beneficiarios registrados.</p>
                  } @else {
                    <ul class="divide-y divide-slate-100 dark:divide-slate-800">
                      @for (b of contract()!.beneficiaries; track b.id) {
                        <li class="py-2 flex items-center justify-between">
                          <div>
                            <p class="text-sm font-medium">{{ b.first_name }} {{ b.last_name }}</p>
                            <p class="text-xs text-slate-500">
                              {{ b.relationship || 'Beneficiario' }}
                              @if (b.document_number) { · doc: {{ b.document_number }} }
                            </p>
                          </div>
                          @if (b.is_titular) {
                            <span class="text-xs px-2 py-0.5 rounded-md bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">Titular</span>
                          }
                        </li>
                      }
                    </ul>
                  }
                </div>
              </section>
            }

            <!-- ============ Facturas ============ -->
            @case ('invoices') {
              @if (invoices().length === 0) {
                <p class="text-sm text-slate-500">Aún no hay facturas asociadas.</p>
              } @else {
                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
                  <table class="min-w-full text-sm">
                    <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                      <tr>
                        <th class="text-left px-3 py-2 font-medium">Código</th>
                        <th class="text-left px-3 py-2 font-medium">Emisión</th>
                        <th class="text-left px-3 py-2 font-medium">Vence</th>
                        <th class="text-right px-3 py-2 font-medium">Total</th>
                        <th class="text-right px-3 py-2 font-medium">Pagado</th>
                        <th class="text-right px-3 py-2 font-medium">Saldo</th>
                        <th class="text-left px-3 py-2 font-medium">Estado</th>
                        <th class="text-right px-3 py-2 font-medium">PDF</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                      @for (inv of invoices(); track inv.id) {
                        <tr>
                          <td class="px-3 py-2 font-mono text-xs">{{ inv.code }}</td>
                          <td class="px-3 py-2">{{ inv.issue_date | date:'mediumDate' }}</td>
                          <td class="px-3 py-2">{{ inv.due_date | date:'mediumDate' }}</td>
                          <td class="px-3 py-2 text-right">$ {{ +inv.total | number:'1.0-0' }}</td>
                          <td class="px-3 py-2 text-right">$ {{ +inv.paid_amount | number:'1.0-0' }}</td>
                          <td class="px-3 py-2 text-right font-medium">$ {{ +inv.balance | number:'1.0-0' }}</td>
                          <td class="px-3 py-2">
                            <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium"
                              [class]="invoiceStatusClass(inv.status)">{{ inv.status }}</span>
                          </td>
                          <td class="px-3 py-2 text-right">
                            <button (click)="downloadPdf(inv)" type="button"
                              class="text-xs text-brand-600 hover:underline">Descargar</button>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            }

            <!-- ============ Pagos ============ -->
            @case ('payments') {
              @if (payments().length === 0) {
                <p class="text-sm text-slate-500">Aún no hay pagos registrados.</p>
              } @else {
                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
                  <table class="min-w-full text-sm">
                    <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                      <tr>
                        <th class="text-left px-3 py-2 font-medium">Código</th>
                        <th class="text-left px-3 py-2 font-medium">Fecha</th>
                        <th class="text-right px-3 py-2 font-medium">Monto</th>
                        <th class="text-left px-3 py-2 font-medium">Método</th>
                        <th class="text-left px-3 py-2 font-medium">Referencia</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                      @for (p of payments(); track p.id) {
                        <tr>
                          <td class="px-3 py-2 font-mono text-xs">{{ p.code }}</td>
                          <td class="px-3 py-2">{{ p.payment_date | date:'mediumDate' }}</td>
                          <td class="px-3 py-2 text-right">$ {{ +p.amount | number:'1.0-0' }}</td>
                          <td class="px-3 py-2 capitalize">{{ p.method }}</td>
                          <td class="px-3 py-2">{{ p.reference || '—' }}</td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            }

            <!-- ============ Servicios ============ -->
            @case ('services') {
              @if (services().length === 0) {
                <p class="text-sm text-slate-500">Sin servicios prestados bajo este contrato.</p>
              } @else {
                <ul class="space-y-3">
                  @for (s of services(); track s.id) {
                    <li class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                      <p class="text-xs text-slate-500 font-mono">{{ s.code }}</p>
                      <p class="text-base font-semibold mt-1">{{ s.deceased_first_name }} {{ s.deceased_last_name }}</p>
                      <p class="text-sm text-slate-600 dark:text-slate-400">
                        Fallecimiento: {{ s.deceased_death_date | date:'mediumDate' }}
                      </p>
                      <p class="text-sm text-slate-600 dark:text-slate-400">
                        Servicio: <span class="capitalize">{{ s.service_type.replace('_', ' ') }}</span>
                        · Estado: <span class="capitalize">{{ s.status }}</span>
                      </p>
                    </li>
                  }
                </ul>
              }
            }
          }
        }
      </main>
    </div>
  `,
})
export class MemorialPortalHomeComponent implements OnInit {
  private readonly portal = inject(MemorialPortalService);
  private readonly router = inject(Router);

  readonly tabs: { value: Tab; label: string }[] = [
    { value: 'contract', label: 'Mi contrato' },
    { value: 'invoices', label: 'Facturas' },
    { value: 'payments', label: 'Pagos' },
    { value: 'services', label: 'Servicios' },
  ];

  tab = signal<Tab>('contract');
  loading = signal(true);
  contract = signal<PortalContract | null>(null);
  invoices = signal<PortalInvoice[]>([]);
  payments = signal<PortalPayment[]>([]);
  services = signal<PortalServiceItem[]>([]);

  titularName = computed(() => {
    const c = this.contract();
    if (!c) return '';
    if (c.titular_business_name) return c.titular_business_name;
    return [c.titular_first_name, c.titular_last_name].filter(Boolean).join(' ').trim() || '—';
  });

  ngOnInit(): void {
    if (!this.portal.getToken()) {
      this.router.navigate(['/memorial-portal']);
      return;
    }
    this.portal.me().subscribe({
      next: (c) => {
        this.contract.set(c);
        this.loading.set(false);
      },
      error: () => {
        this.portal.clear();
        this.loading.set(false);
        this.router.navigate(['/memorial-portal']);
      },
    });
    this.loadAux();
  }

  loadAux(): void {
    this.portal.invoices().subscribe({ next: (r) => this.invoices.set(r) });
    this.portal.payments().subscribe({ next: (r) => this.payments.set(r) });
    this.portal.services().subscribe({ next: (r) => this.services.set(r) });
  }

  setTab(t: Tab): void {
    this.tab.set(t);
  }

  logout(): void {
    this.portal.clear();
    this.router.navigate(['/memorial-portal']);
  }

  freqLabel(f: string): string {
    const map: Record<string, string> = {
      monthly: 'mensual', quarterly: 'trimestral',
      semiannual: 'semestral', annual: 'anual',
    };
    return map[f] || f;
  }

  contractStatusClass(): string {
    const s = this.contract()?.status;
    const map: Record<string, string> = {
      active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      suspended: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      expired: 'bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200',
    };
    return map[s || ''] || '';
  }

  invoiceStatusClass(s: string): string {
    const map: Record<string, string> = {
      pending: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      partial: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      paid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      overdue: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      annulled: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    };
    return map[s] || '';
  }

  downloadPdf(inv: PortalInvoice): void {
    this.portal.downloadInvoicePdf(inv.id).subscribe({
      next: ({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `factura-${inv.code}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      },
    });
  }
}
