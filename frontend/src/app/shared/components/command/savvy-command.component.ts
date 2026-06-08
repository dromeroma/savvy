import { Component, computed, HostListener, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AiService, GraphHit } from '../../../core/services/ai.service';

interface CommandItem {
  label: string;
  hint: string;
  icon: string;
  route: string;
  keywords?: string;
}

const MODULE_ICON: Record<string, string> = {
  hr: '👥', memorial: '⚱️', water: '💧', pos: '🛒', crm: '📇',
};

/**
 * Savvy Command (⌘K) — la barra mágica global.
 * Navegación + búsqueda universal cross-módulo (Savvy Graph) + Copilot conversacional.
 */
@Component({
  selector: 'app-savvy-command',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <button type="button" (click)="open()"
      class="hidden md:flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 px-3 py-1.5 text-sm text-slate-400 hover:border-brand-300 dark:hover:border-brand-700 transition">
      <span>✨ Buscar, preguntar o ejecutar…</span>
      <kbd class="text-[10px] font-sans px-1.5 py-0.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900">⌘K</kbd>
    </button>

    @if (isOpen()) {
      <div class="fixed inset-0 z-[100] flex items-start justify-center pt-[12vh] px-4 bg-slate-900/40 backdrop-blur-sm"
        (click)="$event.target === $event.currentTarget && close()">
        <div class="w-full max-w-xl rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden"
          (drop)="onDrop($event)" (dragover)="$event.preventDefault()">

          <div class="flex items-center gap-3 px-4 py-3 border-b border-slate-100 dark:border-slate-800">
            <span class="text-violet-500 text-lg">{{ mode() === 'chat' ? '💬' : '✨' }}</span>
            <input #cmdInput [(ngModel)]="query" (ngModelChange)="onQuery()" (keydown)="onKey($event)"
              [placeholder]="mode() === 'chat' ? 'Pregúntale a SavvyCopilot…' : 'Busca personas, módulos, acciones… o arrastra una factura'"
              class="flex-1 bg-transparent outline-none text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400" />
            @if (mode() === 'chat') {
              <button (click)="exitChat()" class="text-[11px] text-slate-400 hover:text-slate-600">← volver</button>
            } @else {
              <kbd class="text-[10px] font-sans px-1.5 py-0.5 rounded border border-slate-300 dark:border-slate-600 text-slate-400">esc</kbd>
            }
          </div>

          <!-- ===== Modo CHAT (Copilot) ===== -->
          @if (mode() === 'chat') {
            <div class="px-4 py-4 max-h-96 overflow-y-auto">
              @if (chatLoading()) {
                <div class="flex items-center gap-2 text-sm text-violet-600 dark:text-violet-400">
                  <div class="animate-spin rounded-full h-4 w-4 border-2 border-violet-200 border-t-violet-600"></div>
                  Pensando…
                </div>
              } @else if (chatAnswer()) {
                <div class="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-line leading-relaxed">{{ chatAnswer() }}</div>
                @if (chatTools().length) {
                  <div class="mt-3 flex flex-wrap gap-1">
                    @for (t of chatTools(); track t) {
                      <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono">{{ t }}</span>
                    }
                  </div>
                }
              } @else if (chatError()) {
                <div class="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-500/5 p-3 text-sm text-amber-800 dark:text-amber-300">
                  {{ chatError() }}
                </div>
              } @else {
                <p class="text-xs text-slate-400">Escribe tu pregunta y presiona ↵. Ej: <em>"¿cuánto vendí hoy?"</em>, <em>"¿qué productos están por agotarse?"</em></p>
              }
            </div>
          } @else {
            <!-- ===== Modo COMANDO ===== -->
            <ul class="max-h-96 overflow-y-auto py-2">
              <!-- Copilot CTA -->
              @if (query.trim().length > 0) {
                <li>
                  <button type="button" (click)="askCopilot()" (mouseenter)="highlight.set(-1)"
                    class="w-full flex items-center gap-3 px-4 py-2.5 text-left border-b border-slate-100 dark:border-slate-800"
                    [class.bg-violet-50]="highlight() === -1" [class.dark:bg-violet-500/10]="highlight() === -1">
                    <span class="text-lg w-6 text-center">💬</span>
                    <span class="flex-1 min-w-0">
                      <span class="block text-sm font-medium text-slate-900 dark:text-slate-100">Preguntar a SavvyCopilot</span>
                      <span class="block text-xs text-slate-400 truncate">"{{ query }}"</span>
                    </span>
                    <span class="text-xs text-slate-400">↵</span>
                  </button>
                </li>
              }

              <!-- Resultados universales (Savvy Graph) -->
              @if (searchHits().length > 0) {
                <li class="px-4 pt-2 pb-1 text-[10px] uppercase tracking-wider text-slate-400">Personas y registros</li>
                @for (h of searchHits(); track h.module + h.entity_id; let i = $index) {
                  <li>
                    <button type="button" (click)="goHit(h)" (mouseenter)="highlight.set(i)"
                      class="w-full flex items-center gap-3 px-4 py-2 text-left"
                      [class.bg-brand-50]="highlight() === i" [class.dark:bg-brand-500/10]="highlight() === i">
                      <span class="text-lg w-6 text-center shrink-0">{{ moduleIcon(h.module) }}</span>
                      <span class="flex-1 min-w-0">
                        <span class="block text-sm font-medium text-slate-900 dark:text-slate-100 truncate">{{ h.display_name }}</span>
                        <span class="block text-xs text-slate-400 truncate">{{ h.subtitle }}{{ h.document_number ? ' · ' + h.document_number : '' }}</span>
                      </span>
                    </button>
                  </li>
                }
              }

              <!-- Navegación -->
              @if (filteredCmds().length > 0) {
                <li class="px-4 pt-2 pb-1 text-[10px] uppercase tracking-wider text-slate-400">Ir a</li>
                @for (item of filteredCmds(); track item.route; let i = $index) {
                  <li>
                    <button type="button" (click)="go(item)" (mouseenter)="highlight.set(searchHits().length + i)"
                      class="w-full flex items-center gap-3 px-4 py-2 text-left"
                      [class.bg-brand-50]="highlight() === searchHits().length + i" [class.dark:bg-brand-500/10]="highlight() === searchHits().length + i">
                      <span class="text-lg w-6 text-center shrink-0">{{ item.icon }}</span>
                      <span class="flex-1 min-w-0">
                        <span class="block text-sm font-medium text-slate-900 dark:text-slate-100 truncate">{{ item.label }}</span>
                        <span class="block text-xs text-slate-400 truncate">{{ item.hint }}</span>
                      </span>
                    </button>
                  </li>
                }
              }

              @if (query.trim() && searchHits().length === 0 && filteredCmds().length === 0 && !searching()) {
                <li class="px-4 py-4 text-center text-sm text-slate-400">Sin coincidencias. Prueba preguntarle al Copilot ↵</li>
              }
            </ul>
          }

          <div class="px-4 py-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>↑↓ navegar · ↵ abrir · esc cerrar</span>
            <span class="text-violet-500">Savvy {{ mode() === 'chat' ? 'Copilot' : 'Command' }}</span>
          </div>
        </div>
      </div>
    }
  `,
})
export class SavvyCommandComponent {
  private readonly router = inject(Router);
  private readonly ai = inject(AiService);

  isOpen = signal(false);
  mode = signal<'command' | 'chat'>('command');
  query = '';
  highlight = signal(0);

  searchHits = signal<GraphHit[]>([]);
  searching = signal(false);
  private searchDebounce?: ReturnType<typeof setTimeout>;

  chatAnswer = signal('');
  chatTools = signal<string[]>([]);
  chatLoading = signal(false);
  chatError = signal('');

  private readonly commands: CommandItem[] = [
    { label: 'Escanear factura de compra', hint: 'SavvyScan → actualiza inventario (POS)', icon: '✨', route: '/pos/scan', keywords: 'ia ocr factura compra inventario stock' },
    { label: 'Inicio', hint: 'Cuadro de mando general', icon: '🏠', route: '/dashboard', keywords: 'home dashboard inicio' },
    { label: 'Automatizaciones', hint: 'SavvyFlow — flujos no-code', icon: '🤖', route: '/automations', keywords: 'savvyflow automatizacion workflow flujo zapier alerta' },
    { label: 'POS · Terminal', hint: 'Punto de venta', icon: '🛒', route: '/pos/terminal', keywords: 'pos venta caja' },
    { label: 'POS · Inventario', hint: 'Stock por producto', icon: '📦', route: '/pos/inventory', keywords: 'inventario stock' },
    { label: 'POS · Productos', hint: 'Catálogo', icon: '🏷️', route: '/pos/products', keywords: 'productos catalogo' },
    { label: 'Talento Humano', hint: 'SavvyHR', icon: '👥', route: '/hr/dashboard', keywords: 'hr rrhh empleados nomina' },
    { label: 'HR · Liquidaciones', hint: 'Cese de contrato', icon: '🧾', route: '/hr/liquidations', keywords: 'liquidacion despido' },
    { label: 'Memorial', hint: 'Funeraria', icon: '⚱️', route: '/memorial/dashboard', keywords: 'memorial funeraria exequial' },
    { label: 'Memorial · Pagos', hint: 'Registrar pago', icon: '💰', route: '/memorial/payments', keywords: 'pago cartera' },
    { label: 'Configuración', hint: 'Ajustes de la organización', icon: '⚙️', route: '/settings', keywords: 'config ajustes' },
  ];

  filteredCmds = computed(() => {
    const q = this.query.trim().toLowerCase();
    if (!q) return this.commands;
    return this.commands.filter((c) =>
      (c.label + ' ' + c.hint + ' ' + (c.keywords || '')).toLowerCase().includes(q),
    ).slice(0, 6);
  });

  private totalItems = computed(() => this.searchHits().length + this.filteredCmds().length);

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
    this.mode.set('command');
    this.searchHits.set([]);
    this.highlight.set(0);
    this.isOpen.set(true);
    setTimeout(() => document.querySelector<HTMLInputElement>('app-savvy-command input')?.focus());
  }
  close(): void { this.isOpen.set(false); }

  onQuery(): void {
    this.highlight.set(0);
    if (this.searchDebounce) clearTimeout(this.searchDebounce);
    const q = this.query.trim();
    if (q.length < 2) { this.searchHits.set([]); return; }
    this.searching.set(true);
    this.searchDebounce = setTimeout(() => {
      this.ai.search(q).subscribe({
        next: (r) => { this.searchHits.set(r.hits.slice(0, 6)); this.searching.set(false); },
        error: () => { this.searchHits.set([]); this.searching.set(false); },
      });
    }, 250);
  }

  onKey(ev: KeyboardEvent): void {
    if (this.mode() === 'chat') {
      if (ev.key === 'Enter') { ev.preventDefault(); this.askCopilot(); }
      return;
    }
    const total = this.totalItems();
    if (ev.key === 'ArrowDown') { ev.preventDefault(); this.highlight.set(Math.min(this.highlight() + 1, total - 1)); }
    else if (ev.key === 'ArrowUp') { ev.preventDefault(); this.highlight.set(Math.max(this.highlight() - 1, -1)); }
    else if (ev.key === 'Enter') {
      ev.preventDefault();
      const h = this.highlight();
      if (h === -1) { this.askCopilot(); return; }
      const hits = this.searchHits();
      if (h < hits.length) { this.goHit(hits[h]); return; }
      const cmd = this.filteredCmds()[h - hits.length];
      if (cmd) this.go(cmd);
    }
  }

  askCopilot(): void {
    const msg = this.query.trim();
    if (!msg) return;
    this.mode.set('chat');
    this.chatAnswer.set('');
    this.chatError.set('');
    this.chatTools.set([]);
    this.chatLoading.set(true);
    this.ai.copilot(msg).subscribe({
      next: (r) => { this.chatAnswer.set(r.answer); this.chatTools.set(r.tools_used || []); this.chatLoading.set(false); },
      error: (err) => {
        this.chatLoading.set(false);
        this.chatError.set(err?.error?.detail || 'No se pudo consultar. La IA puede no estar configurada todavía.');
      },
    });
  }
  exitChat(): void { this.mode.set('command'); this.query = ''; this.chatAnswer.set(''); this.chatError.set(''); }

  go(item: CommandItem): void { this.close(); this.router.navigate([item.route]); }
  goHit(h: GraphHit): void { if (h.route) { this.close(); this.router.navigate([h.route]); } }
  moduleIcon(m: string): string { return MODULE_ICON[m] || '•'; }

  onDrop(ev: DragEvent): void {
    ev.preventDefault();
    if (ev.dataTransfer?.files?.[0]) { this.close(); this.router.navigate(['/pos/scan']); }
  }
}
