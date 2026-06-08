import { Component, computed, HostListener, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

interface CommandItem {
  label: string;
  hint: string;
  icon: string;
  route: string;
  keywords?: string;
}

/**
 * Savvy Command (⌘K) — la barra mágica global.
 * Fase 1: navegación instantánea + acceso directo a SavvyScan.
 * Fase 2 sumará lenguaje natural (Copilot) y búsqueda universal cross-módulo.
 */
@Component({
  selector: 'app-savvy-command',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <!-- Trigger (en el header) -->
    <button type="button" (click)="open()"
      class="hidden md:flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 px-3 py-1.5 text-sm text-slate-400 hover:border-brand-300 dark:hover:border-brand-700 transition">
      <span>✨ Buscar o ejecutar…</span>
      <kbd class="text-[10px] font-sans px-1.5 py-0.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900">⌘K</kbd>
    </button>

    @if (isOpen()) {
      <div class="fixed inset-0 z-[100] flex items-start justify-center pt-[12vh] px-4 bg-slate-900/40 backdrop-blur-sm"
        (click)="$event.target === $event.currentTarget && close()">
        <div class="w-full max-w-xl rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden"
          (drop)="onDrop($event)" (dragover)="$event.preventDefault()">
          <!-- Input -->
          <div class="flex items-center gap-3 px-4 py-3 border-b border-slate-100 dark:border-slate-800">
            <span class="text-violet-500 text-lg">✨</span>
            <input #cmdInput [(ngModel)]="query" (ngModelChange)="onQuery()" (keydown)="onKey($event)"
              placeholder="Busca un módulo, una acción… o arrastra una factura aquí"
              class="flex-1 bg-transparent outline-none text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400" />
            <kbd class="text-[10px] font-sans px-1.5 py-0.5 rounded border border-slate-300 dark:border-slate-600 text-slate-400">esc</kbd>
          </div>

          <!-- Resultados -->
          <ul class="max-h-80 overflow-y-auto py-2">
            @for (item of filtered(); track item.route; let i = $index) {
              <li>
                <button type="button" (click)="go(item)" (mouseenter)="highlight.set(i)"
                  class="w-full flex items-center gap-3 px-4 py-2.5 text-left"
                  [class.bg-brand-50]="highlight() === i"
                  [class.dark:bg-brand-500/10]="highlight() === i">
                  <span class="text-lg w-6 text-center shrink-0">{{ item.icon }}</span>
                  <span class="flex-1 min-w-0">
                    <span class="block text-sm font-medium text-slate-900 dark:text-slate-100 truncate">{{ item.label }}</span>
                    <span class="block text-xs text-slate-400 truncate">{{ item.hint }}</span>
                  </span>
                  @if (highlight() === i) { <span class="text-xs text-slate-400">↵</span> }
                </button>
              </li>
            } @empty {
              <li class="px-4 py-6 text-center text-sm text-slate-400">Sin coincidencias.</li>
            }
          </ul>

          <div class="px-4 py-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>↑↓ navegar · ↵ abrir · esc cerrar</span>
            <span class="text-violet-500">Savvy Command</span>
          </div>
        </div>
      </div>
    }
  `,
})
export class SavvyCommandComponent {
  private readonly router = inject(Router);

  isOpen = signal(false);
  query = '';
  highlight = signal(0);

  private readonly commands: CommandItem[] = [
    { label: 'Escanear factura de compra', hint: 'SavvyScan → actualiza inventario (POS)', icon: '✨', route: '/pos/scan', keywords: 'ia ai ocr factura compra inventario stock' },
    { label: 'Inicio', hint: 'Cuadro de mando general', icon: '🏠', route: '/dashboard', keywords: 'home dashboard inicio' },
    { label: 'POS · Terminal', hint: 'Punto de venta', icon: '🛒', route: '/pos/terminal', keywords: 'pos venta caja terminal' },
    { label: 'POS · Inventario', hint: 'Stock por producto', icon: '📦', route: '/pos/inventory', keywords: 'inventario stock pos' },
    { label: 'POS · Productos', hint: 'Catálogo', icon: '🏷️', route: '/pos/products', keywords: 'productos catalogo pos' },
    { label: 'Talento Humano', hint: 'SavvyHR', icon: '👥', route: '/hr/dashboard', keywords: 'hr rrhh empleados nomina' },
    { label: 'HR · Liquidaciones', hint: 'Cese de contrato', icon: '🧾', route: '/hr/liquidations', keywords: 'liquidacion hr despido' },
    { label: 'Memorial', hint: 'Funeraria', icon: '⚱️', route: '/memorial/dashboard', keywords: 'memorial funeraria exequial' },
    { label: 'Memorial · Pagos', hint: 'Registrar pago', icon: '💰', route: '/memorial/payments', keywords: 'pago memorial cartera' },
    { label: 'Configuración', hint: 'Ajustes de la organización', icon: '⚙️', route: '/settings', keywords: 'config ajustes settings' },
  ];

  filtered = computed(() => {
    const q = this.query.trim().toLowerCase();
    if (!q) return this.commands;
    return this.commands.filter((c) =>
      (c.label + ' ' + c.hint + ' ' + (c.keywords || '')).toLowerCase().includes(q),
    );
  });

  @HostListener('document:keydown', ['$event'])
  onGlobalKey(ev: KeyboardEvent): void {
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'k') {
      ev.preventDefault();
      this.isOpen() ? this.close() : this.open();
    } else if (ev.key === 'Escape' && this.isOpen()) {
      this.close();
    }
  }

  open(): void {
    this.query = '';
    this.highlight.set(0);
    this.isOpen.set(true);
    setTimeout(() => {
      const el = document.querySelector<HTMLInputElement>('app-savvy-command input');
      el?.focus();
    });
  }
  close(): void { this.isOpen.set(false); }
  onQuery(): void { this.highlight.set(0); }

  onKey(ev: KeyboardEvent): void {
    const list = this.filtered();
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      this.highlight.set(Math.min(this.highlight() + 1, list.length - 1));
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      this.highlight.set(Math.max(this.highlight() - 1, 0));
    } else if (ev.key === 'Enter') {
      ev.preventDefault();
      const item = list[this.highlight()];
      if (item) this.go(item);
    }
  }

  go(item: CommandItem): void {
    this.close();
    this.router.navigate([item.route]);
  }

  onDrop(ev: DragEvent): void {
    ev.preventDefault();
    const file = ev.dataTransfer?.files?.[0];
    if (file) {
      // Fase 1: enrutamos a SavvyScan. (Fase 2: detección de intención por archivo.)
      this.close();
      this.router.navigate(['/pos/scan']);
    }
  }
}
