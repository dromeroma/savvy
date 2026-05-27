import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  InventoryItem,
  InventoryItemCreate,
  InventoryItemListItem,
  InventoryMovementCreate,
  InventoryMovementListItem,
  ItemCategory,
  MovementType,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

type Tab = 'items' | 'movements';

@Component({
  selector: 'app-memorial-inventory',
  imports: [CommonModule, FormsModule, PaginationComponent],
  templateUrl: './inventory.component.html',
})
export class MemorialInventoryComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  tab = signal<Tab>('items');
  loading = signal(false);

  items = signal<InventoryItemListItem[]>([]);
  movements = signal<InventoryMovementListItem[]>([]);

  itemsPage = signal(0);
  itemsPageSize = signal(20);
  paginatedItems = computed(() => {
    const s = this.itemsPage() * this.itemsPageSize();
    return this.items().slice(s, s + this.itemsPageSize());
  });

  movPage = signal(0);
  movPageSize = signal(20);
  paginatedMovements = computed(() => {
    const s = this.movPage() * this.movPageSize();
    return this.movements().slice(s, s + this.movPageSize());
  });

  constructor() {
    effect(() => { this.items(); this.itemsPage.set(0); }, { allowSignalWrites: true });
    effect(() => { this.movements(); this.movPage.set(0); }, { allowSignalWrites: true });
  }

  // Filtros items
  filterCategory: ItemCategory | '' = '';
  lowStockOnly = false;
  searchItems = '';
  private searchTimer: any;

  // Item form
  itemFormOpen = signal(false);
  editingItemId = signal<string | null>(null);
  itemForm: InventoryItemCreate = this.emptyItem();
  savingItem = signal(false);
  itemFormError = signal('');

  // Movement form
  movFormOpen = signal(false);
  movForm: InventoryMovementCreate = this.emptyMov();
  savingMov = signal(false);
  movFormError = signal('');

  readonly categories: { value: ItemCategory; label: string }[] = [
    { value: 'casket', label: 'Ataúdes' },
    { value: 'urn', label: 'Urnas' },
    { value: 'flowers', label: 'Flores' },
    { value: 'supplies', label: 'Insumos generales' },
    { value: 'vehicle_supplies', label: 'Insumos vehículos' },
    { value: 'other', label: 'Otros' },
  ];

  readonly movTypes: { value: MovementType; label: string }[] = [
    { value: 'entry', label: 'Entrada' },
    { value: 'exit', label: 'Salida' },
    { value: 'adjustment', label: 'Ajuste (set absoluto)' },
    { value: 'transfer_in', label: 'Transferencia entrante' },
    { value: 'transfer_out', label: 'Transferencia saliente' },
  ];

  ngOnInit(): void { this.load(); }

  setTab(t: Tab): void {
    if (this.tab() === t) return;
    this.tab.set(t);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    if (this.tab() === 'items') {
      this.memorial.listInventoryItems({
        category: this.filterCategory || undefined,
        low_stock_only: this.lowStockOnly || undefined,
        search: this.searchItems || undefined,
      }).subscribe({
        next: (d) => { this.items.set(d); this.loading.set(false); },
        error: () => this.loading.set(false),
      });
    } else {
      this.memorial.listInventoryMovements().subscribe({
        next: (d) => { this.movements.set(d); this.loading.set(false); },
        error: () => this.loading.set(false),
      });
    }
  }

  onSearchChange(): void {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.load(), 300);
  }

  // ----------- Items
  openCreateItem(): void {
    this.editingItemId.set(null);
    this.itemForm = this.emptyItem();
    this.itemFormError.set('');
    this.itemFormOpen.set(true);
  }
  openEditItem(item: InventoryItemListItem): void {
    this.memorial.getInventoryItem(item.id).subscribe({
      next: (full) => {
        this.editingItemId.set(full.id);
        this.itemForm = {
          code: full.code, name: full.name, category: full.category as ItemCategory,
          description: full.description, unit: full.unit,
          min_stock: full.min_stock, max_stock: full.max_stock,
          unit_cost: full.unit_cost, sale_price: full.sale_price,
          is_active: full.is_active, notes: full.notes,
        };
        this.itemFormOpen.set(true);
      },
    });
  }
  closeItemForm(): void { this.itemFormOpen.set(false); }

  submitItem(): void {
    if (!this.itemForm.code || !this.itemForm.name || !this.itemForm.category) {
      this.itemFormError.set('Código, nombre y categoría son obligatorios.');
      return;
    }
    this.savingItem.set(true);
    this.itemFormError.set('');
    const id = this.editingItemId();
    const obs = id
      ? this.memorial.updateInventoryItem(id, this.stripImmutableItem(this.itemForm))
      : this.memorial.createInventoryItem(this.itemForm);
    obs.subscribe({
      next: (r) => {
        this.savingItem.set(false);
        this.closeItemForm();
        this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: r.name });
        this.load();
      },
      error: (err) => {
        this.savingItem.set(false);
        const detail = err?.error?.detail;
        this.itemFormError.set(typeof detail === 'string' ? detail : 'Error al guardar.');
      },
    });
  }

  confirmDeleteItem(item: InventoryItemListItem): void {
    if (!confirm(`¿Eliminar ${item.name}?`)) return;
    this.memorial.deleteInventoryItem(item.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: item.name }); this.load(); },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo eliminar.',
      }),
    });
  }

  // ----------- Movements
  openCreateMov(itemId?: string): void {
    this.movForm = this.emptyMov();
    if (itemId) this.movForm.item_id = itemId;
    this.movFormError.set('');
    this.movFormOpen.set(true);
  }
  closeMovForm(): void { this.movFormOpen.set(false); }

  submitMov(): void {
    if (!this.movForm.item_id || !this.movForm.movement_type || !this.movForm.quantity) {
      this.movFormError.set('Item, tipo y cantidad son obligatorios.');
      return;
    }
    this.savingMov.set(true);
    this.movFormError.set('');
    this.memorial.recordInventoryMovement(this.movForm).subscribe({
      next: (m) => {
        this.savingMov.set(false);
        this.closeMovForm();
        this.notify.show({ type: 'success', title: 'Movimiento registrado', message: m.code });
        if (this.tab() === 'movements') this.load();
        else { /* refrescar items para ver stock actualizado */ this.tab.set('items'); this.load(); }
      },
      error: (err) => {
        this.savingMov.set(false);
        const detail = err?.error?.detail;
        this.movFormError.set(typeof detail === 'string' ? detail : 'Error al registrar.');
      },
    });
  }

  // ----------- Labels
  categoryLabel(c: string): string {
    return this.categories.find(x => x.value === c)?.label || c;
  }
  movTypeLabel(t: string): string {
    return this.movTypes.find(x => x.value === t)?.label || t;
  }
  movTypeBadge(t: string): string {
    switch (t) {
      case 'entry': case 'transfer_in':
        return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'exit': case 'transfer_out':
        return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'adjustment':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  }

  private emptyItem(): InventoryItemCreate {
    return {
      code: '', name: '', category: 'casket',
      unit: 'unidad',
      min_stock: 0, unit_cost: 0, sale_price: 0,
      initial_stock: 0, is_active: true,
    };
  }

  private emptyMov(): InventoryMovementCreate {
    return {
      item_id: '', movement_type: 'entry', quantity: 1,
      movement_date: new Date().toISOString().slice(0, 10),
    };
  }

  private stripImmutableItem(data: InventoryItemCreate): Partial<InventoryItemCreate> {
    const { code, category, initial_stock, ...rest } = data;
    return rest;
  }
}
