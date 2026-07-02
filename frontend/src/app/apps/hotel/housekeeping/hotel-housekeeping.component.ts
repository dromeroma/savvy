import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HotelService, Room } from '../hotel.service';

@Component({
  selector: 'app-hotel-housekeeping',
  imports: [CommonModule],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">Housekeeping</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">Estado de limpieza de cada habitación. Toca para cambiarlo.</p>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        @for (r of rooms(); track r.id) {
          <div class="rounded-xl border p-4 text-center" [ngClass]="border(r.housekeeping_status)">
            <div class="text-lg font-bold text-gray-800 dark:text-white/90">{{ r.number }}</div>
            <div class="text-xs text-gray-400 mb-2">{{ r.room_type_name }}</div>
            <div class="text-xs font-medium mb-2" [ngClass]="text(r.housekeeping_status)">{{ label(r.housekeeping_status) }}</div>
            <div class="flex flex-wrap gap-1 justify-center">
              @for (s of states; track s) {
                <button (click)="setState(r, s)" [disabled]="r.housekeeping_status === s"
                  class="px-1.5 py-0.5 rounded text-[10px] border border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800">{{ label(s) }}</button>
              }
            </div>
          </div>
        } @empty { <p class="text-sm text-gray-400 col-span-full">Sin habitaciones.</p> }
      </div>
    </div>
  `,
})
export class HotelHousekeepingComponent implements OnInit {
  private readonly hotel = inject(HotelService);
  rooms = signal<Room[]>([]);
  states = ['clean', 'dirty', 'cleaning', 'inspected'];
  ngOnInit(): void { this.load(); }
  load(): void { this.hotel.listRooms().subscribe({ next: (r) => this.rooms.set(r) }); }
  setState(r: Room, s: string): void { this.hotel.setHousekeeping(r.id, s).subscribe({ next: () => this.load() }); }
  label(s: string): string { return { clean: 'Limpia', dirty: 'Sucia', cleaning: 'Limpiando', inspected: 'Inspeccionada' }[s] || s; }
  border(s: string): string {
    return { clean: 'border-emerald-300 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10',
      dirty: 'border-rose-300 dark:border-rose-800 bg-rose-50/50 dark:bg-rose-900/10',
      cleaning: 'border-sky-300 dark:border-sky-800 bg-sky-50/50 dark:bg-sky-900/10',
      inspected: 'border-violet-300 dark:border-violet-800 bg-violet-50/50 dark:bg-violet-900/10' }[s] || 'border-gray-200 dark:border-gray-800';
  }
  text(s: string): string {
    return { clean: 'text-emerald-600 dark:text-emerald-400', dirty: 'text-rose-600 dark:text-rose-400',
      cleaning: 'text-sky-600 dark:text-sky-400', inspected: 'text-violet-600 dark:text-violet-400' }[s] || 'text-gray-500';
  }
}
