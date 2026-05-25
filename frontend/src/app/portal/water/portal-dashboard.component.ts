import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { PortalService } from '../../core/services/portal.service';
import { PortalDashboard } from '../../core/models/portal.model';

@Component({
  selector: 'app-portal-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div class="space-y-6">
      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-sky-200 border-t-sky-600"></div>
        </div>
      } @else if (data()) {
        @let d = data()!;

        <!-- Hero balance -->
        <div class="rounded-2xl p-6"
          [ngClass]="+d.open_balance > 0
            ? 'bg-gradient-to-br from-red-500 to-rose-600 text-white'
            : 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white'">
          <div class="text-xs uppercase tracking-wider opacity-80">
            {{ +d.open_balance > 0 ? 'Saldo pendiente' : 'Saldo al día' }}
          </div>
          <div class="text-4xl font-bold mt-1">$ {{ +d.open_balance | number:'1.0-0' }}</div>
          @if (d.pending_count > 0) {
            <div class="text-sm opacity-90 mt-2">
              {{ d.pending_count }} factura(s) sin pagar
              @if (d.overdue_count > 0) {
                · <span class="font-semibold">{{ d.overdue_count }} vencida(s)</span>
              }
            </div>
          } @else {
            <div class="text-sm opacity-90 mt-2">No tienes facturas pendientes 🎉</div>
          }
        </div>

        <!-- Highlights grid -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
            <div class="text-[11px] uppercase tracking-wider text-gray-400">Último consumo</div>
            @if (d.last_consumption_cubic !== null) {
              <div class="text-xl font-semibold text-gray-800 dark:text-white/90 mt-1">{{ d.last_consumption_cubic }} m³</div>
              <div class="text-[11px] text-gray-400 mt-0.5">{{ d.last_consumption_period }}</div>
            } @else {
              <div class="text-sm text-gray-400 italic mt-1">Sin lecturas todavía</div>
            }
          </div>
          <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
            <div class="text-[11px] uppercase tracking-wider text-gray-400">Última factura</div>
            @if (d.last_invoice_date) {
              <div class="text-xl font-semibold text-gray-800 dark:text-white/90 mt-1">{{ d.last_invoice_date }}</div>
            } @else {
              <div class="text-sm text-gray-400 italic mt-1">Sin facturas</div>
            }
          </div>
          <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
            <div class="text-[11px] uppercase tracking-wider text-gray-400">Último pago</div>
            @if (d.last_payment_date) {
              <div class="text-xl font-semibold text-gray-800 dark:text-white/90 mt-1">{{ d.last_payment_date }}</div>
            } @else {
              <div class="text-sm text-gray-400 italic mt-1">Sin pagos</div>
            }
          </div>
        </div>

        <!-- Quick links -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <a routerLink="/portal/water/invoices"
            class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:border-sky-400 transition text-center">
            <div class="text-3xl">🧾</div>
            <div class="text-sm font-medium text-gray-800 dark:text-white/90 mt-1">Mis facturas</div>
          </a>
          <a routerLink="/portal/water/payments"
            class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:border-sky-400 transition text-center">
            <div class="text-3xl">💸</div>
            <div class="text-sm font-medium text-gray-800 dark:text-white/90 mt-1">Mis pagos</div>
          </a>
          <a routerLink="/portal/water/consumption"
            class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:border-sky-400 transition text-center">
            <div class="text-3xl">📊</div>
            <div class="text-sm font-medium text-gray-800 dark:text-white/90 mt-1">Mi consumo</div>
          </a>
          <a routerLink="/portal/water/pqrs"
            class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:border-sky-400 transition text-center">
            <div class="text-3xl">📝</div>
            <div class="text-sm font-medium text-gray-800 dark:text-white/90 mt-1">PQRS</div>
          </a>
        </div>
      }
    </div>
  `,
})
export class PortalDashboardComponent implements OnInit {
  private readonly portal = inject(PortalService);

  loading = signal(true);
  data = signal<PortalDashboard | null>(null);

  ngOnInit(): void {
    this.portal.dashboard().subscribe({
      next: (d) => { this.data.set(d); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
}
