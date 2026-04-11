import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-families',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Familias</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Unidades familiares registradas</p>
        </div>
        <button (click)="showModal = true"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
          + Nueva Familia
        </button>
      </div>

      <div class="mb-4">
        <input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar por nombre..."
          class="w-full sm:w-80 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="grid gap-4">
          @for (f of families(); track f.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 cursor-pointer hover:border-brand-400 dark:hover:border-brand-500 transition"
              (click)="openFamily(f.id)">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ f.name }}</h4>
                  <div class="flex gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                    <span>Tipo: {{ typeLabel(f.type) }}</span>
                    @if (f.city) { <span>Ciudad: {{ f.city }}</span> }
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="px-2 py-1 text-xs rounded-full"
                    [class]="f.status === 'active'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'">
                    {{ f.status === 'active' ? 'Activa' : 'Inactiva' }}
                  </span>
                  <button (click)="openGenogram(f.id, $event)"
                    class="px-3 py-1.5 text-xs font-medium rounded-lg border border-pink-500 text-pink-600 dark:border-pink-400 dark:text-pink-400 hover:bg-pink-50 dark:hover:bg-pink-900/20 transition">
                    🌳 Genograma
                  </button>
                </div>
              </div>
            </div>
          }
          @if (families().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No hay familias registradas</p>
          }
        </div>
      }

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Familia</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                <input [(ngModel)]="form.name" placeholder="Familia Rodríguez López" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
                  <select [(ngModel)]="form.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option value="nuclear">Nuclear</option>
                    <option value="extended">Extendida</option>
                    <option value="single_parent">Monoparental</option>
                    <option value="blended">Reconstituida</option>
                    <option value="other">Otra</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ciudad</label>
                  <input [(ngModel)]="form.city" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dirección</label>
                <input [(ngModel)]="form.address" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Teléfono</label>
                <input [(ngModel)]="form.phone" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class FamiliesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  private readonly router = inject(Router);

  families = signal<any[]>([]);
  loading = signal(false);
  showModal = false;
  search = '';

  form: any = { name: '', type: 'nuclear', city: '', address: '', phone: '' };

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const params: any = {};
    if (this.search) params.search = this.search;

    this.api.get<any[]>('/family/units', params).subscribe({
      next: (r) => { this.families.set(r); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  save(): void {
    const payload: any = { name: this.form.name, type: this.form.type };
    if (this.form.city) payload.city = this.form.city;
    if (this.form.address) payload.address = this.form.address;
    if (this.form.phone) payload.phone = this.form.phone;

    this.api.post('/family/units', payload).subscribe({
      next: () => {
        this.showModal = false;
        this.form = { name: '', type: 'nuclear', city: '', address: '', phone: '' };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Familia creada' });
        this.load();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear la familia' }),
    });
  }

  openFamily(id: string): void {
    this.router.navigate(['/family', id]);
  }

  openGenogram(id: string, event: Event): void {
    event.stopPropagation();
    this.router.navigate(['/family', id, 'genogram']);
  }

  typeLabel(t: string): string {
    return { nuclear: 'Nuclear', extended: 'Extendida', single_parent: 'Monoparental', blended: 'Reconstituida', other: 'Otra' }[t] || t;
  }
}
