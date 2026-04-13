import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface Feature {
  id: string;
  key: string;
  name: string;
  description: string | null;
  category: string | null;
  feature_type: string;
  default_enabled: boolean | null;
  default_limit: number | null;
  created_at: string;
}

@Component({
  selector: 'app-platform-features-catalog',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">Catálogo de features</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Capacidades que pueden habilitarse o limitarse por plan u organización</p>
        </div>
        <button (click)="openCreate()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition">
          + Nueva feature
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="space-y-6">
          @for (group of grouped(); track group.category) {
            <div>
              <p class="text-[10px] uppercase tracking-wider font-semibold text-gray-400 mb-2">{{ group.category }}</p>
              <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                      <th class="px-4 py-3 font-medium text-gray-500">Feature</th>
                      <th class="px-4 py-3 font-medium text-gray-500">Clave</th>
                      <th class="px-4 py-3 font-medium text-gray-500">Tipo</th>
                      <th class="px-4 py-3 font-medium text-gray-500">Default</th>
                      <th class="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (f of group.items; track f.id) {
                      <tr class="border-b border-gray-100 dark:border-gray-700/50">
                        <td class="px-4 py-3">
                          <p class="font-medium text-gray-800 dark:text-white/90">{{ f.name }}</p>
                          @if (f.description) {
                            <p class="text-xs text-gray-500">{{ f.description }}</p>
                          }
                        </td>
                        <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ f.key }}</td>
                        <td class="px-4 py-3">
                          <span class="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full"
                            [ngClass]="f.feature_type === 'boolean' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400' : 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400'">
                            {{ f.feature_type }}
                          </span>
                        </td>
                        <td class="px-4 py-3 text-xs text-gray-600 dark:text-gray-400">
                          @if (f.feature_type === 'boolean') {
                            {{ f.default_enabled ? 'ON' : 'OFF' }}
                          } @else {
                            {{ f.default_limit ?? '—' }}
                          }
                        </td>
                        <td class="px-4 py-3 text-right">
                          <div class="flex justify-end gap-2">
                            <button (click)="openEdit(f)" class="text-xs text-brand-600 dark:text-brand-400 hover:underline">Editar</button>
                            <button (click)="deleteFeature(f)" class="text-xs text-red-600 hover:underline">Eliminar</button>
                          </div>
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>
          }
        </div>
      }

      <!-- Create / Edit modal -->
      @if (showModal()) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">
                {{ editingId() ? 'Editar feature' : 'Nueva feature' }}
              </h3>
            </div>
            <div class="p-6 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Clave *</label>
                <input type="text" [(ngModel)]="form.key" [disabled]="!!editingId()" placeholder="custom_reports"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm font-mono disabled:opacity-60" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                <input type="text" [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
                <textarea [(ngModel)]="form.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm resize-none"></textarea>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Categoría</label>
                  <input type="text" [(ngModel)]="form.category" placeholder="limits, support, branding..."
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Tipo *</label>
                  <select [(ngModel)]="form.feature_type" [disabled]="!!editingId()"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm disabled:opacity-60">
                    <option value="boolean">Boolean</option>
                    <option value="quantity">Quantity</option>
                  </select>
                </div>
              </div>
              @if (form.feature_type === 'boolean') {
                <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input type="checkbox" [(ngModel)]="form.default_enabled" class="rounded" />
                  Habilitada por default
                </label>
              } @else {
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Límite por default</label>
                  <input type="number" [(ngModel)]="form.default_limit" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm" />
                </div>
              }
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="closeModal()" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class FeaturesCatalogComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  features = signal<Feature[]>([]);

  showModal = signal(false);
  editingId = signal<string | null>(null);
  form: any = {
    key: '',
    name: '',
    description: '',
    category: '',
    feature_type: 'boolean',
    default_enabled: false,
    default_limit: null,
  };

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.get<Feature[]>('/platform/features').subscribe({
      next: (f) => {
        this.features.set(f);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  grouped(): Array<{ category: string; items: Feature[] }> {
    const map = new Map<string, Feature[]>();
    for (const f of this.features()) {
      const cat = f.category || 'general';
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat)!.push(f);
    }
    return Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([category, items]) => ({ category, items }));
  }

  openCreate(): void {
    this.editingId.set(null);
    this.form = {
      key: '', name: '', description: '', category: '',
      feature_type: 'boolean', default_enabled: false, default_limit: null,
    };
    this.showModal.set(true);
  }

  openEdit(f: Feature): void {
    this.editingId.set(f.id);
    this.form = {
      key: f.key,
      name: f.name,
      description: f.description || '',
      category: f.category || '',
      feature_type: f.feature_type,
      default_enabled: f.default_enabled,
      default_limit: f.default_limit,
    };
    this.showModal.set(true);
  }

  closeModal(): void {
    this.showModal.set(false);
    this.editingId.set(null);
  }

  save(): void {
    if (!this.form.name || !this.form.key) {
      this.notify.show({ type: 'error', title: 'Faltan datos', message: 'Clave y nombre son obligatorios' });
      return;
    }
    const editId = this.editingId();
    const body = {
      name: this.form.name,
      description: this.form.description || null,
      category: this.form.category || null,
      default_enabled: this.form.default_enabled,
      default_limit: this.form.default_limit,
    };
    const req$ = editId
      ? this.api.patch<Feature>(`/platform/features/${editId}`, body)
      : this.api.post<Feature>('/platform/features', {
          key: this.form.key,
          feature_type: this.form.feature_type,
          ...body,
        });
    req$.subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Guardado', message: this.form.name });
        this.closeModal();
        this.load();
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo guardar',
      }),
    });
  }

  deleteFeature(f: Feature): void {
    if (!confirm(`¿Eliminar la feature "${f.name}"? Debe no estar referenciada por ningún plan u override.`)) return;
    this.api.delete(`/platform/features/${f.id}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminada', message: f.name });
        this.load();
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err.error?.detail || 'No se pudo eliminar',
      }),
    });
  }
}
