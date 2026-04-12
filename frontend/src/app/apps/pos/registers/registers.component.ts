import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pos-registers',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Cajas</h2><p class="text-sm text-gray-500 dark:text-gray-400">Apertura y cierre de caja</p></div>
        <button (click)="showOpenModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Abrir Caja</button>
      </div>
      <div class="space-y-3">
        @for (r of registers(); track r.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ r.register_name }}</h4>
                <div class="flex gap-3 text-xs text-gray-500 mt-1">
                  <span>Apertura: $ {{ r.opening_balance | number:'1.0-0' }}</span>
                  @if (r.closing_balance !== null) { <span>Cierre: $ {{ r.closing_balance | number:'1.0-0' }}</span> }
                  @if (r.difference !== null) { <span [class]="r.difference === 0 ? 'text-green-600' : r.difference < 0 ? 'text-red-600' : 'text-orange-600'">Diferencia: $ {{ r.difference | number:'1.0-0' }}</span> }
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="px-2 py-1 text-xs rounded-full" [class]="r.status === 'open' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600'">{{ r.status === 'open' ? 'Abierta' : 'Cerrada' }}</span>
                @if (r.status === 'open') { <button (click)="openCloseModal(r)" class="px-3 py-1 text-xs font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition">Cerrar</button> }
              </div>
            </div>
          </div>
        }
        @if (registers().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay cajas</p> }
      </div>
      @if (showOpenModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showOpenModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Abrir Caja</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Sucursal</label><select [(ngModel)]="openForm.location_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">@for (l of locations(); track l.id) { <option [value]="l.id">{{ l.name }}</option> }</select></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre caja</label><input [(ngModel)]="openForm.register_name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Saldo apertura</label><input type="number" [(ngModel)]="openForm.opening_balance" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showOpenModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="openRegister()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Abrir</button></div>
          </div>
        </div>
      }
      @if (showCloseModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showCloseModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Cerrar Caja</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Saldo final (conteo fisico)</label><input type="number" [(ngModel)]="closeForm.closing_balance" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notas</label><textarea [(ngModel)]="closeForm.notes" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showCloseModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="closeRegister()" class="px-4 py-2 text-sm font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition">Cerrar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PosRegistersComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  registers = signal<any[]>([]); locations = signal<any[]>([]);
  showOpenModal = false; showCloseModal = false; closingReg: any = null;
  openForm: any = { location_id: '', register_name: 'Caja 1', opening_balance: 0 };
  closeForm: any = { closing_balance: 0, notes: '' };
  ngOnInit(): void { this.load(); this.api.get<any[]>('/pos/locations').subscribe({ next: (r) => { this.locations.set(r); if (r.length) this.openForm.location_id = r[0].id; } }); }
  load(): void { this.api.get<any[]>('/pos/registers').subscribe({ next: (r) => this.registers.set(r) }); }
  openRegister(): void { this.api.post('/pos/registers/open', this.openForm).subscribe({ next: () => { this.showOpenModal = false; this.notify.show({ type: 'success', title: 'Abierta', message: 'Caja abierta' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo abrir' }) }); }
  openCloseModal(r: any): void { this.closingReg = r; this.closeForm = { closing_balance: 0, notes: '' }; this.showCloseModal = true; }
  closeRegister(): void { this.api.post(`/pos/registers/${this.closingReg.id}/close`, this.closeForm).subscribe({ next: (r: any) => { this.showCloseModal = false; this.notify.show({ type: 'success', title: 'Cerrada', message: `Diferencia: $ ${r.difference}` }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cerrar' }) }); }
}
