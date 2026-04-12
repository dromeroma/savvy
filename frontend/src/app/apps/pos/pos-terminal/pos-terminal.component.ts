import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

interface CartLine {
  product_id: string;
  name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  discount: number;
}

@Component({
  selector: 'app-pos-terminal',
  imports: [CommonModule, FormsModule],
  template: `
    <div class="h-[calc(100vh-120px)] flex flex-col lg:flex-row gap-4">
      <!-- Products panel -->
      <div class="lg:w-2/3 flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 overflow-hidden">
        <div class="flex gap-3 mb-4">
          <input [(ngModel)]="search" (ngModelChange)="loadProducts()" placeholder="Buscar producto, SKU, codigo de barras..." class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
          <select [(ngModel)]="selectedLocation" class="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
            @for (l of locations(); track l.id) { <option [value]="l.id">{{ l.name }}</option> }
          </select>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            @for (p of products(); track p.id) {
              <button (click)="addToCart(p)" class="flex flex-col items-center gap-1 p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-brand-50 dark:hover:bg-brand-900/20 hover:border-brand-400 transition text-center">
                <span class="text-2xl">📦</span>
                <span class="text-xs font-medium text-gray-800 dark:text-white/90 line-clamp-2">{{ p.name }}</span>
                <span class="text-sm font-bold text-green-600 dark:text-green-400">$ {{ p.price | number:'1.0-0' }}</span>
                <span class="text-xs text-gray-400">{{ p.sku }}</span>
              </button>
            }
            @if (products().length === 0) { <p class="col-span-full text-sm text-gray-400 text-center py-8">No hay productos</p> }
          </div>
        </div>
      </div>

      <!-- Cart panel -->
      <div class="lg:w-1/3 flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Carrito ({{ cart().length }})</h3>
        <div class="flex-1 overflow-y-auto custom-scrollbar space-y-2 mb-4">
          @for (line of cart(); track line.product_id; let i = $index) {
            <div class="flex items-center gap-2 p-2 rounded-lg border border-gray-200 dark:border-gray-700">
              <div class="flex-1 min-w-0"><p class="text-sm font-medium text-gray-800 dark:text-white/90 truncate">{{ line.name }}</p><p class="text-xs text-gray-500">$ {{ line.unit_price | number:'1.0-0' }} x {{ line.quantity }}</p></div>
              <input type="number" [(ngModel)]="line.quantity" min="1" class="w-14 text-center rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-1 py-1 text-sm" />
              <button (click)="removeLine(i)" class="text-red-500 hover:text-red-700 text-sm">✕</button>
            </div>
          }
          @if (cart().length === 0) { <p class="text-sm text-gray-400 text-center py-8">Sin productos</p> }
        </div>
        <div class="border-t border-gray-200 dark:border-gray-700 pt-3 space-y-2">
          <div class="flex justify-between text-sm text-gray-600 dark:text-gray-400"><span>Subtotal</span><span>$ {{ subtotal() | number:'1.0-0' }}</span></div>
          <div class="flex justify-between text-lg font-bold text-gray-800 dark:text-white/90"><span>Total</span><span>$ {{ total() | number:'1.0-0' }}</span></div>
          <div><label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Metodo de pago</label><select [(ngModel)]="paymentMethod" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="cash">Efectivo</option><option value="card">Tarjeta</option><option value="bank_transfer">Transferencia</option><option value="credit">Credito</option></select></div>
          <button (click)="checkout()" [disabled]="cart().length === 0" class="w-full px-4 py-3 text-sm font-bold rounded-lg bg-green-600 text-white hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed">Cobrar $ {{ total() | number:'1.0-0' }}</button>
        </div>
      </div>
    </div>
  `,
})
export class PosTerminalComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  products = signal<any[]>([]);
  cart = signal<CartLine[]>([]);
  locations = signal<any[]>([]);
  selectedLocation = '';
  search = '';
  paymentMethod = 'cash';

  subtotal = computed(() => this.cart().reduce((s, l) => s + l.unit_price * l.quantity - l.discount, 0));
  total = computed(() => this.subtotal());

  ngOnInit(): void {
    this.api.get<any[]>('/pos/locations').subscribe({
      next: (r) => { this.locations.set(r); if (r.length) this.selectedLocation = r[0].id; }
    });
    this.loadProducts();
  }

  loadProducts(): void {
    const p: any = { page_size: 50 };
    if (this.search) p.search = this.search;
    this.api.get<any>('/pos/products', p).subscribe({ next: (r) => this.products.set(r.items || []) });
  }

  addToCart(p: any): void {
    const existing = this.cart().find(l => l.product_id === p.id);
    if (existing) {
      existing.quantity += 1;
      this.cart.set([...this.cart()]);
    } else {
      this.cart.set([...this.cart(), { product_id: p.id, name: p.name, sku: p.sku, quantity: 1, unit_price: Number(p.price), discount: 0 }]);
    }
  }

  removeLine(i: number): void {
    const c = [...this.cart()];
    c.splice(i, 1);
    this.cart.set(c);
  }

  checkout(): void {
    if (!this.selectedLocation) {
      this.notify.show({ type: 'error', title: 'Error', message: 'Selecciona una sucursal' });
      return;
    }
    const payload = {
      location_id: this.selectedLocation,
      payment_method: this.paymentMethod,
      lines: this.cart().map(l => ({
        product_id: l.product_id, quantity: l.quantity, unit_price: l.unit_price, discount: l.discount,
      })),
    };
    this.api.post('/pos/sales', payload).subscribe({
      next: (r: any) => {
        this.notify.show({ type: 'success', title: 'Venta completada', message: `${r.sale_number} — $ ${r.total}` });
        this.cart.set([]);
      },
      error: (e: any) => this.notify.show({ type: 'error', title: 'Error', message: e?.error?.detail || 'No se pudo completar la venta' }),
    });
  }
}
