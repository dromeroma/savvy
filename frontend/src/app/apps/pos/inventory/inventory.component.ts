import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-pos-inventory',
  imports: [CommonModule],
  template: `
    <div>
      <div class="mb-6"><h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Inventario</h2><p class="text-sm text-gray-500 dark:text-gray-400">Stock por producto y sucursal</p></div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar"><table class="w-full text-sm"><thead><tr class="border-b border-gray-200 dark:border-gray-700 text-left"><th class="px-4 py-3 font-medium text-gray-500">Producto</th><th class="px-4 py-3 font-medium text-gray-500">Sucursal</th><th class="px-4 py-3 font-medium text-gray-500 text-right">Cantidad</th><th class="px-4 py-3 font-medium text-gray-500 text-right">Min Stock</th></tr></thead>
        <tbody>@for (i of inventory(); track i.id) {
          <tr class="border-b border-gray-100 dark:border-gray-700/50"><td class="px-4 py-3 font-mono text-xs text-gray-500">{{ i.product_id | slice:0:8 }}</td><td class="px-4 py-3 font-mono text-xs text-gray-500">{{ i.location_id | slice:0:8 }}</td><td class="px-4 py-3 font-mono text-right text-gray-800 dark:text-white/90" [class.text-red-600]="i.quantity <= i.min_stock">{{ i.quantity }}</td><td class="px-4 py-3 font-mono text-right text-gray-500">{{ i.min_stock }}</td></tr>
        }</tbody></table></div>
        @if (inventory().length === 0) { <p class="text-sm text-gray-400 text-center py-8">Sin stock registrado</p> }
      </div>
    </div>
  `,
})
export class PosInventoryComponent implements OnInit {
  private readonly api = inject(ApiService);
  inventory = signal<any[]>([]);
  ngOnInit(): void { this.api.get<any[]>('/pos/inventory').subscribe({ next: (r) => this.inventory.set(r) }); }
}
