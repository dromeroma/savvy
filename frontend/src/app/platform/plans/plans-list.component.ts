import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface Plan {
  id: string;
  code: string;
  name: string;
  tier: number;
  description: string | null;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  is_active: boolean;
  is_public: boolean;
  sort_order: number;
}

@Component({
  selector: 'app-platform-plans-list',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Planes de suscripción</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Catálogo de planes ofrecidos a empresas</p>
        </div>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          @for (plan of plans(); track plan.id) {
            <div class="bg-white dark:bg-gray-800 rounded-2xl border p-6 transition"
              [ngClass]="plan.is_active ? 'border-gray-200 dark:border-gray-700' : 'border-gray-200 dark:border-gray-700 opacity-60'">
              <div class="flex items-start justify-between mb-3">
                <div>
                  <p class="text-xs uppercase tracking-wide text-gray-500 font-mono">{{ plan.code }}</p>
                  <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mt-1">{{ plan.name }}</h3>
                </div>
                @if (!plan.is_public) {
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500">Oculto</span>
                }
              </div>
              @if (plan.description) {
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{{ plan.description }}</p>
              }
              <div class="mb-4">
                <p class="text-2xl font-bold text-brand-600 dark:text-brand-400">$ {{ plan.price_monthly }}</p>
                <p class="text-xs text-gray-500">USD / mes · $ {{ plan.price_yearly }} / año</p>
              </div>
              <div class="flex gap-2">
                <button (click)="startEdit(plan)" class="flex-1 text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                  Editar precio
                </button>
              </div>
            </div>
          }
        </div>
      }

      <!-- Edit modal -->
      @if (editing()) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Editar {{ editing()!.name }}</h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre</label>
                <input type="text" [(ngModel)]="editForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="editForm.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm resize-none"></textarea>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Precio mensual</label>
                  <input type="number" step="0.01" [(ngModel)]="editForm.price_monthly" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Precio anual</label>
                  <input type="number" step="0.01" [(ngModel)]="editForm.price_yearly" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
                </div>
              </div>
              <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input type="checkbox" [(ngModel)]="editForm.is_public" class="rounded border-gray-300" />
                Visible públicamente
              </label>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="editing.set(null)" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PlansListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  plans = signal<Plan[]>([]);
  editing = signal<Plan | null>(null);
  editForm: any = {};

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.get<Plan[]>('/platform/plans', { include_inactive: true }).subscribe({
      next: (p) => {
        this.plans.set(p);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  startEdit(p: Plan): void {
    this.editing.set(p);
    this.editForm = {
      name: p.name,
      description: p.description || '',
      price_monthly: p.price_monthly,
      price_yearly: p.price_yearly,
      is_public: p.is_public,
    };
  }

  save(): void {
    const p = this.editing();
    if (!p) return;
    this.api.patch<Plan>(`/platform/plans/${p.id}`, this.editForm).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Guardado', message: `${p.name} actualizado` });
        this.editing.set(null);
        this.load();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo actualizar' }),
    });
  }
}
