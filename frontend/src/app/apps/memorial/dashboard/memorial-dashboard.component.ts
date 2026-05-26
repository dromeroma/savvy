import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import { MemorialDashboardKpis } from '../../../core/models/memorial.model';

@Component({
  selector: 'app-memorial-dashboard',
  imports: [CommonModule, RouterLink],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">SavvyMemorial</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Resumen operativo del módulo funerario.
        </p>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-gray-600"></div>
        </div>
      } @else if (kpis(); as k) {
        <!-- Top KPI row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-[11px] uppercase tracking-wider text-gray-400">Servicios totales</div>
            <div class="text-3xl font-semibold text-gray-800 dark:text-white/90 mt-1">{{ k.services_total }}</div>
          </div>
          <div class="rounded-2xl border border-amber-200 dark:border-amber-700/40 bg-amber-50/60 dark:bg-amber-500/10 p-5">
            <div class="text-[11px] uppercase tracking-wider text-amber-700 dark:text-amber-400">Activos</div>
            <div class="text-3xl font-semibold text-amber-700 dark:text-amber-300 mt-1">{{ k.services_active }}</div>
            <div class="text-xs text-amber-700/80 dark:text-amber-400/80 mt-1">iniciado · en proceso · pendiente</div>
          </div>
          <div class="rounded-2xl border border-emerald-200 dark:border-emerald-700/40 bg-emerald-50/60 dark:bg-emerald-500/10 p-5">
            <div class="text-[11px] uppercase tracking-wider text-emerald-700 dark:text-emerald-400">Cerrados</div>
            <div class="text-3xl font-semibold text-emerald-700 dark:text-emerald-300 mt-1">{{ k.services_closed }}</div>
            <div class="text-xs text-emerald-700/80 dark:text-emerald-400/80 mt-1">finalizado · cancelado</div>
          </div>
          <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
            <div class="text-[11px] uppercase tracking-wider text-gray-400">Defunciones hoy</div>
            <div class="text-3xl font-semibold text-gray-800 dark:text-white/90 mt-1">{{ k.services_today }}</div>
          </div>
        </div>

        <!-- Breakdown by status -->
        <div class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
          <h2 class="text-sm font-semibold text-gray-800 dark:text-white/90 mb-4">Distribución por estado</h2>
          <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
            @for (s of statuses; track s) {
              <div>
                <div class="text-[11px] uppercase tracking-wider text-gray-400">{{ statusLabel(s) }}</div>
                <div class="text-xl font-semibold text-gray-800 dark:text-white/90 mt-1">
                  {{ k.services_by_status[s] || 0 }}
                </div>
              </div>
            }
          </div>
        </div>

        <!-- Quick links -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <a routerLink="/memorial/services"
            class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 hover:border-brand-400 transition">
            <div class="text-sm font-semibold text-gray-800 dark:text-white/90">Servicios funerarios</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Crear, ver y gestionar servicios. Estados, familiares, ejecución.
            </div>
          </a>
          <div class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 p-5 text-gray-400">
            <div class="text-sm font-medium">Planes exequiales</div>
            <div class="text-xs mt-1">Disponible en la próxima fase (afiliados + cuotas).</div>
          </div>
        </div>
      } @else {
        <div class="p-5 bg-error-50 border border-error-200 dark:bg-error-500/10 dark:border-error-500/30 rounded-xl text-sm text-error-700 dark:text-error-400">
          No se pudo cargar el resumen de SavvyMemorial.
        </div>
      }
    </div>
  `,
})
export class MemorialDashboardComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);

  loading = signal(true);
  kpis = signal<MemorialDashboardKpis | null>(null);

  readonly statuses = ['iniciado', 'en_proceso', 'pendiente', 'finalizado', 'cancelado'];

  ngOnInit(): void {
    this.memorial.getKpis().subscribe({
      next: (d) => { this.kpis.set(d); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  statusLabel(s: string): string {
    switch (s) {
      case 'iniciado': return 'Iniciado';
      case 'en_proceso': return 'En proceso';
      case 'pendiente': return 'Pendiente';
      case 'finalizado': return 'Finalizado';
      case 'cancelado': return 'Cancelado';
      default: return s;
    }
  }
}
