import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HotelService, HotelDashboard } from '../hotel.service';

@Component({
  selector: 'app-hotel-dashboard',
  imports: [CommonModule, DecimalPipe, RouterLink],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">SavvyHotel</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Ocupación, llegadas y desempeño de hoy.</p>
        </div>
        <a routerLink="/hotel/reservations" class="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium">Reservas</a>
      </div>

      @if (d(); as m) {
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5">
            <p class="text-xs uppercase tracking-wider text-gray-400">Ocupación</p>
            <p class="text-3xl font-bold text-gray-800 dark:text-white/90 mt-1">{{ m.occupancy_rate | number:'1.0-1' }}%</p>
            <p class="text-xs text-gray-500 mt-1">{{ m.occupied_rooms }}/{{ m.total_rooms }} habitaciones</p>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5">
            <p class="text-xs uppercase tracking-wider text-gray-400">ADR (tarifa prom.)</p>
            <p class="text-3xl font-bold text-gray-800 dark:text-white/90 mt-1">$ {{ m.adr | number:'1.0-0' }}</p>
            <p class="text-xs text-gray-500 mt-1">RevPAR $ {{ m.revpar | number:'1.0-0' }}</p>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5">
            <p class="text-xs uppercase tracking-wider text-gray-400">Llegadas hoy</p>
            <p class="text-3xl font-bold text-emerald-600 mt-1">{{ m.arrivals_today }}</p>
            <p class="text-xs text-gray-500 mt-1">Salidas {{ m.departures_today }} · En casa {{ m.in_house }}</p>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5">
            <p class="text-xs uppercase tracking-wider text-gray-400">Ingreso de hoy</p>
            <p class="text-3xl font-bold text-gray-800 dark:text-white/90 mt-1">$ {{ m.revenue_today | number:'1.0-0' }}</p>
            <p class="text-xs mt-1" [class.text-amber-600]="m.dirty_rooms > 0" [class.text-gray-500]="m.dirty_rooms === 0">{{ m.dirty_rooms }} por limpiar</p>
          </div>
        </div>

        <div class="flex flex-wrap gap-3">
          <a routerLink="/hotel/reservations" class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800">➕ Nueva reserva</a>
          <a routerLink="/hotel/rooms" class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800">🛏️ Habitaciones</a>
          <a routerLink="/hotel/housekeeping" class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800">🧹 Housekeeping</a>
        </div>
      } @else {
        <div class="flex items-center justify-center py-20"><div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div></div>
      }
    </div>
  `,
})
export class HotelDashboardComponent implements OnInit {
  private readonly hotel = inject(HotelService);
  d = signal<HotelDashboard | null>(null);
  ngOnInit(): void { this.hotel.dashboard().subscribe({ next: (r) => this.d.set(r) }); }
}
