import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  ActionDef, Catalog, ConfigField, FlowNotification, FlowService,
  TriggerDef, Workflow, WorkflowDetail, FlowStep,
} from '../core/services/flow.service';

type Tab = 'flows' | 'templates' | 'inbox';

const TRIGGER_FIELDS: Record<string, string[]> = {
  memorial_overdue: ['risk_tier (alto|medio|bajo)', 'days_late', 'overdue_amount', 'overdue_count'],
  pos_low_stock: ['quantity', 'min_stock', 'product'],
};

@Component({
  selector: 'app-automations',
  imports: [CommonModule, FormsModule, RouterLink, DatePipe],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-6">
      <header class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-wider text-violet-600 dark:text-violet-400 font-medium">SavvyFlow ✨</p>
          <h1 class="text-2xl font-bold text-slate-900 dark:text-white mt-1">Automatizaciones</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Crea flujos sin código: cuando pase <em>algo</em>, haz <em>esto</em>. Sin escribir una línea.
          </p>
        </div>
        <div class="flex gap-2">
          <button (click)="evaluate()" [disabled]="evaluating()"
            class="rounded-md border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm disabled:opacity-50">
            {{ evaluating() ? 'Evaluando…' : '⚡ Evaluar ahora' }}
          </button>
          <button (click)="newFlow()" class="rounded-md bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 text-sm font-medium">+ Nueva automatización</button>
        </div>
      </header>

      @if (evalMsg()) { <div class="rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-2 text-sm">{{ evalMsg() }}</div> }

      <!-- Tabs -->
      <nav class="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        @for (t of tabs; track t.id) {
          <button (click)="tab.set(t.id)" class="px-4 py-2 text-sm border-b-2 -mb-px"
            [class.border-violet-600]="tab() === t.id" [class.text-violet-700]="tab() === t.id" [class.dark:text-violet-300]="tab() === t.id"
            [class.border-transparent]="tab() !== t.id" [class.text-slate-500]="tab() !== t.id">
            {{ t.label }}
            @if (t.id === 'inbox' && unread() > 0) { <span class="ml-1 text-[10px] px-1.5 py-0.5 rounded-full bg-rose-500 text-white">{{ unread() }}</span> }
          </button>
        }
      </nav>

      <!-- ===== FLOWS ===== -->
      @if (tab() === 'flows') {
        @if (workflows().length === 0) {
          <div class="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-10 text-center">
            <div class="text-4xl mb-2">🤖</div>
            <p class="text-sm text-slate-600 dark:text-slate-300">Aún no tienes automatizaciones.</p>
            <p class="text-xs text-slate-400 mt-1">Empieza con una <button (click)="tab.set('templates')" class="text-violet-600 hover:underline">plantilla</button> o crea una desde cero.</p>
          </div>
        } @else {
          <div class="grid gap-3">
            @for (w of workflows(); track w.id) {
              <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 flex items-center justify-between gap-3">
                <div class="flex items-center gap-3 min-w-0">
                  <span class="text-2xl shrink-0">{{ triggerIcon(w.trigger_type) }}</span>
                  <div class="min-w-0">
                    <div class="font-semibold text-slate-900 dark:text-white truncate">{{ w.name }}</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400 truncate">{{ w.description || triggerLabel(w.trigger_type) }}</div>
                    <div class="text-[11px] text-slate-400 mt-0.5">
                      {{ w.run_count }} ejecución(es)
                      @if (w.last_run_at) { · última {{ w.last_run_at | date:'short' }} · {{ w.last_status }} }
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <button (click)="toggle(w)" class="text-xs px-2 py-1 rounded-md border"
                    [class]="w.is_active ? 'border-emerald-300 text-emerald-700 dark:text-emerald-300' : 'border-slate-300 text-slate-400'">
                    {{ w.is_active ? '● Activa' : '○ Pausada' }}
                  </button>
                  <button (click)="runNow(w)" [disabled]="running() === w.id" class="text-xs text-violet-600 hover:underline disabled:opacity-50">{{ running() === w.id ? '…' : 'Ejecutar' }}</button>
                  <button (click)="edit(w)" class="text-xs text-slate-600 dark:text-slate-300 hover:underline">Editar</button>
                  <button (click)="remove(w)" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                </div>
              </div>
            }
          </div>
        }
        @if (runMsg()) { <div class="rounded-lg bg-violet-50 border border-violet-200 text-violet-800 px-4 py-2 text-sm">{{ runMsg() }}</div> }
      }

      <!-- ===== TEMPLATES ===== -->
      @if (tab() === 'templates') {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          @for (t of catalog()?.templates || []; track t.key) {
            <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 flex flex-col">
              <div class="text-3xl mb-2">{{ t.icon }}</div>
              <div class="font-semibold text-slate-900 dark:text-white">{{ t.name }}</div>
              <div class="text-xs text-slate-500 dark:text-slate-400 mt-1 flex-1">{{ t.description }}</div>
              <button (click)="install(t.key)" [disabled]="installing() === t.key"
                class="mt-3 rounded-md bg-violet-600 hover:bg-violet-700 text-white px-3 py-2 text-sm font-medium disabled:opacity-50">
                {{ installing() === t.key ? 'Instalando…' : 'Instalar' }}
              </button>
            </div>
          }
        </div>
      }

      <!-- ===== INBOX ===== -->
      @if (tab() === 'inbox') {
        <div class="flex justify-end">
          @if (unread() > 0) { <button (click)="readAll()" class="text-xs text-violet-600 hover:underline">Marcar todo leído</button> }
        </div>
        @if (inbox().length === 0) {
          <p class="text-sm text-slate-400 text-center py-8">Sin notificaciones todavía. Tus automatizaciones las generarán aquí.</p>
        } @else {
          <ul class="space-y-2">
            @for (n of inbox(); track n.id) {
              <li class="rounded-xl border p-3 flex items-start gap-3"
                [class]="n.read_at ? 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900' : levelBorder(n.level)">
                <span class="text-lg">{{ levelIcon(n.level) }}</span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-slate-900 dark:text-white">{{ n.title }}</div>
                  @if (n.body) { <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{{ n.body }}</div> }
                  <div class="text-[11px] text-slate-400 mt-1">{{ n.created_at | date:'short' }}</div>
                </div>
                @if (n.link) { <a [routerLink]="n.link" class="text-xs text-violet-600 hover:underline shrink-0">Ver →</a> }
              </li>
            }
          </ul>
        }
      }

      <!-- ===== EDITOR (modal pipeline) ===== -->
      @if (editorOpen()) {
        <div class="fixed inset-0 z-50 flex items-start justify-center pt-[6vh] px-4 bg-slate-900/40 backdrop-blur-sm overflow-y-auto"
          (click)="$event.target === $event.currentTarget && closeEditor()">
          <div class="w-full max-w-2xl rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-2xl mb-10">
            <div class="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <h3 class="font-semibold text-slate-900 dark:text-white">{{ editId() ? 'Editar' : 'Nueva' }} automatización</h3>
              <button (click)="closeEditor()" class="text-slate-400 text-xl leading-none">×</button>
            </div>

            <div class="p-5 space-y-4">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombre *</span>
                <input [(ngModel)]="draft.name" placeholder="Ej: Avísame del stock bajo"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>

              <!-- TRIGGER -->
              <div class="rounded-xl border border-violet-200 dark:border-violet-900/50 bg-violet-50/40 dark:bg-violet-500/5 p-4">
                <div class="text-[11px] uppercase tracking-wider text-violet-600 dark:text-violet-400 font-medium mb-2">Cuándo (disparador)</div>
                <select [(ngModel)]="draft.trigger_type" (ngModelChange)="onTriggerChange()"
                  class="w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  @for (t of catalog()?.triggers || []; track t.type) { <option [value]="t.type">{{ t.icon }} {{ t.label }}</option> }
                </select>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">{{ triggerDesc(draft.trigger_type) }}</p>
                @for (f of triggerFields(); track f.key) {
                  <label class="block mt-2">
                    <span class="text-xs text-slate-600 dark:text-slate-400">{{ f.label }}</span>
                    <input [ngModel]="draft.trigger_config[f.key]" (ngModelChange)="draft.trigger_config[f.key] = $event"
                      [type]="f.type === 'time' ? 'time' : 'text'"
                      class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                  </label>
                }
              </div>

              <!-- STEPS -->
              <div class="space-y-2">
                <div class="text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-medium">Luego (pasos)</div>
                @for (s of draft.steps; track $index; let i = $index) {
                  <div class="rounded-xl border border-slate-200 dark:border-slate-700 p-3 relative">
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-xs font-medium px-2 py-0.5 rounded"
                        [class]="s.kind === 'condition' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'">
                        {{ s.kind === 'condition' ? '🔎 Si' : '⚙️ Acción' }}: {{ stepLabel(s) }}
                      </span>
                      <button (click)="removeStep(i)" class="text-rose-500 text-xs">Quitar</button>
                    </div>
                    @if (s.kind === 'condition') {
                      <div class="grid grid-cols-3 gap-2">
                        <input [ngModel]="s.config['field']" (ngModelChange)="s.config['field'] = $event" placeholder="campo"
                          class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1.5 text-xs" />
                        <select [ngModel]="s.config['op']" (ngModelChange)="s.config['op'] = $event"
                          class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1.5 text-xs">
                          <option value="eq">=</option><option value="ne">≠</option><option value="gt">&gt;</option>
                          <option value="gte">≥</option><option value="lt">&lt;</option><option value="lte">≤</option><option value="contains">contiene</option>
                        </select>
                        <input [ngModel]="s.config['value']" (ngModelChange)="s.config['value'] = $event" placeholder="valor"
                          class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1.5 text-xs" />
                      </div>
                      @if (triggerHint().length) { <p class="text-[10px] text-slate-400 mt-1">Campos: {{ triggerHint().join(', ') }}</p> }
                    } @else {
                      @for (f of actionFields(s.type); track f.key) {
                        <label class="block mt-1.5">
                          <span class="text-[11px] text-slate-500 dark:text-slate-400">{{ f.label }}</span>
                          @if (f.type === 'select') {
                            <select [ngModel]="s.config[f.key]" (ngModelChange)="s.config[f.key] = $event"
                              class="mt-0.5 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1.5 text-xs">
                              @for (o of f.options || []; track o) { <option [value]="o">{{ o }}</option> }
                            </select>
                          } @else if (f.type === 'textarea') {
                            <textarea [ngModel]="s.config[f.key]" (ngModelChange)="s.config[f.key] = $event" rows="2"
                              class="mt-0.5 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1.5 text-xs"></textarea>
                          } @else {
                            <input [ngModel]="s.config[f.key]" (ngModelChange)="s.config[f.key] = $event"
                              class="mt-0.5 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1.5 text-xs" />
                          }
                        </label>
                      }
                      <p class="text-[10px] text-slate-400 mt-1">Usa <code>&#123;count&#125;</code> en el texto para el número de resultados.</p>
                    }
                  </div>
                }
                <div class="flex gap-2">
                  <button (click)="addStep('condition')" class="text-xs px-3 py-1.5 rounded border border-amber-300 text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-900/20">+ Condición</button>
                  <select #actionPick (change)="addAction(actionPick.value); actionPick.value=''"
                    class="text-xs px-3 py-1.5 rounded border border-blue-300 text-blue-700 dark:text-blue-300 bg-white dark:bg-slate-800">
                    <option value="">+ Acción…</option>
                    @for (a of catalog()?.actions || []; track a.type) { <option [value]="a.type">{{ a.icon }} {{ a.label }}</option> }
                  </select>
                </div>
              </div>
            </div>

            <div class="px-5 py-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center">
              <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <input type="checkbox" [(ngModel)]="draft.is_active" class="h-4 w-4" /> Activa
              </label>
              <div class="flex gap-2">
                <button (click)="closeEditor()" class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button (click)="save()" [disabled]="saving() || !draft.name.trim()"
                  class="rounded-md bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white px-5 py-2 text-sm font-medium">{{ saving() ? 'Guardando…' : 'Guardar' }}</button>
              </div>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class AutomationsComponent implements OnInit {
  private readonly flow = inject(FlowService);

  readonly tabs: { id: Tab; label: string }[] = [
    { id: 'flows', label: 'Mis automatizaciones' },
    { id: 'templates', label: 'Plantillas' },
    { id: 'inbox', label: 'Bandeja' },
  ];
  tab = signal<Tab>('flows');

  catalog = signal<Catalog | null>(null);
  workflows = signal<Workflow[]>([]);
  inbox = signal<FlowNotification[]>([]);
  unread = computed(() => this.inbox().filter((n) => !n.read_at).length);

  running = signal<string | null>(null);
  installing = signal<string | null>(null);
  evaluating = signal(false);
  saving = signal(false);
  runMsg = signal('');
  evalMsg = signal('');

  editorOpen = signal(false);
  editId = signal<string | null>(null);
  draft: { name: string; description: string | null; trigger_type: string; trigger_config: Record<string, any>; is_active: boolean; steps: FlowStep[] } = this.emptyDraft();

  ngOnInit(): void {
    this.flow.catalog().subscribe({ next: (c) => this.catalog.set(c) });
    this.reload();
    this.flow.notifications().subscribe({ next: (n) => this.inbox.set(n) });
  }

  reload(): void { this.flow.list().subscribe({ next: (w) => this.workflows.set(w) }); }

  emptyDraft() {
    return { name: '', description: null as string | null, trigger_type: 'manual', trigger_config: {} as Record<string, any>, is_active: true, steps: [] as FlowStep[] };
  }

  // ---- catalog helpers ----
  triggerLabel(t: string): string { return this.catalog()?.triggers.find((x) => x.type === t)?.label || t; }
  triggerIcon(t: string): string { return this.catalog()?.triggers.find((x) => x.type === t)?.icon || '🤖'; }
  triggerDesc(t: string): string { return this.catalog()?.triggers.find((x) => x.type === t)?.desc || ''; }
  triggerFields(): ConfigField[] { return this.catalog()?.triggers.find((x) => x.type === this.draft.trigger_type)?.config_fields || []; }
  triggerHint(): string[] { return TRIGGER_FIELDS[this.draft.trigger_type] || []; }
  actionFields(type: string): ConfigField[] { return this.catalog()?.actions.find((a) => a.type === type)?.config_fields || []; }
  actionLabel(type: string): string { return this.catalog()?.actions.find((a) => a.type === type)?.label || type; }
  stepLabel(s: FlowStep): string { return s.kind === 'condition' ? 'filtro' : this.actionLabel(s.type); }

  // ---- editor ----
  newFlow(): void { this.editId.set(null); this.draft = this.emptyDraft(); this.editorOpen.set(true); }
  edit(w: Workflow): void {
    this.flow.get(w.id).subscribe({ next: (d) => {
      this.editId.set(d.id);
      this.draft = { name: d.name, description: d.description, trigger_type: d.trigger_type, trigger_config: { ...d.trigger_config }, is_active: d.is_active, steps: d.steps.map((s) => ({ ...s, config: { ...s.config } })) };
      this.editorOpen.set(true);
    }});
  }
  closeEditor(): void { this.editorOpen.set(false); }
  onTriggerChange(): void { this.draft.trigger_config = {}; }
  addStep(kind: 'condition'): void { this.draft.steps.push({ kind, type: 'field_compare', config: { op: 'eq' }, sort_order: this.draft.steps.length }); }
  addAction(type: string): void { if (!type) return; const f = this.actionFields(type); const cfg: Record<string, unknown> = {}; f.forEach((x) => cfg[x.key] = x.default ?? ''); this.draft.steps.push({ kind: 'action', type, config: cfg, sort_order: this.draft.steps.length }); }
  removeStep(i: number): void { this.draft.steps.splice(i, 1); }

  save(): void {
    this.saving.set(true);
    const body = { ...this.draft, steps: this.draft.steps.map((s, i) => ({ ...s, sort_order: i })) };
    const obs = this.editId() ? this.flow.update(this.editId()!, body as any) : this.flow.create(body as any);
    obs.subscribe({
      next: () => { this.saving.set(false); this.editorOpen.set(false); this.reload(); },
      error: () => this.saving.set(false),
    });
  }

  // ---- actions ----
  toggle(w: Workflow): void { this.flow.toggle(w.id, !w.is_active).subscribe({ next: () => this.reload() }); }
  runNow(w: Workflow): void {
    this.running.set(w.id); this.runMsg.set('');
    this.flow.run(w.id).subscribe({
      next: (r) => { this.running.set(null); this.runMsg.set(`"${w.name}": ${r.status} · ${r.items_matched} resultado(s).`); this.reload(); this.flow.notifications().subscribe({ next: (n) => this.inbox.set(n) }); },
      error: () => { this.running.set(null); this.runMsg.set('No se pudo ejecutar.'); },
    });
  }
  remove(w: Workflow): void { if (!confirm(`¿Eliminar "${w.name}"?`)) return; this.flow.remove(w.id).subscribe({ next: () => this.reload() }); }
  install(key: string): void { this.installing.set(key); this.flow.installTemplate(key).subscribe({ next: () => { this.installing.set(null); this.tab.set('flows'); this.reload(); }, error: () => this.installing.set(null) }); }
  evaluate(): void {
    this.evaluating.set(true); this.evalMsg.set('');
    this.flow.evaluate().subscribe({
      next: (r) => { this.evaluating.set(false); this.evalMsg.set(`Evaluadas ${r.evaluated} · ejecutadas ${r.executed} · omitidas ${r.skipped}.`); this.reload(); this.flow.notifications().subscribe({ next: (n) => this.inbox.set(n) }); },
      error: () => this.evaluating.set(false),
    });
  }
  readAll(): void { this.flow.readAll().subscribe({ next: () => this.flow.notifications().subscribe({ next: (n) => this.inbox.set(n) }) }); }

  levelIcon(l: string): string { return l === 'danger' ? '🔴' : l === 'warning' ? '🟠' : '🔵'; }
  levelBorder(l: string): string {
    return l === 'danger' ? 'border-rose-300 dark:border-rose-800 bg-rose-50/40 dark:bg-rose-500/5'
      : l === 'warning' ? 'border-amber-300 dark:border-amber-800 bg-amber-50/40 dark:bg-amber-500/5'
      : 'border-blue-300 dark:border-blue-800 bg-blue-50/40 dark:bg-blue-500/5';
  }
}
