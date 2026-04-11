import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-teachers',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Docentes</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Gestión de profesores y personal académico</p>
        </div>
        <button (click)="showModal = true"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
          + Nuevo Docente
        </button>
      </div>

      <!-- Search -->
      <div class="flex flex-col sm:flex-row gap-3 mb-4">
        <input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar por nombre, código..."
          class="w-full sm:w-80 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
        <select [(ngModel)]="statusFilter" (ngModelChange)="load()"
          class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
          <option value="">Todos</option>
          <option value="active">Activo</option>
          <option value="inactive">Inactivo</option>
          <option value="on_leave">Con licencia</option>
        </select>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else {
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Código</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Nombre</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Email</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Especialización</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Contrato</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
                </tr>
              </thead>
              <tbody>
                @for (t of teachers(); track t.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-white/5 transition">
                    <td class="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">{{ t.employee_code }}</td>
                    <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ t.first_name }} {{ t.last_name }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ t.email || '-' }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ t.specialization || '-' }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ contractLabel(t.contract_type) }}</td>
                    <td class="px-4 py-3">
                      <span class="px-2 py-0.5 text-xs rounded-full"
                        [class]="t.status === 'active'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : t.status === 'on_leave'
                            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'">
                        {{ statusLabel(t.status) }}
                      </span>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (teachers().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No hay docentes registrados</p>
          }
          @if (total() > 0) {
            <div class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700">
              {{ teachers().length }} de {{ total() }} docentes
            </div>
          }
        </div>
      }

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto custom-scrollbar p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Docente</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label>
                  <input [(ngModel)]="form.first_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Apellido</label>
                  <input [(ngModel)]="form.last_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código Empleado</label>
                  <input [(ngModel)]="form.employee_code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                  <input type="email" [(ngModel)]="form.email" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Especialización</label>
                  <input [(ngModel)]="form.specialization" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo Contrato</label>
                  <select [(ngModel)]="form.contract_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option value="">--</option>
                    <option value="full_time">Tiempo completo</option>
                    <option value="part_time">Medio tiempo</option>
                    <option value="adjunct">Catedrático</option>
                  </select>
                </div>
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
export class TeachersComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  teachers = signal<any[]>([]);
  total = signal(0);
  loading = signal(false);
  showModal = false;
  search = '';
  statusFilter = '';

  form: any = {
    first_name: '', last_name: '', employee_code: '', email: '',
    specialization: '', contract_type: '', phone: '',
  };

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const params: any = { page_size: 100 };
    if (this.search) params.search = this.search;
    if (this.statusFilter) params.status = this.statusFilter;

    this.api.get<any>('/edu/teachers', params).subscribe({
      next: (r) => { this.teachers.set(r.items); this.total.set(r.total); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  save(): void {
    const payload: any = {
      first_name: this.form.first_name,
      last_name: this.form.last_name,
      employee_code: this.form.employee_code,
    };
    if (this.form.email) payload.email = this.form.email;
    if (this.form.specialization) payload.specialization = this.form.specialization;
    if (this.form.contract_type) payload.contract_type = this.form.contract_type;
    if (this.form.phone) payload.phone = this.form.phone;

    this.api.post('/edu/teachers', payload).subscribe({
      next: () => {
        this.showModal = false;
        this.form = { first_name: '', last_name: '', employee_code: '', email: '', specialization: '', contract_type: '', phone: '' };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Docente creado' });
        this.load();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear el docente' }),
    });
  }

  statusLabel(s: string): string {
    const map: Record<string, string> = { active: 'Activo', inactive: 'Inactivo', on_leave: 'Con licencia' };
    return map[s] || s;
  }

  contractLabel(c: string): string {
    if (!c) return '-';
    const map: Record<string, string> = { full_time: 'Tiempo completo', part_time: 'Medio tiempo', adjunct: 'Catedrático' };
    return map[c] || c;
  }
}
