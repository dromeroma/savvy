import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pos-products',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Productos</h2><p class="text-sm text-gray-500 dark:text-gray-400">Catalogo de productos</p></div>
        <button (click)="showModal = true" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">+ Nuevo Producto</button>
      </div>
      <div class="mb-4"><input [(ngModel)]="search" (ngModelChange)="load()" placeholder="Buscar..." class="w-full sm:w-80 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">SKU</th><th class="px-4 py-3 font-medium text-gray-500">Nombre</th><th class="px-4 py-3 font-medium text-gray-500">Tipo</th><th class="px-4 py-3 font-medium text-gray-500">Precio</th><th class="px-4 py-3 font-medium text-gray-500">Costo</th><th class="px-4 py-3 font-medium text-gray-500">Estado</th></tr></thead>
        <tbody>@for (p of products(); track p.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50">
            <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ p.sku }}</td>
            <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ p.name }}</td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ p.product_type }}</td>
            <td class="px-4 py-3 font-mono text-green-600 dark:text-green-400">$ {{ p.price | number:'1.0-0' }}</td>
            <td class="px-4 py-3 font-mono text-gray-500">$ {{ p.cost | number:'1.0-0' }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">{{ p.status }}</span></td>
          </tr>
        }</tbody></table></div>
        @if (products().length === 0) { <p class="text-sm text-gray-400 text-center py-8">No hay productos</p> }
      </div>
      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nuevo Producto</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-3 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">SKU</label><input [(ngModel)]="form.sku" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div class="col-span-2"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre</label><input [(ngModel)]="form.name" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
              <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Codigo de barras</label><input [(ngModel)]="form.barcode" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div>
              <div class="grid grid-cols-3 gap-3"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select [(ngModel)]="form.product_type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"><option value="simple">Simple</option><option value="variant">Con variantes</option><option value="bundle">Combo</option><option value="service">Servicio</option></select></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Precio</label><input type="number" [(ngModel)]="form.price" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Costo</label><input type="number" [(ngModel)]="form.cost" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" /></div></div>
            </div>
            <div class="flex justify-end gap-3 mt-6"><button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button><button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button></div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PosProductsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  products = signal<any[]>([]); showModal = false; search = '';
  form: any = { sku: '', name: '', barcode: '', product_type: 'simple', price: 0, cost: 0 };
  ngOnInit(): void { this.load(); }
  load(): void { const p: any = { page_size: 100 }; if (this.search) p.search = this.search; this.api.get<any>('/pos/products', p).subscribe({ next: (r) => this.products.set(r.items || []) }); }
  save(): void { this.api.post('/pos/products', this.form).subscribe({ next: () => { this.showModal = false; this.notify.show({ type: 'success', title: 'Listo', message: 'Producto creado' }); this.load(); }, error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }) }); }
}
