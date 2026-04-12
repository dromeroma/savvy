import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pay-subscriptions',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Suscripciones</h2><p class="text-sm text-gray-500 dark:text-gray-400">Planes y cobros recurrentes</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Plan</button>
      </div>
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Planes</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        @for (p of plans(); track p.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ p.name }}</h4>
            <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">$ {{ p.amount | number:'1.0-0' }} <span class="text-xs font-normal text-gray-500">/ {{ p.billing_cycle }}</span></p>
            <div class="flex gap-2 text-xs text-gray-500 mt-2"><span>{{ p.code }}</span>@if (p.trial_days > 0) { <span>Trial: {{ p.trial_days }}d</span> }</div>
          </div>
        }
        @if (plans().length === 0) { <p class="text-sm text-gray-400 col-span-full text-center py-4">No hay planes</p> }
      </div>
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Suscripciones Activas</h3>
      <div class="space-y-3">
        @for (s of subscriptions(); track s.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex justify-between items-center">
            <div><p class="text-sm text-gray-800 dark:text-white/90">Plan: {{ s.plan_id | slice:0:8 }}</p><p class="text-xs text-gray-500">Periodo: {{ s.current_period_start }} - {{ s.current_period_end }}</p></div>
            <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">{{ s.status }}</span>
          </div>
        }
        @if (subscriptions().length === 0) { <p class="text-sm text-gray-400 text-center py-4">No hay suscripciones activas</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Plan</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="planForm.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Codigo</label><input [(ngModel)]="planForm.code" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
              <div class="grid grid-cols-2 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Monto</label><input type="number" [(ngModel)]="planForm.amount" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ciclo</label><select [(ngModel)]="planForm.billing_cycle" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="weekly">Semanal</option><option value="monthly">Mensual</option><option value="quarterly">Trimestral</option><option value="annual">Anual</option></select></div></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="savePlan()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Crear</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PaySubscriptionsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  plans = signal<any[]>([]); subscriptions = signal<any[]>([]); showModal = false;
  planForm: any = { name: '', code: '', amount: 50000, billing_cycle: 'monthly' };
  ngOnInit(): void { this.load(); }
  load(): void {
    this.api.get<any[]>('/pay/subscriptions/plans').subscribe({ next: (r) => this.plans.set(r) });
    this.api.get<any[]>('/pay/subscriptions').subscribe({ next: (r) => this.subscriptions.set(r) });
  }
  savePlan(): void { this.api.post('/pay/subscriptions/plans', this.planForm).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Plan creado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
