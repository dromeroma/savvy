import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HotelService, Reservation, AvailabilityRow, Room, Folio } from '../hotel.service';
import { NotificationService } from '../../../shared/services/notification.service';
import { ScanPrefillComponent } from '../../../shared/components/ai/scan-prefill.component';

@Component({
  selector: 'app-hotel-reservations',
  imports: [CommonModule, FormsModule, DecimalPipe, ScanPrefillComponent],
  template: `
    <div class="p-4 sm:p-6 lg:p-8 space-y-5">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">Reservas</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Disponibilidad, check-in/out y folio del huésped.</p>
        </div>
        <button (click)="openNew()" class="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium">➕ Nueva reserva</button>
      </div>

      <div class="flex flex-wrap gap-2">
        @for (f of filters; track f.value) {
          <button (click)="filter.set(f.value); load()" class="px-3 py-1.5 rounded-full text-xs border"
            [class]="filter() === f.value ? 'bg-brand-500 text-white border-brand-500' : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300'">{{ f.label }}</button>
        }
      </div>

      <div class="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-800/40 text-left text-xs uppercase text-gray-400"><tr>
            <th class="px-4 py-2">Código</th><th class="px-4 py-2">Huésped</th><th class="px-4 py-2">Tipo / Hab.</th>
            <th class="px-4 py-2">Entrada</th><th class="px-4 py-2">Salida</th><th class="px-4 py-2 text-right">Saldo</th><th class="px-4 py-2">Estado</th>
          </tr></thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
            @for (r of reservations(); track r.id) {
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30 cursor-pointer" (click)="openFolio(r)">
                <td class="px-4 py-2 font-mono text-xs text-gray-600 dark:text-gray-300">{{ r.code }}</td>
                <td class="px-4 py-2 text-gray-800 dark:text-white/90">{{ r.guest_name }}</td>
                <td class="px-4 py-2 text-gray-600 dark:text-gray-300">{{ r.room_type_name }}<span *ngIf="r.room_number"> · {{ r.room_number }}</span></td>
                <td class="px-4 py-2 text-gray-600 dark:text-gray-300">{{ r.check_in_date }}</td>
                <td class="px-4 py-2 text-gray-600 dark:text-gray-300">{{ r.check_out_date }}</td>
                <td class="px-4 py-2 text-right font-mono text-xs" [class.text-rose-600]="(r.folio_balance || 0) > 0">$ {{ (r.folio_balance || 0) | number:'1.0-0' }}</td>
                <td class="px-4 py-2"><span class="px-2 py-0.5 rounded-full text-xs" [ngClass]="statusClass(r.status)">{{ statusLabel(r.status) }}</span></td>
              </tr>
            } @empty { <tr><td colspan="7" class="px-4 py-10 text-center text-gray-400">Sin reservas.</td></tr> }
          </tbody>
        </table>
      </div>
    </div>

    <!-- Nueva reserva -->
    @if (newModal) {
      <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="newModal = false">
        <div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-2xl p-6 max-h-[92vh] overflow-y-auto" (click)="$event.stopPropagation()">
          <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva reserva</h3>

          <div class="grid grid-cols-2 gap-3 mb-3">
            <label class="block"><span class="text-xs text-gray-500">Entrada</span>
              <input type="date" [(ngModel)]="nf.check_in_date" (ngModelChange)="checkAvail()" class="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" /></label>
            <label class="block"><span class="text-xs text-gray-500">Salida</span>
              <input type="date" [(ngModel)]="nf.check_out_date" (ngModelChange)="checkAvail()" class="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" /></label>
          </div>

          @if (avail().length) {
            <div class="mb-3">
              <p class="text-xs text-gray-500 mb-1">Disponibilidad ({{ nights() }} noche(s)) — elige un tipo:</p>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                @for (a of avail(); track a.room_type_id) {
                  <button (click)="pickType(a)" [disabled]="a.available === 0"
                    class="text-left rounded-lg border p-3 disabled:opacity-40"
                    [class]="nf.room_type_id === a.room_type_id ? 'border-brand-500 ring-1 ring-brand-500' : 'border-gray-200 dark:border-gray-700'">
                    <div class="flex justify-between"><span class="font-medium text-gray-800 dark:text-white/90">{{ a.room_type_name }}</span>
                      <span class="text-xs" [class.text-emerald-600]="a.available > 0" [class.text-rose-600]="a.available === 0">{{ a.available }} libres</span></div>
                    <div class="text-xs text-gray-500">$ {{ a.base_rate | number:'1.0-0' }}/noche</div>
                  </button>
                }
              </div>
            </div>
          }

          <div class="flex items-center justify-between mb-2 mt-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-400">Huésped</h4>
            <app-scan-prefill prompt-key="extraction.id_card" target-app="hotel" document-type="id_card" label="Escanear documento" (prefill)="applyGuest($event)" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <input [(ngModel)]="nf.guest_name" placeholder="Nombre completo *" class="col-span-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
            <input [(ngModel)]="nf.guest_document" placeholder="Documento" class="rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
            <input [(ngModel)]="nf.guest_phone" placeholder="Teléfono" class="rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" />
            <div class="grid grid-cols-3 gap-2 col-span-2">
              <label class="block"><span class="text-xs text-gray-500">Adultos</span><input type="number" [(ngModel)]="nf.adults" class="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" /></label>
              <label class="block"><span class="text-xs text-gray-500">Niños</span><input type="number" [(ngModel)]="nf.children" class="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" /></label>
              <label class="block"><span class="text-xs text-gray-500">Tarifa/noche</span><input type="number" [(ngModel)]="nf.rate" class="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-white/90" /></label>
            </div>
          </div>

          <div class="flex items-center justify-between mt-5">
            <span class="text-sm text-gray-500">Total: <b class="text-gray-800 dark:text-white/90">$ {{ (nf.rate || 0) * nights() | number:'1.0-0' }}</b></span>
            <div class="flex gap-3">
              <button (click)="newModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="save()" [disabled]="saving()" class="px-4 py-2 text-sm rounded-lg bg-brand-600 text-white disabled:opacity-50">Crear reserva</button>
            </div>
          </div>
        </div>
      </div>
    }

    <!-- Folio / detalle -->
    @if (folioModal && current()) {
      <div class="fixed inset-0 z-50 flex items-center justify-end bg-black/40" (click)="folioModal = false">
        <div class="bg-white dark:bg-gray-900 shadow-xl w-full max-w-md h-full overflow-y-auto p-6" (click)="$event.stopPropagation()">
          <div class="flex justify-between items-start mb-1">
            <div><h3 class="text-lg font-bold text-gray-800 dark:text-white/90">{{ current()!.guest_name }}</h3>
              <p class="text-xs text-gray-400">{{ current()!.code }} · {{ current()!.room_type_name }}<span *ngIf="current()!.room_number"> · Hab. {{ current()!.room_number }}</span></p></div>
            <button (click)="folioModal = false" class="text-gray-400 text-xl">×</button>
          </div>
          <p class="text-xs text-gray-500 mb-4">{{ current()!.check_in_date }} → {{ current()!.check_out_date }} · {{ current()!.nights }} noche(s)</p>

          <!-- Acciones de estado -->
          <div class="flex flex-wrap gap-2 mb-4">
            @if (current()!.status === 'confirmed') {
              <button (click)="startCheckIn()" class="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs">Check-in</button>
              <button (click)="doCancel()" class="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 text-xs">Cancelar</button>
              <button (click)="doNoShow()" class="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 text-xs">No-show</button>
            }
            @if (current()!.status === 'checked_in') {
              <button (click)="doCheckOut()" class="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs">Check-out</button>
            }
            <span class="px-2 py-1 rounded-full text-xs" [ngClass]="statusClass(current()!.status)">{{ statusLabel(current()!.status) }}</span>
          </div>

          <!-- Asignar habitación para check-in -->
          @if (assigning()) {
            <div class="mb-4 rounded-lg border border-emerald-300 dark:border-emerald-800 p-3">
              <p class="text-xs text-gray-500 mb-2">Asigna una habitación libre:</p>
              <div class="flex flex-wrap gap-2">
                @for (rm of freeRooms(); track rm.id) {
                  <button (click)="confirmCheckIn(rm)" class="px-2 py-1 rounded border border-gray-300 dark:border-gray-700 text-xs text-gray-700 dark:text-gray-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20">{{ rm.number }}</button>
                } @empty { <span class="text-xs text-rose-600">No hay habitaciones libres de este tipo.</span> }
              </div>
            </div>
          }

          <!-- Folio -->
          @if (folio(); as fo) {
            <div class="rounded-xl border border-gray-200 dark:border-gray-800 p-4 mb-4">
              <div class="flex justify-between text-sm mb-2"><span class="text-gray-500">Cargos</span><span class="text-gray-800 dark:text-white/90">$ {{ fo.total_charges | number:'1.0-0' }}</span></div>
              <div class="flex justify-between text-sm mb-2"><span class="text-gray-500">Pagos</span><span class="text-gray-800 dark:text-white/90">$ {{ fo.total_payments | number:'1.0-0' }}</span></div>
              <div class="flex justify-between text-base font-bold border-t border-gray-100 dark:border-gray-800 pt-2"><span>Saldo</span><span [class.text-rose-600]="fo.balance > 0">$ {{ fo.balance | number:'1.0-0' }}</span></div>

              <div class="mt-3 space-y-1">
                @for (c of fo.charges; track c.id) {
                  <div class="flex justify-between text-xs text-gray-600 dark:text-gray-300"><span>{{ c.description }}</span><span>$ {{ c.amount | number:'1.0-0' }}</span></div>
                }
                @for (p of fo.payments; track p.id) {
                  <div class="flex justify-between text-xs text-emerald-600"><span>Pago ({{ p.method }})</span><span>- $ {{ p.amount | number:'1.0-0' }}</span></div>
                }
              </div>
            </div>

            @if (fo.status === 'open') {
              <div class="space-y-2">
                <div class="flex gap-2">
                  <input [(ngModel)]="chg.description" placeholder="Concepto" class="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-xs text-gray-800 dark:text-white/90" />
                  <input type="number" [(ngModel)]="chg.unit_price" placeholder="Valor" class="w-24 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-xs text-gray-800 dark:text-white/90" />
                  <button (click)="addCharge()" class="px-2 py-1.5 rounded-lg bg-gray-700 text-white text-xs">+ Cargo</button>
                </div>
                <div class="flex gap-2">
                  <input [(ngModel)]="posSaleId" placeholder="ID venta POS" class="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-xs text-gray-800 dark:text-white/90" />
                  <button (click)="chargePos()" class="px-2 py-1.5 rounded-lg bg-violet-600 text-white text-xs">Cargar POS</button>
                </div>
                <div class="flex gap-2">
                  <input type="number" [(ngModel)]="pay.amount" placeholder="Monto pago" class="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-xs text-gray-800 dark:text-white/90" />
                  <select [(ngModel)]="pay.method" class="rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-xs text-gray-800 dark:text-white/90">
                    <option value="cash">Efectivo</option><option value="card">Tarjeta</option><option value="transfer">Transf.</option>
                  </select>
                  <button (click)="addPayment()" class="px-2 py-1.5 rounded-lg bg-emerald-600 text-white text-xs">+ Pago</button>
                </div>
              </div>
            }
          }
        </div>
      </div>
    }
  `,
})
export class HotelReservationsComponent implements OnInit {
  private readonly hotel = inject(HotelService);
  private readonly notify = inject(NotificationService);

  reservations = signal<Reservation[]>([]);
  filter = signal<string>('');
  filters = [
    { label: 'Todas', value: '' }, { label: 'Confirmadas', value: 'confirmed' },
    { label: 'En casa', value: 'checked_in' }, { label: 'Check-out', value: 'checked_out' },
  ];

  newModal = false; saving = signal(false);
  avail = signal<AvailabilityRow[]>([]);
  nf: any = this.emptyNew();

  folioModal = false;
  current = signal<Reservation | null>(null);
  folio = signal<Folio | null>(null);
  assigning = signal(false);
  freeRooms = signal<Room[]>([]);
  chg: any = { description: '', unit_price: 0 };
  pay: any = { amount: 0, method: 'cash' };
  posSaleId = '';

  ngOnInit(): void { this.load(); }

  emptyNew() {
    const today = new Date().toISOString().slice(0, 10);
    const tmr = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
    return { check_in_date: today, check_out_date: tmr, room_type_id: '', guest_name: '', guest_document: '', guest_phone: '', adults: 1, children: 0, rate: 0, source: 'direct' };
  }
  nights(): number {
    const a = new Date(this.nf.check_in_date), b = new Date(this.nf.check_out_date);
    return Math.max(Math.round((b.getTime() - a.getTime()) / 86400000), 0);
  }

  load(): void {
    const p: Record<string, string> = {};
    if (this.filter()) p['status'] = this.filter();
    this.hotel.listReservations(p).subscribe({ next: (r) => this.reservations.set(r) });
  }

  openNew(): void { this.nf = this.emptyNew(); this.avail.set([]); this.newModal = true; this.checkAvail(); }
  checkAvail(): void {
    if (!this.nf.check_in_date || !this.nf.check_out_date || this.nights() < 1) { this.avail.set([]); return; }
    this.hotel.availability(this.nf.check_in_date, this.nf.check_out_date).subscribe({ next: (r) => this.avail.set(r.rows) });
  }
  pickType(a: AvailabilityRow): void { if (a.available > 0) { this.nf.room_type_id = a.room_type_id; if (!this.nf.rate) this.nf.rate = a.base_rate; } }
  applyGuest(data: Record<string, unknown>): void {
    const v = (k: string) => (data[k] == null ? '' : String(data[k]));
    const name = `${v('first_name')} ${v('last_name')}`.trim();
    if (name) this.nf.guest_name = name;
    if (v('document_number')) this.nf.guest_document = v('document_number');
    this.notify.show({ type: 'success', title: 'Documento leído', message: 'Revisa los datos del huésped.' });
  }
  save(): void {
    if (!this.nf.room_type_id) { this.notify.show({ type: 'error', title: 'Falta tipo', message: 'Elige un tipo disponible.' }); return; }
    if (!this.nf.guest_name?.trim()) { this.notify.show({ type: 'error', title: 'Falta huésped', message: 'Ingresa el nombre.' }); return; }
    this.saving.set(true);
    this.hotel.createReservation(this.nf).subscribe({
      next: () => { this.saving.set(false); this.newModal = false; this.load(); this.notify.show({ type: 'success', title: 'Reserva creada', message: this.nf.guest_name }); },
      error: (e) => { this.saving.set(false); this.notify.show({ type: 'error', title: 'No se pudo', message: e?.error?.detail || 'Error' }); },
    });
  }

  openFolio(r: Reservation): void {
    this.current.set(r); this.folio.set(null); this.assigning.set(false);
    this.chg = { description: '', unit_price: 0 }; this.pay = { amount: 0, method: 'cash' }; this.posSaleId = '';
    this.folioModal = true;
    this.hotel.getFolio(r.id).subscribe({ next: (f) => this.folio.set(f) });
  }
  refresh(): void {
    const r = this.current(); if (!r) return;
    this.hotel.getFolio(r.id).subscribe({ next: (f) => this.folio.set(f) });
    this.load();
  }

  startCheckIn(): void {
    const r = this.current(); if (!r) return;
    this.assigning.set(true);
    this.hotel.availableRooms(r.check_in_date, r.check_out_date, r.room_type_id).subscribe({ next: (rooms) => this.freeRooms.set(rooms) });
  }
  confirmCheckIn(rm: Room): void {
    const r = this.current(); if (!r) return;
    this.hotel.checkIn(r.id, rm.id).subscribe({
      next: (upd) => { this.current.set(upd); this.assigning.set(false); this.refresh(); this.notify.show({ type: 'success', title: 'Check-in', message: `Hab. ${rm.number}` }); },
      error: (e) => this.notify.show({ type: 'error', title: 'No se pudo', message: e?.error?.detail || 'Error' }),
    });
  }
  doCheckOut(): void {
    const r = this.current(); if (!r) return;
    this.hotel.checkOut(r.id).subscribe({ next: (upd) => { this.current.set(upd); this.refresh(); this.notify.show({ type: 'success', title: 'Check-out', message: 'Folio cerrado' }); } });
  }
  doCancel(): void { const r = this.current(); if (!r) return; this.hotel.cancel(r.id).subscribe({ next: (u) => { this.current.set(u); this.refresh(); } }); }
  doNoShow(): void { const r = this.current(); if (!r) return; this.hotel.noShow(r.id).subscribe({ next: (u) => { this.current.set(u); this.refresh(); } }); }

  addCharge(): void {
    const r = this.current(); if (!r || !this.chg.description || !this.chg.unit_price) return;
    this.hotel.addCharge(r.id, { description: this.chg.description, quantity: 1, unit_price: +this.chg.unit_price }).subscribe({
      next: (f) => { this.folio.set(f); this.chg = { description: '', unit_price: 0 }; this.load(); } });
  }
  chargePos(): void {
    const r = this.current(); if (!r || !this.posSaleId) return;
    this.hotel.chargeFromPos(r.id, this.posSaleId.trim()).subscribe({
      next: (f) => { this.folio.set(f); this.posSaleId = ''; this.load(); this.notify.show({ type: 'success', title: 'Consumo cargado', message: 'POS → folio' }); },
      error: (e) => this.notify.show({ type: 'error', title: 'No se pudo', message: e?.error?.detail || 'Error' }) });
  }
  addPayment(): void {
    const r = this.current(); if (!r || !this.pay.amount) return;
    this.hotel.addPayment(r.id, { amount: +this.pay.amount, method: this.pay.method }).subscribe({
      next: (f) => { this.folio.set(f); this.pay = { amount: 0, method: 'cash' }; this.load(); } });
  }

  statusClass(s: string): string {
    return { confirmed: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300',
      checked_in: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
      checked_out: 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
      cancelled: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300',
      no_show: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' }[s] || 'bg-gray-100 text-gray-600';
  }
  statusLabel(s: string): string {
    return { confirmed: 'Confirmada', checked_in: 'En casa', checked_out: 'Check-out', cancelled: 'Cancelada', no_show: 'No-show' }[s] || s;
  }
}
