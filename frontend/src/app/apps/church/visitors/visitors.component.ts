import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface Visitor {
  id: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  email: string | null;
  visit_date: string;
  how_found: string | null;
  notes: string | null;
  status: string;
  converted_person_id: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  new: 'Nuevo',
  contacted: 'Contactado',
  follow_up: 'En seguimiento',
  converted: 'Convertido',
  not_interested: 'No interesado',
};

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',
  contacted: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400',
  follow_up: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400',
  converted: 'bg-success-100 text-success-700 dark:bg-success-500/20 dark:text-success-400',
  not_interested: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
};

const HOW_FOUND_OPTIONS = [
  'Invitación de un miembro',
  'Redes sociales',
  'Publicidad',
  'Pasaba por el lugar',
  'Familiar',
  'Otro',
];

@Component({
  selector: 'app-visitors',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Visitantes</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Registro y seguimiento de visitantes</p>
        </div>
        <button (click)="openModal()"
          class="px-4 py-2.5 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition shadow-theme-xs shrink-0">
          + Nuevo visitante
        </button>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2 mb-6">
        <button (click)="statusFilter = ''; loadVisitors()"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
          [ngClass]="statusFilter === '' ? 'bg-brand-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'">
          Todos
        </button>
        @for (s of statusOptions; track s.key) {
          <button (click)="statusFilter = s.key; loadVisitors()"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
            [ngClass]="statusFilter === s.key ? 'bg-brand-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'">
            {{ s.label }}
          </button>
        }
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
                  <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Nombre</th>
                  <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden sm:table-cell">Teléfono</th>
                  <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden md:table-cell">Fecha visita</th>
                  <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden lg:table-cell">Cómo nos encontró</th>
                  <th class="text-left px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Estado</th>
                  <th class="text-right px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">Acciones</th>
                </tr>
              </thead>
              <tbody>
                @for (v of visitors(); track v.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/[0.02] transition">
                    <td class="px-6 py-4 font-medium text-gray-800 dark:text-white/90">{{ v.first_name }} {{ v.last_name }}</td>
                    <td class="px-6 py-4 text-gray-600 dark:text-gray-300 hidden sm:table-cell">{{ v.phone || '-' }}</td>
                    <td class="px-6 py-4 text-gray-600 dark:text-gray-300 hidden md:table-cell">{{ v.visit_date }}</td>
                    <td class="px-6 py-4 text-gray-600 dark:text-gray-300 hidden lg:table-cell">{{ v.how_found || '-' }}</td>
                    <td class="px-6 py-4">
                      <select [(ngModel)]="v.status" (ngModelChange)="updateStatus(v)"
                        class="text-xs px-2 py-1 rounded-full border-0 font-medium cursor-pointer" [ngClass]="getStatusColor(v.status)">
                        @for (s of statusOptions; track s.key) {
                          <option [value]="s.key">{{ s.label }}</option>
                        }
                      </select>
                    </td>
                    <td class="px-6 py-4 text-right">
                      @if (v.status !== 'converted') {
                        <button (click)="convertVisitor(v)" class="text-xs text-brand-600 dark:text-brand-400 hover:underline font-medium">
                          Convertir a congregante
                        </button>
                      } @else {
                        <span class="text-xs text-success-600 dark:text-success-400">Congregante</span>
                      }
                    </td>
                  </tr>
                } @empty {
                  <tr><td colspan="6" class="px-6 py-12 text-center text-gray-400 dark:text-gray-500">No hay visitantes registrados.</td></tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      }

      <!-- Create Modal -->
      @if (showModal) {
        <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Nuevo visitante</h3>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nombre *</label>
                  <input type="text" [(ngModel)]="form.first_name"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Apellido *</label>
                  <input type="text" [(ngModel)]="form.last_name"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Teléfono</label>
                  <input type="text" [(ngModel)]="form.phone"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Email</label>
                  <input type="email" [(ngModel)]="form.email"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Fecha de visita *</label>
                  <input type="date" [(ngModel)]="form.visit_date"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Cómo nos encontró</label>
                  <select [(ngModel)]="form.how_found"
                    class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition">
                    <option value="">Seleccionar...</option>
                    @for (opt of howFoundOptions; track opt) {
                      <option [value]="opt">{{ opt }}</option>
                    }
                  </select>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Notas</label>
                <textarea [(ngModel)]="form.notes" rows="2"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-800 dark:text-white/90 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition resize-none"></textarea>
              </div>
            </div>
            <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button (click)="showModal = false"
                class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">Cancelar</button>
              <button (click)="createVisitor()" [disabled]="!form.first_name || !form.last_name || !form.visit_date"
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition disabled:opacity-50">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class VisitorsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  visitors = signal<Visitor[]>([]);
  showModal = false;
  statusFilter = '';

  statusOptions = [
    { key: 'new', label: 'Nuevo' },
    { key: 'contacted', label: 'Contactado' },
    { key: 'follow_up', label: 'En seguimiento' },
    { key: 'converted', label: 'Convertido' },
    { key: 'not_interested', label: 'No interesado' },
  ];

  howFoundOptions = HOW_FOUND_OPTIONS;

  form = { first_name: '', last_name: '', phone: '', email: '', visit_date: '', how_found: '', notes: '' };

  ngOnInit(): void {
    this.loadVisitors();
  }

  loadVisitors(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.statusFilter) params['status'] = this.statusFilter;
    this.api.get<Visitor[]>('/church/visitors/', params).subscribe({
      next: (data) => { this.visitors.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openModal(): void {
    this.form = { first_name: '', last_name: '', phone: '', email: '', visit_date: new Date().toISOString().split('T')[0], how_found: '', notes: '' };
    this.showModal = true;
  }

  createVisitor(): void {
    const body: Record<string, any> = { first_name: this.form.first_name, last_name: this.form.last_name, visit_date: this.form.visit_date };
    if (this.form.phone) body['phone'] = this.form.phone;
    if (this.form.email) body['email'] = this.form.email;
    if (this.form.how_found) body['how_found'] = this.form.how_found;
    if (this.form.notes) body['notes'] = this.form.notes;

    this.api.post('/church/visitors/', body).subscribe({
      next: () => {
        this.showModal = false;
        this.loadVisitors();
        this.notify.show({ type: 'success', title: 'Registrado', message: 'Visitante registrado correctamente' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'Error al registrar visitante' }),
    });
  }

  updateStatus(v: Visitor): void {
    this.api.patch(`/church/visitors/${v.id}`, { status: v.status }).subscribe({
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'Error al actualizar estado' }),
    });
  }

  convertVisitor(v: Visitor): void {
    this.api.post(`/church/visitors/${v.id}/convert`, {}).subscribe({
      next: () => {
        this.loadVisitors();
        this.notify.show({ type: 'success', title: 'Convertido', message: `${v.first_name} ahora es congregante` });
      },
      error: (err) => {
        const msg = err.error?.detail || 'Error al convertir visitante';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
      },
    });
  }

  getStatusColor(status: string): string {
    return STATUS_COLORS[status] || STATUS_COLORS['new'];
  }
}
