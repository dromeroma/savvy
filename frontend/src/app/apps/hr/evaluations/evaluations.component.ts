import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrCompetency,
  HrEvaluation,
  HrEvaluationCycle,
  HrEvaluationCycleCreate,
  HrEvaluationCycleStatus,
  HrEvaluationResponseInput,
  HrEvaluationStatus,
  HrEvaluatorType,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';

type Tab = 'cycles' | 'evaluations';

@Component({
  selector: 'app-hr-evaluations',
  imports: [CommonModule, FormsModule, PaginationComponent],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Evaluaciones de desempeño</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400">
            Crea ciclos con competencias y escala, ábrelos para generar evaluaciones por empleado.
          </p>
        </div>
        <button (click)="openCreate()" type="button"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + Nuevo ciclo
        </button>
      </header>

      <nav class="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        @for (t of tabs; track t.value) {
          <button type="button" (click)="tab.set(t.value)"
            class="px-4 py-2 text-sm border-b-2 -mb-px"
            [class.border-brand-600]="tab() === t.value"
            [class.text-brand-700]="tab() === t.value"
            [class.dark:text-brand-300]="tab() === t.value"
            [class.border-transparent]="tab() !== t.value"
            [class.text-slate-600]="tab() !== t.value"
            [class.dark:text-slate-400]="tab() !== t.value">
            {{ t.label }}
          </button>
        }
      </nav>

      @switch (tab()) {

        @case ('cycles') {
          <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
              <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                <tr>
                  <th class="text-left px-4 py-2 font-medium">Código</th>
                  <th class="text-left px-4 py-2 font-medium">Nombre</th>
                  <th class="text-left px-4 py-2 font-medium">Período</th>
                  <th class="text-left px-4 py-2 font-medium">Tipos</th>
                  <th class="text-right px-4 py-2 font-medium">Compet.</th>
                  <th class="text-left px-4 py-2 font-medium">Estado</th>
                  <th class="text-right px-4 py-2 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                @if (loadingCycles()) {
                  <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
                } @else if (cycles().length === 0) {
                  <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin ciclos.</td></tr>
                } @else {
                  @for (c of paginatedCycles(); track c.id) {
                    <tr class="cursor-pointer" (click)="selectCycle(c)" [class.bg-slate-50]="selectedCycleId() === c.id" [class.dark:bg-slate-800]="selectedCycleId() === c.id">
                      <td class="px-4 py-2 font-mono text-xs">{{ c.code }}</td>
                      <td class="px-4 py-2 font-medium">{{ c.name }}</td>
                      <td class="px-4 py-2 text-xs">{{ c.start_date }} → {{ c.end_date }}</td>
                      <td class="px-4 py-2 text-xs space-x-1">
                        @if (c.enable_self) { <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300">Auto</span> }
                        @if (c.enable_supervisor) { <span class="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300">Jefe</span> }
                        @if (c.enable_360) { <span class="text-[10px] px-1.5 py-0.5 rounded bg-pink-100 dark:bg-pink-900/40 text-pink-700 dark:text-pink-300">360°</span> }
                      </td>
                      <td class="px-4 py-2 text-right">{{ c.competencies?.length || 0 }}</td>
                      <td class="px-4 py-2">
                        <span class="text-xs px-2 py-0.5 rounded-md" [class]="cycleStatusClass(c.status)">{{ cycleStatusLabel(c.status) }}</span>
                      </td>
                      <td class="px-4 py-2 text-right whitespace-nowrap space-x-2">
                        @if (c.status === 'draft') {
                          <button (click)="openCycle(c); $event.stopPropagation()" type="button" class="text-xs text-emerald-600 hover:underline">Abrir</button>
                          <button (click)="removeCycle(c); $event.stopPropagation()" type="button" class="text-xs text-rose-600 hover:underline">Eliminar</button>
                        }
                        @if (c.status === 'open') {
                          <button (click)="closeCycle(c); $event.stopPropagation()" type="button" class="text-xs text-slate-600 dark:text-slate-400 hover:underline">Cerrar</button>
                        }
                      </td>
                    </tr>
                  }
                }
              </tbody>
            </table>
            <app-pagination [totalItems]="cycles().length" [(page)]="pageCycles" [(pageSize)]="pageSize" />
          </section>
        }

        @case ('evaluations') {
          @if (!selectedCycleId()) {
            <p class="text-sm text-slate-500 dark:text-slate-400">Selecciona un ciclo en la pestaña anterior para ver sus evaluaciones.</p>
          } @else {
            <section class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
              <div class="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
                <p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  Ciclo: <span class="font-mono">{{ selectedCycle()?.code }}</span> — {{ selectedCycle()?.name }}
                </p>
              </div>
              <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
                <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                  <tr>
                    <th class="text-left px-4 py-2 font-medium">Empleado</th>
                    <th class="text-right px-4 py-2 font-medium">Auto</th>
                    <th class="text-right px-4 py-2 font-medium">Jefe</th>
                    <th class="text-right px-4 py-2 font-medium">Peer (n)</th>
                    <th class="text-right px-4 py-2 font-medium">Overall</th>
                    <th class="text-left px-4 py-2 font-medium">Estado</th>
                    <th class="text-right px-4 py-2 font-medium">Acciones</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                  @if (loadingEvals()) {
                    <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Cargando...</td></tr>
                  } @else if (evaluations().length === 0) {
                    <tr><td colspan="7" class="px-4 py-6 text-center text-slate-500 dark:text-slate-400">Sin evaluaciones. Abre el ciclo para generarlas.</td></tr>
                  } @else {
                    @for (e of evaluations(); track e.id) {
                      <tr>
                        <td class="px-4 py-2 font-mono text-xs">{{ e.employee_id.slice(0, 8) }}…</td>
                        <td class="px-4 py-2 text-right">{{ e.self_score || '—' }}</td>
                        <td class="px-4 py-2 text-right">{{ e.supervisor_score || '—' }}</td>
                        <td class="px-4 py-2 text-right">{{ e.peer_count > 0 ? e.peer_avg + ' (' + e.peer_count + ')' : '—' }}</td>
                        <td class="px-4 py-2 text-right font-mono font-semibold text-emerald-700 dark:text-emerald-300">{{ e.overall_score || '—' }}</td>
                        <td class="px-4 py-2">
                          <span class="text-xs px-2 py-0.5 rounded-md" [class]="evalStatusClass(e.status)">{{ evalStatusLabel(e.status) }}</span>
                        </td>
                        <td class="px-4 py-2 text-right whitespace-nowrap">
                          <button (click)="openRespond(e)" type="button" class="text-xs text-brand-600 hover:underline">Responder</button>
                        </td>
                      </tr>
                    }
                  }
                </tbody>
              </table>
            </section>
          }
        }
      }

      <!-- Modal crear ciclo -->
      @if (formOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Nuevo ciclo</h3>
            @if (formError()) { <p class="text-sm text-rose-600 mb-3">{{ formError() }}</p> }
            <form (ngSubmit)="save()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Código *</span>
                <input [(ngModel)]="form.code" name="code" required maxlength="40"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Nombre *</span>
                <input [(ngModel)]="form.name" name="name" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Inicio *</span>
                <input type="date" [(ngModel)]="form.start_date" name="sd" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fin *</span>
                <input type="date" [(ngModel)]="form.end_date" name="ed" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Escala mín</span>
                <input type="number" [(ngModel)]="form.scale_min" name="smin" step="0.01"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Escala máx</span>
                <input type="number" [(ngModel)]="form.scale_max" name="smax" step="0.01"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <div class="sm:col-span-2 grid grid-cols-3 gap-2 text-sm">
                <label class="flex items-center gap-2">
                  <input type="checkbox" [(ngModel)]="form.enable_self" name="es" />
                  <span class="text-slate-700 dark:text-slate-300">Auto-evaluación</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" [(ngModel)]="form.enable_supervisor" name="esup" />
                  <span class="text-slate-700 dark:text-slate-300">Evaluación jefe</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" [(ngModel)]="form.enable_360" name="e360" />
                  <span class="text-slate-700 dark:text-slate-300">Evaluación 360°</span>
                </label>
              </div>

              <div class="sm:col-span-2 border-t border-slate-200 dark:border-slate-700 pt-3">
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Competencias</h4>
                  <button type="button" (click)="addCompetency()"
                    class="text-xs text-brand-600 hover:underline">+ Agregar</button>
                </div>
                @if (form.competencies.length === 0) {
                  <p class="text-xs text-slate-500 dark:text-slate-400">Sin competencias. Agrega al menos una.</p>
                }
                @for (comp of form.competencies; track $index) {
                  <div class="grid grid-cols-12 gap-2 mb-2">
                    <input [(ngModel)]="comp.code" [name]="'ccode' + $index" placeholder="LEAD" required
                      class="col-span-3 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1 text-xs uppercase" />
                    <input [(ngModel)]="comp.name" [name]="'cname' + $index" placeholder="Liderazgo" required
                      class="col-span-6 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1 text-xs" />
                    <input type="number" step="0.1" [(ngModel)]="comp.weight" [name]="'cw' + $index" placeholder="1"
                      class="col-span-2 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-2 py-1 text-xs" />
                    <button type="button" (click)="removeCompetency($index)" class="col-span-1 text-rose-600 text-xs">×</button>
                  </div>
                }
              </div>

              <div class="sm:col-span-2 flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeForm()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="saving()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ saving() ? 'Guardando...' : 'Crear ciclo' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }

      <!-- Modal responder evaluación -->
      @if (respondOpen() && selectedEval(); as ev) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeRespond()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Responder evaluación</h3>
            @if (respondError()) { <p class="text-sm text-rose-600 mb-3">{{ respondError() }}</p> }
            <div class="space-y-4">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo de evaluador</span>
                <select [(ngModel)]="respondInput.evaluator_type"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  @if (selectedCycle()?.enable_self) { <option value="self">Auto-evaluación</option> }
                  @if (selectedCycle()?.enable_supervisor) { <option value="supervisor">Jefe inmediato</option> }
                  @if (selectedCycle()?.enable_360) {
                    <option value="peer">Par</option>
                    <option value="subordinate">Subordinado</option>
                  }
                </select>
              </label>

              @for (comp of selectedCycle()?.competencies; track comp.code) {
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-sm font-medium text-slate-900 dark:text-slate-100">{{ comp.name }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">peso: {{ comp.weight }}</span>
                  </div>
                  @if (comp.description) {
                    <p class="text-xs text-slate-500 dark:text-slate-400 mb-1">{{ comp.description }}</p>
                  }
                  <input type="number" [min]="+(selectedCycle()?.scale_min || '1')" [max]="+(selectedCycle()?.scale_max || '5')"
                    step="0.5" [(ngModel)]="scoresMap[comp.code]"
                    [placeholder]="'Puntaje (' + selectedCycle()?.scale_min + '-' + selectedCycle()?.scale_max + ')'"
                    class="w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </div>
              }

              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Comentarios</span>
                <textarea [(ngModel)]="respondInput.comments" rows="3"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
            </div>

            <div class="flex justify-end gap-2 pt-3 mt-4 border-t border-slate-200 dark:border-slate-700">
              <button type="button" (click)="closeRespond()"
                class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
              <button type="button" (click)="submitResponse()" [disabled]="respondSaving()"
                class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                {{ respondSaving() ? 'Enviando...' : 'Enviar respuesta' }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrEvaluationsComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);

  readonly tabs: { value: Tab; label: string }[] = [
    { value: 'cycles', label: 'Ciclos' },
    { value: 'evaluations', label: 'Evaluaciones' },
  ];

  tab = signal<Tab>('cycles');
  loadingCycles = signal(true);
  loadingEvals = signal(false);

  cycles = signal<HrEvaluationCycle[]>([]);
  evaluations = signal<HrEvaluation[]>([]);
  selectedCycleId = signal<string | null>(null);
  selectedCycle = computed(() => this.cycles().find((c) => c.id === this.selectedCycleId()) ?? null);

  pageCycles = signal(0);
  pageSize = signal(20);
  paginatedCycles = computed(() => {
    const s = this.pageCycles() * this.pageSize();
    return this.cycles().slice(s, s + this.pageSize());
  });

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: HrEvaluationCycleCreate = this.emptyForm();

  respondOpen = signal(false);
  respondSaving = signal(false);
  respondError = signal('');
  selectedEval = signal<HrEvaluation | null>(null);
  respondInput: HrEvaluationResponseInput = { evaluator_type: 'self', scores: {}, comments: null };
  scoresMap: Record<string, number> = {};

  constructor() {
    effect(() => { this.cycles(); this.pageCycles.set(0); }, { allowSignalWrites: true });
  }

  ngOnInit(): void { this.loadCycles(); }

  loadCycles(): void {
    this.loadingCycles.set(true);
    this.hr.listEvaluationCycles().subscribe({
      next: (r) => { this.cycles.set(r); this.loadingCycles.set(false); },
      error: () => { this.loadingCycles.set(false); },
    });
  }

  selectCycle(c: HrEvaluationCycle): void {
    this.selectedCycleId.set(c.id);
    this.tab.set('evaluations');
    this.loadEvaluations();
  }

  loadEvaluations(): void {
    const cid = this.selectedCycleId();
    if (!cid) return;
    this.loadingEvals.set(true);
    this.hr.listEvaluationsByCycle(cid).subscribe({
      next: (r) => { this.evaluations.set(r); this.loadingEvals.set(false); },
      error: () => { this.loadingEvals.set(false); },
    });
  }

  emptyForm(): HrEvaluationCycleCreate {
    const today = new Date();
    return {
      code: '', name: '',
      start_date: today.toISOString().slice(0, 10),
      end_date: new Date(today.getTime() + 30 * 86400000).toISOString().slice(0, 10),
      enable_self: true, enable_supervisor: true, enable_360: false,
      scale_min: '1', scale_max: '5',
      competencies: [
        { code: 'TECH', name: 'Conocimientos técnicos', weight: 1 },
        { code: 'TEAM', name: 'Trabajo en equipo', weight: 1 },
        { code: 'RESULTS', name: 'Orientación a resultados', weight: 1 },
      ],
    };
  }

  addCompetency(): void {
    this.form.competencies.push({ code: '', name: '', weight: 1 });
  }
  removeCompetency(i: number): void {
    this.form.competencies.splice(i, 1);
  }

  openCreate(): void { this.form = this.emptyForm(); this.formError.set(''); this.formOpen.set(true); }
  closeForm(): void { this.formOpen.set(false); }

  save(): void {
    if (this.form.competencies.length === 0) {
      this.formError.set('Agrega al menos una competencia.');
      return;
    }
    this.saving.set(true);
    this.hr.createEvaluationCycle(this.form).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Creado', message: this.form.code });
        this.saving.set(false); this.formOpen.set(false); this.loadCycles();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'No se pudo crear.');
      },
    });
  }

  openCycle(c: HrEvaluationCycle): void {
    if (!confirm(`¿Abrir ciclo ${c.code}? Generará evaluaciones para todos los empleados activos.`)) return;
    this.hr.openEvaluationCycle(c.id).subscribe({
      next: (r) => {
        this.notify.show({ type: 'success', title: 'Abierto', message: `${r.evaluations_created} evaluaciones creadas` });
        this.loadCycles();
      },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo abrir.' }),
    });
  }

  closeCycle(c: HrEvaluationCycle): void {
    if (!confirm(`¿Cerrar definitivamente el ciclo ${c.code}?`)) return;
    this.hr.closeEvaluationCycle(c.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Cerrado', message: c.code }); this.loadCycles(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo cerrar.' }),
    });
  }

  removeCycle(c: HrEvaluationCycle): void {
    if (!confirm(`¿Eliminar ciclo ${c.code}?`)) return;
    this.hr.deleteEvaluationCycle(c.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: c.code }); this.loadCycles(); },
      error: (err) => this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo eliminar.' }),
    });
  }

  openRespond(e: HrEvaluation): void {
    this.selectedEval.set(e);
    this.scoresMap = {};
    const sc = this.selectedCycle();
    if (sc) {
      for (const comp of sc.competencies) this.scoresMap[comp.code] = +(sc.scale_min || '1');
      const defaultType: HrEvaluatorType =
        sc.enable_self ? 'self' :
        sc.enable_supervisor ? 'supervisor' :
        sc.enable_360 ? 'peer' : 'self';
      this.respondInput = { evaluator_type: defaultType, scores: {}, comments: null };
    }
    this.respondError.set('');
    this.respondOpen.set(true);
  }
  closeRespond(): void { this.respondOpen.set(false); }

  submitResponse(): void {
    const e = this.selectedEval();
    if (!e) return;
    this.respondInput.scores = { ...this.scoresMap };
    this.respondSaving.set(true);
    this.hr.submitEvaluationResponse(e.id, this.respondInput).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Enviada', message: 'Respuesta registrada' });
        this.respondSaving.set(false); this.respondOpen.set(false);
        this.loadEvaluations();
      },
      error: (err) => {
        this.respondSaving.set(false);
        this.respondError.set(err?.error?.detail || 'No se pudo enviar.');
      },
    });
  }

  cycleStatusLabel(s: HrEvaluationCycleStatus): string {
    const map: Record<HrEvaluationCycleStatus, string> = {
      draft: 'Borrador', open: 'Abierto', closed: 'Cerrado', cancelled: 'Cancelado',
    };
    return map[s];
  }
  cycleStatusClass(s: HrEvaluationCycleStatus): string {
    const map: Record<HrEvaluationCycleStatus, string> = {
      draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      open: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      closed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    };
    return map[s];
  }
  evalStatusLabel(s: HrEvaluationStatus): string {
    const map: Record<HrEvaluationStatus, string> = {
      pending: 'Pendiente', in_progress: 'En curso', completed: 'Completada', cancelled: 'Cancelada',
    };
    return map[s];
  }
  evalStatusClass(s: HrEvaluationStatus): string {
    const map: Record<HrEvaluationStatus, string> = {
      pending: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    };
    return map[s];
  }
}
