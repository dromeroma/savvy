import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-companies',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Empresas</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Organizaciones clientes</p>
        </div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nueva Empresa</button>
      </div>
      <div class="grid gap-4">
        @for (c of companies(); track c.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ c.name }}</h4>
                <div class="flex gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
                  @if (c.industry) { <span>{{ c.industry }}</span> }
                  @if (c.city) { <span>{{ c.city }}</span> }
                  @if (c.size) { <span>{{ c.size }}</span> }
                </div>
              </div>
              @if (c.website) { <a [href]="c.website" target="_blank" class="text-xs text-brand-600 dark:text-brand-400 hover:underline">{{ c.website }}</a> }
            </div>
          </div>
        }
        @if (companies().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay empresas</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Empresa</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Industria</label><input [(ngModel)]="form.industry" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
                <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ciudad</label><input [(ngModel)]="form.city" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              </div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Website</label><input [(ngModel)]="form.website" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class CompaniesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  companies = signal<any[]>([]);
  showModal = false;
  form: any = { name: '', industry: '', city: '', website: '' };
  ngOnInit(): void { this.load(); }
  load(): void { this.api.get<any[]>('/crm/companies').subscribe({ next: (r) => this.companies.set(r) }); }
  save(): void {
    this.api.post('/crm/companies', this.form).subscribe({
      next: () => { this.showModal = false; this.form = { name: '', industry: '', city: '', website: '' }; this.notify.show({ type: 'success', title: 'Listo', message: 'Empresa creada' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
}
