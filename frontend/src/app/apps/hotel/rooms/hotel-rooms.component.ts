import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HotelService, Room, RoomType } from '../hotel.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-hotel-rooms',
  imports: [CommonModule, FormsModule, DecimalPipe],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-8">
      <!-- Tipos -->
      <section>
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Tipos de habitación</h2>
          <button (click)="typeModal = true" class="px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm">+ Tipo</button>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          @for (t of types(); track t.id) {
            <div class="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4">
              <div class="flex justify-between"><span class="font-medium text-gray-800 dark:text-white/90">{{ t.name }}</span><span class="text-xs text-gray-400">{{ t.code }}</span></div>
              <p class="text-sm text-gray-500 mt-1">Capacidad {{ t.capacity }} · $ {{ t.base_rate | number:'1.0-0' }}/noche</p>
            </div>
          } @empty { <p class="text-sm text-gray-400">Aún no hay tipos. Crea el primero.</p> }
        </div>
      </section>

      <!-- Habitaciones -->
      <section>
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Habitaciones</h2>
          <button (click)="openRoom()" [disabled]="types().length === 0" class="px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-sm">+ Habitación</button>
        </div>
        <div class="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800/40 text-left text-xs uppercase text-gray-400"><tr>
              <th class="px-4 py-2">N°</th><th class="px-4 py-2">Tipo</th><th class="px-4 py-2">Piso</th><th class="px-4 py-2">Estado</th><th class="px-4 py-2">Limpieza</th>
            </tr></thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
              @for (r of rooms(); track r.id) {
                <tr>
                  <td class="px-4 py-2 font-medium text-gray-800 dark:text-white/90">{{ r.number }}</td>
                  <td class="px-4 py-2 text-gray-600 dark:text-gray-300">{{ r.room_type_name }}</td>
                  <td class="px-4 py-2 text-gray-500">{{ r.floor || '—' }}</td>
                  <td class="px-4 py-2"><span class="px-2 py-0.5 rounded-full text-xs" [ngClass]="statusClass(r.status)">{{ r.status }}</span></td>
                  <td class="px-4 py-2"><span class="px-2 py-0.5 rounded-full text-xs" [ngClass]="hkClass(r.housekeeping_status)">{{ r.housekeeping_status }}</span></td>
                </tr>
              } @empty { <tr><td colspan="5" class="px-4 py-8 text-center text-gray-400">Sin habitaciones.</td></tr> }
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <!-- Modal tipo -->
    @if (typeModal) {
      <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="typeModal = false">
        <div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
          <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo tipo</h3>
          <div class="space-y-3">
            <input [(ngModel)]="tf.code" placeholder="Código (STD, SUITE)" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
            <input [(ngModel)]="tf.name" placeholder="Nombre (Doble estándar)" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
            <div class="grid grid-cols-2 gap-3">
              <input type="number" [(ngModel)]="tf.capacity" placeholder="Capacidad" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
              <input type="number" [(ngModel)]="tf.base_rate" placeholder="Tarifa/noche" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-5">
            <button (click)="typeModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300">Cancelar</button>
            <button (click)="saveType()" class="px-4 py-2 text-sm rounded-lg bg-brand-600 text-white">Guardar</button>
          </div>
        </div>
      </div>
    }

    <!-- Modal habitación -->
    @if (roomModal) {
      <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="roomModal = false">
        <div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
          <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva habitación</h3>
          <div class="space-y-3">
            <select [(ngModel)]="rf.room_type_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90">
              <option value="">— Tipo —</option>
              @for (t of types(); track t.id) { <option [value]="t.id">{{ t.name }}</option> }
            </select>
            <div class="grid grid-cols-2 gap-3">
              <input [(ngModel)]="rf.number" placeholder="Número (101)" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
              <input [(ngModel)]="rf.floor" placeholder="Piso" class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-5">
            <button (click)="roomModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300">Cancelar</button>
            <button (click)="saveRoom()" class="px-4 py-2 text-sm rounded-lg bg-brand-600 text-white">Guardar</button>
          </div>
        </div>
      </div>
    }
  `,
})
export class HotelRoomsComponent implements OnInit {
  private readonly hotel = inject(HotelService);
  private readonly notify = inject(NotificationService);
  types = signal<RoomType[]>([]);
  rooms = signal<Room[]>([]);
  typeModal = false; roomModal = false;
  tf: any = { code: '', name: '', capacity: 2, base_rate: 0 };
  rf: any = { room_type_id: '', number: '', floor: '' };

  ngOnInit(): void { this.load(); }
  load(): void {
    this.hotel.listRoomTypes().subscribe({ next: (r) => this.types.set(r) });
    this.hotel.listRooms().subscribe({ next: (r) => this.rooms.set(r) });
  }
  saveType(): void {
    if (!this.tf.code || !this.tf.name) { this.notify.show({ type: 'error', title: 'Faltan datos', message: 'Código y nombre.' }); return; }
    this.hotel.createRoomType(this.tf).subscribe({ next: () => { this.typeModal = false; this.tf = { code: '', name: '', capacity: 2, base_rate: 0 }; this.load(); } });
  }
  openRoom(): void { this.rf = { room_type_id: '', number: '', floor: '' }; this.roomModal = true; }
  saveRoom(): void {
    if (!this.rf.room_type_id || !this.rf.number) { this.notify.show({ type: 'error', title: 'Faltan datos', message: 'Tipo y número.' }); return; }
    this.hotel.createRoom(this.rf).subscribe({ next: () => { this.roomModal = false; this.load(); } });
  }
  statusClass(s: string): string {
    return { available: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
      occupied: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      maintenance: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
      blocked: 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300' }[s] || 'bg-gray-100 text-gray-600';
  }
  hkClass(s: string): string {
    return { clean: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
      dirty: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300',
      cleaning: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300',
      inspected: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300' }[s] || 'bg-gray-100 text-gray-600';
  }
}
