import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-edu-finance',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Finanzas Educativas</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Planes de matrícula, cobros y becas</p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-6 border-b border-gray-200 dark:border-gray-700">
        @for (tab of tabs; track tab.key) {
          <button (click)="activeTab = tab.key"
            class="px-4 py-2.5 text-sm font-medium transition rounded-t-lg"
            [class]="activeTab === tab.key
              ? 'text-brand-600 dark:text-brand-400 border-b-2 border-brand-600 dark:border-brand-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'">
            {{ tab.label }}
          </button>
        }
      </div>

      @if (activeTab === 'plans') {
        <div class="space-y-4">
          <div class="flex justify-end">
            <button (click)="showPlanModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Plan de Matrícula</button>
          </div>
          @for (plan of tuitionPlans(); track plan.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ plan.name }}</h4>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Total: $ {{ plan.total_amount | number:'1.2-2' }} | Cuotas: {{ plan.installments?.length || 0 }}
              </p>
            </div>
          }
          @if (tuitionPlans().length === 0) {
            <p class="text-sm text-gray-400 text-center py-8">No hay planes configurados</p>
          }
        </div>
      }

      @if (activeTab === 'charges') {
        <div class="space-y-4">
          <div class="flex justify-end">
            <button (click)="showChargeModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nuevo Cobro</button>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div class="overflow-x-auto custom-scrollbar">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Descripción</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Monto</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Saldo</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Vencimiento</th>
                    <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  @for (c of charges(); track c.id) {
                    <tr class="border-b border-gray-100 dark:border-gray-700/50">
                      <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ c.description }}</td>
                      <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">$ {{ c.amount | number:'1.2-2' }}</td>
                      <td class="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">$ {{ c.balance | number:'1.2-2' }}</td>
                      <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ c.due_date || '-' }}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 text-xs rounded-full"
                          [class]="c.status === 'paid' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : c.status === 'overdue' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                            : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'">
                          {{ c.status === 'paid' ? 'Pagado' : c.status === 'overdue' ? 'Vencido' : 'Pendiente' }}
                        </span>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
            @if (charges().length === 0) {
              <p class="text-sm text-gray-400 text-center py-8">No hay cobros registrados</p>
            }
          </div>
        </div>
      }

      @if (activeTab === 'scholarships') {
        <div class="space-y-4">
          <div class="flex justify-end">
            <button (click)="showSchModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">+ Nueva Beca</button>
          </div>
          @for (s of scholarships(); track s.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 flex justify-between items-center">
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ s.name }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ s.type === 'percentage' ? s.value + '%' : '$ ' + s.value }}
                </p>
              </div>
              <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">{{ s.status }}</span>
            </div>
          }
          @if (scholarships().length === 0) {
            <p class="text-sm text-gray-400 text-center py-8">No hay becas configuradas</p>
          }
        </div>
      }

      <!-- Plan Modal -->
      @if (showPlanModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showPlanModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Plan de Matrícula</h3>
            <div class="space-y-3">
              <input [(ngModel)]="planForm.name" placeholder="Nombre del plan" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              <input type="number" [(ngModel)]="planForm.total_amount" placeholder="Monto total" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              <select [(ngModel)]="planForm.program_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                <option value="">-- Programa --</option>
                @for (p of programs(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }
              </select>
              <select [(ngModel)]="planForm.academic_period_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                <option value="">-- Periodo --</option>
                @for (p of periods(); track p.id) { <option [value]="p.id">{{ p.name }}</option> }
              </select>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showPlanModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="savePlan()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }

      <!-- Charge Modal -->
      @if (showChargeModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showChargeModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Cobro</h3>
            <div class="space-y-3">
              <select [(ngModel)]="chargeForm.student_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                <option value="">-- Estudiante --</option>
                @for (s of students(); track s.id) { <option [value]="s.id">{{ s.student_code }} - {{ s.first_name }} {{ s.last_name }}</option> }
              </select>
              <input [(ngModel)]="chargeForm.description" placeholder="Descripción" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              <input type="number" [(ngModel)]="chargeForm.amount" placeholder="Monto" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showChargeModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="saveCharge()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }

      <!-- Scholarship Modal -->
      @if (showSchModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showSchModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Beca</h3>
            <div class="space-y-3">
              <input [(ngModel)]="schForm.name" placeholder="Nombre" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              <div class="grid grid-cols-2 gap-3">
                <select [(ngModel)]="schForm.type" class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="percentage">Porcentaje</option>
                  <option value="fixed">Monto fijo</option>
                </select>
                <input type="number" [(ngModel)]="schForm.value" placeholder="Valor" class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showSchModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="saveScholarship()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class EduFinanceComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  tuitionPlans = signal<any[]>([]);
  charges = signal<any[]>([]);
  scholarships = signal<any[]>([]);
  programs = signal<any[]>([]);
  periods = signal<any[]>([]);
  students = signal<any[]>([]);

  activeTab = 'plans';
  tabs = [
    { key: 'plans', label: 'Planes de Matrícula' },
    { key: 'charges', label: 'Cobros' },
    { key: 'scholarships', label: 'Becas' },
  ];

  showPlanModal = false;
  showChargeModal = false;
  showSchModal = false;

  planForm: any = { name: '', total_amount: 0, program_id: '', academic_period_id: '' };
  chargeForm: any = { student_id: '', description: '', amount: 0 };
  schForm: any = { name: '', type: 'percentage', value: 0 };

  ngOnInit(): void {
    this.loadAll();
    this.api.get<any[]>('/edu/structure/programs').subscribe({ next: (r) => this.programs.set(r) });
    this.api.get<any[]>('/edu/structure/periods').subscribe({ next: (r) => this.periods.set(r) });
    this.api.get<any>('/edu/students', { page_size: 500 }).subscribe({ next: (r) => this.students.set(r.items || []) });
  }

  loadAll(): void {
    this.api.get<any[]>('/edu/finance/tuition-plans').subscribe({ next: (r) => this.tuitionPlans.set(r) });
    this.api.get<any[]>('/edu/finance/charges').subscribe({ next: (r) => this.charges.set(r) });
    this.api.get<any[]>('/edu/finance/scholarships').subscribe({ next: (r) => this.scholarships.set(r) });
  }

  savePlan(): void {
    this.api.post('/edu/finance/tuition-plans', this.planForm).subscribe({
      next: () => { this.showPlanModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Plan creado' }); this.loadAll(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }

  saveCharge(): void {
    this.api.post('/edu/finance/charges', this.chargeForm).subscribe({
      next: () => { this.showChargeModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Cobro creado' }); this.loadAll(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }

  saveScholarship(): void {
    this.api.post('/edu/finance/scholarships', this.schForm).subscribe({
      next: () => { this.showSchModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Beca creada' }); this.loadAll(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }
}
