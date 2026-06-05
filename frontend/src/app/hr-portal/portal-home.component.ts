import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  HrPortalService,
  PortalContract,
  PortalDocument,
  PortalEmployee,
  PortalEvaluation,
  PortalEvaluationDetail,
  PortalLeave,
  PortalPayroll,
  PortalTraining,
  PortalVacationBalance,
  PortalVacationRequest,
} from './portal.service';

type Tab = 'profile' | 'payrolls' | 'vacations' | 'leaves' | 'evaluations' | 'training' | 'documents';

@Component({
  selector: 'app-hr-portal-home',
  imports: [CommonModule, FormsModule, DatePipe, DecimalPipe],
  template: `
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div class="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <p class="text-xs text-slate-500 dark:text-slate-400">{{ employee()?.organization_name }}</p>
            <h1 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Portal del empleado</h1>
          </div>
          <div class="flex items-center gap-3">
            <div class="text-right">
              <p class="text-sm text-slate-700 dark:text-slate-300">{{ fullName() }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400 font-mono">{{ employee()?.employee_code }}</p>
            </div>
            <button (click)="logout()" type="button"
              class="text-xs text-rose-600 hover:underline">Cerrar sesión</button>
          </div>
        </div>
      </header>

      <nav class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div class="max-w-6xl mx-auto px-4 flex gap-1 overflow-x-auto">
          @for (t of tabs; track t.value) {
            <button type="button" (click)="setTab(t.value)"
              class="px-4 py-3 text-sm border-b-2 whitespace-nowrap"
              [class.border-brand-600]="tab() === t.value"
              [class.text-brand-700]="tab() === t.value"
              [class.dark:text-brand-300]="tab() === t.value"
              [class.border-transparent]="tab() !== t.value"
              [class.text-slate-600]="tab() !== t.value"
              [class.dark:text-slate-400]="tab() !== t.value">
              {{ t.label }}
            </button>
          }
        </div>
      </nav>

      <main class="max-w-6xl mx-auto px-4 py-6">

        @if (loading()) {
          <p class="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
        } @else if (!employee()) {
          <p class="text-sm text-rose-600">No se pudo cargar tu información.</p>
        } @else {

          @switch (tab()) {

            <!-- ============ Profile ============ -->
            @case ('profile') {
              <section class="grid gap-4 md:grid-cols-2">
                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                  <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Datos personales</h2>
                  <dl class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-slate-800 dark:text-slate-200">
                    <div><dt class="text-xs text-slate-500 dark:text-slate-400">Email</dt><dd>{{ employee()?.email || '—' }}</dd></div>
                    <div><dt class="text-xs text-slate-500 dark:text-slate-400">Celular</dt><dd>{{ employee()?.mobile || '—' }}</dd></div>
                    <div class="sm:col-span-2"><dt class="text-xs text-slate-500 dark:text-slate-400">Dirección</dt><dd>{{ employee()?.address || '—' }}</dd></div>
                  </dl>
                </div>

                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                  <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Datos laborales</h2>
                  <dl class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-slate-800 dark:text-slate-200">
                    <div><dt class="text-xs text-slate-500 dark:text-slate-400">Departamento</dt><dd>{{ employee()?.department_name || '—' }}</dd></div>
                    <div><dt class="text-xs text-slate-500 dark:text-slate-400">Cargo</dt><dd>{{ employee()?.position_name || '—' }}</dd></div>
                    <div><dt class="text-xs text-slate-500 dark:text-slate-400">Fecha de ingreso</dt><dd>{{ employee()?.hire_date | date:'mediumDate' }}</dd></div>
                    <div><dt class="text-xs text-slate-500 dark:text-slate-400">Modalidad</dt><dd>{{ workLocLabel(employee()?.work_location || '') }}</dd></div>
                  </dl>
                </div>

                @if (contracts().length > 0) {
                  <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4 md:col-span-2">
                    <h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Mis contratos</h2>
                    <ul class="space-y-2">
                      @for (c of contracts(); track c.id) {
                        <li class="rounded-md border border-slate-200 dark:border-slate-700 p-3">
                          <div class="flex justify-between items-start">
                            <div>
                              <p class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ c.contract_number }}</p>
                              <p class="font-medium text-slate-900 dark:text-slate-100">{{ c.contract_type | titlecase }}</p>
                              <p class="text-xs text-slate-600 dark:text-slate-400">
                                {{ c.start_date | date:'mediumDate' }} {{ c.end_date ? '→ ' + (c.end_date | date:'mediumDate') : '· sin término' }}
                              </p>
                            </div>
                            <div class="text-right">
                              <p class="text-xs text-slate-500 dark:text-slate-400">Salario</p>
                              <p class="font-mono font-semibold text-slate-900 dark:text-slate-100">{{ c.currency }} {{ +c.base_salary | number:'1.0-0' }}</p>
                            </div>
                          </div>
                        </li>
                      }
                    </ul>
                  </div>
                }
              </section>
            }

            <!-- ============ Payrolls ============ -->
            @case ('payrolls') {
              @if (payrolls().length === 0) {
                <p class="text-sm text-slate-500 dark:text-slate-400">Aún no hay desprendibles disponibles.</p>
              } @else {
                <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
                  <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
                    <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                      <tr>
                        <th class="text-left px-3 py-2 font-medium">Período</th>
                        <th class="text-left px-3 py-2 font-medium">Rango</th>
                        <th class="text-right px-3 py-2 font-medium">Devengado</th>
                        <th class="text-right px-3 py-2 font-medium">Deducciones</th>
                        <th class="text-right px-3 py-2 font-medium">Neto</th>
                        <th class="text-left px-3 py-2 font-medium">Estado</th>
                        <th class="text-right px-3 py-2 font-medium">PDF</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                      @for (p of payrolls(); track p.id) {
                        <tr>
                          <td class="px-3 py-2">
                            <div class="font-medium">{{ p.period_name }}</div>
                            <div class="text-xs text-slate-500 dark:text-slate-400 font-mono">{{ p.period_code }}</div>
                          </td>
                          <td class="px-3 py-2 text-xs">{{ p.period_start | date:'mediumDate' }} → {{ p.period_end | date:'mediumDate' }}</td>
                          <td class="px-3 py-2 text-right font-mono text-xs">$ {{ +p.total_earnings | number:'1.0-0' }}</td>
                          <td class="px-3 py-2 text-right font-mono text-xs text-rose-600">$ {{ +p.total_deductions | number:'1.0-0' }}</td>
                          <td class="px-3 py-2 text-right font-mono font-semibold text-emerald-700 dark:text-emerald-300">$ {{ +p.net_amount | number:'1.0-0' }}</td>
                          <td class="px-3 py-2"><span class="text-xs px-2 py-0.5 rounded-md" [class]="statusClass(p.status)">{{ p.status }}</span></td>
                          <td class="px-3 py-2 text-right">
                            <button (click)="downloadPdf(p)" type="button" class="text-xs text-brand-600 hover:underline">Descargar</button>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            }

            <!-- ============ Vacations ============ -->
            @case ('vacations') {
              <section class="space-y-4">
                <div class="grid gap-3 sm:grid-cols-2">
                  @for (b of balances(); track b.period_year) {
                    <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                      <p class="text-xs text-slate-500 dark:text-slate-400">Saldo {{ b.period_year }}</p>
                      <p class="text-3xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">{{ +b.days_available | number:'1.0-2' }} <span class="text-sm font-normal text-slate-500 dark:text-slate-400">días disponibles</span></p>
                      <dl class="grid grid-cols-2 gap-2 mt-3 text-xs text-slate-600 dark:text-slate-400">
                        <div><dt>Causados</dt><dd class="font-mono text-slate-900 dark:text-slate-100">{{ b.days_accrued }}</dd></div>
                        <div><dt>Disfrutados</dt><dd class="font-mono text-slate-900 dark:text-slate-100">{{ b.days_taken }}</dd></div>
                        <div><dt>Pendientes</dt><dd class="font-mono text-slate-900 dark:text-slate-100">{{ b.days_pending }}</dd></div>
                        <div><dt>Compensados</dt><dd class="font-mono text-slate-900 dark:text-slate-100">{{ b.days_compensated }}</dd></div>
                      </dl>
                    </div>
                  }
                </div>

                <div class="flex justify-end">
                  <button (click)="openVacForm()" type="button"
                    class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
                    + Solicitar vacaciones
                  </button>
                </div>

                @if (vacationRequests().length === 0) {
                  <p class="text-sm text-slate-500 dark:text-slate-400">Sin solicitudes registradas.</p>
                } @else {
                  <div class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
                    <table class="min-w-full text-sm text-slate-800 dark:text-slate-200">
                      <thead class="bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300">
                        <tr>
                          <th class="text-left px-3 py-2 font-medium">N°</th>
                          <th class="text-left px-3 py-2 font-medium">Inicio</th>
                          <th class="text-left px-3 py-2 font-medium">Fin</th>
                          <th class="text-right px-3 py-2 font-medium">Días</th>
                          <th class="text-left px-3 py-2 font-medium">Estado</th>
                          <th class="text-left px-3 py-2 font-medium">Motivo</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                        @for (r of vacationRequests(); track r.id) {
                          <tr>
                            <td class="px-3 py-2 font-mono text-xs">{{ r.request_number }}</td>
                            <td class="px-3 py-2 text-xs">{{ r.start_date | date:'mediumDate' }}</td>
                            <td class="px-3 py-2 text-xs">{{ r.end_date | date:'mediumDate' }}</td>
                            <td class="px-3 py-2 text-right">{{ r.days_count }}</td>
                            <td class="px-3 py-2"><span class="text-xs px-2 py-0.5 rounded-md" [class]="vacStatusClass(r.status)">{{ vacStatusLabel(r.status) }}</span></td>
                            <td class="px-3 py-2 text-xs">{{ r.request_reason || '—' }}</td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
                }
              </section>
            }

            <!-- ============ Leaves ============ -->
            @case ('leaves') {
              @if (leaves().length === 0) {
                <p class="text-sm text-slate-500 dark:text-slate-400">Sin registros de incapacidades o licencias.</p>
              } @else {
                <ul class="space-y-2">
                  @for (l of leaves(); track l.id) {
                    <li class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ l.leave_number }}</p>
                        <p class="font-medium text-slate-900 dark:text-slate-100">{{ leaveTypeLabel(l.leave_type) }}</p>
                        <p class="text-xs text-slate-600 dark:text-slate-400">{{ l.start_date | date:'mediumDate' }} → {{ l.end_date | date:'mediumDate' }} · {{ l.days_count }} días</p>
                      </div>
                      <div class="text-right text-xs">
                        <span class="px-2 py-0.5 rounded-md" [class]="leaveStatusClass(l.status)">{{ l.status }}</span>
                        @if (l.is_paid) { <p class="mt-1 text-emerald-700 dark:text-emerald-300">Pagada {{ l.paid_percentage ? '· ' + l.paid_percentage + '%' : '' }}</p> }
                      </div>
                    </li>
                  }
                </ul>
              }
            }

            <!-- ============ Evaluations ============ -->
            @case ('evaluations') {
              @if (evaluations().length === 0) {
                <p class="text-sm text-slate-500 dark:text-slate-400">No tienes evaluaciones pendientes.</p>
              } @else {
                <ul class="space-y-2">
                  @for (e of evaluations(); track e.id) {
                    <li class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                      <div class="flex justify-between items-start">
                        <div>
                          <p class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ e.cycle_code }}</p>
                          <p class="font-medium text-slate-900 dark:text-slate-100">{{ e.cycle_name }}</p>
                          <p class="text-xs text-slate-600 dark:text-slate-400 mt-1">
                            Auto: {{ e.self_completed ? '✓' : '—' }} ·
                            Jefe: {{ e.supervisor_completed ? '✓' : '—' }}
                            @if (e.overall_score) { · Overall {{ e.overall_score }} }
                          </p>
                        </div>
                        <div class="flex flex-col gap-2 items-end">
                          <span class="text-xs px-2 py-0.5 rounded-md" [class]="evalStatusClass(e.status)">{{ evalStatusLabel(e.status) }}</span>
                          @if (!e.self_completed) {
                            <button (click)="openRespond(e)" type="button" class="text-xs text-brand-600 hover:underline">Responder mi auto-evaluación</button>
                          }
                        </div>
                      </div>
                    </li>
                  }
                </ul>
              }
            }

            <!-- ============ Training ============ -->
            @case ('training') {
              @if (trainings().length === 0) {
                <p class="text-sm text-slate-500 dark:text-slate-400">No tienes capacitaciones registradas.</p>
              } @else {
                <ul class="space-y-2">
                  @for (t of trainings(); track t.id) {
                    <li class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                      <div class="flex justify-between items-start">
                        <div>
                          <p class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ t.course_code }}</p>
                          <p class="font-medium text-slate-900 dark:text-slate-100">{{ t.course_name }}</p>
                          <p class="text-xs text-slate-600 dark:text-slate-400">
                            {{ t.course_category }}
                            @if (t.duration_hours) { · {{ t.duration_hours }} h }
                            @if (t.scheduled_date) { · Programado {{ t.scheduled_date | date:'mediumDate' }} }
                          </p>
                        </div>
                        <div class="text-right">
                          <span class="text-xs px-2 py-0.5 rounded-md" [class]="trainStatusClass(t.completion_status)">{{ trainStatusLabel(t.completion_status) }}</span>
                          @if (t.score) { <p class="text-xs text-slate-600 dark:text-slate-400 mt-1">Puntaje: <span class="font-mono">{{ t.score }}</span></p> }
                          @if (t.certificate_url) {
                            <a [href]="t.certificate_url" target="_blank" rel="noopener" class="text-xs text-brand-600 hover:underline">Certificado</a>
                          }
                        </div>
                      </div>
                    </li>
                  }
                </ul>
              }
            }

            <!-- ============ Documents ============ -->
            @case ('documents') {
              @if (documents().length === 0) {
                <p class="text-sm text-slate-500 dark:text-slate-400">Sin documentos disponibles.</p>
              } @else {
                <ul class="space-y-2">
                  @for (d of documents(); track d.id) {
                    <li class="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 p-3 flex items-center justify-between">
                      <div>
                        <p class="text-xs text-slate-500 dark:text-slate-400">{{ docTypeLabel(d.document_type) }}</p>
                        <p class="font-medium text-slate-900 dark:text-slate-100">{{ d.title }}</p>
                        @if (d.issue_date) { <p class="text-xs text-slate-500 dark:text-slate-400">Emitido {{ d.issue_date | date:'mediumDate' }}</p> }
                        @if (d.expiration_date) { <p class="text-xs text-slate-500 dark:text-slate-400">Vence {{ d.expiration_date | date:'mediumDate' }}</p> }
                      </div>
                      @if (d.file_url) {
                        <a [href]="d.file_url" target="_blank" rel="noopener" class="text-xs text-brand-600 hover:underline">Ver</a>
                      }
                    </li>
                  }
                </ul>
              }
            }
          }
        }
      </main>

      <!-- Modal solicitar vacaciones -->
      @if (vacFormOpen()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeVacForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Solicitar vacaciones</h3>
            @if (vacError()) { <p class="text-sm text-rose-600 mb-3">{{ vacError() }}</p> }
            <form (ngSubmit)="submitVac()" class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Inicio *</span>
                  <input type="date" [(ngModel)]="vacForm.start_date" name="sd" required (change)="updateDays()"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
                <label class="block">
                  <span class="text-xs text-slate-600 dark:text-slate-400">Fin *</span>
                  <input type="date" [(ngModel)]="vacForm.end_date" name="ed" required (change)="updateDays()"
                    class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </label>
              </div>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Días *</span>
                <input type="number" step="0.5" min="0" [(ngModel)]="vacForm.days_count" name="dc" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Motivo</span>
                <textarea [(ngModel)]="vacForm.request_reason" name="rr" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
              <div class="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeVacForm()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="vacSaving()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ vacSaving() ? '...' : 'Solicitar' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }

      <!-- Modal responder evaluación -->
      @if (respondOpen() && evalDetail(); as detail) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeRespond()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1">Auto-evaluación</h3>
            <p class="text-sm text-slate-600 dark:text-slate-400 mb-4">
              {{ detail.cycle_name }} · escala {{ detail.scale_min }} - {{ detail.scale_max }}
            </p>
            @if (respondError()) { <p class="text-sm text-rose-600 mb-3">{{ respondError() }}</p> }
            <div class="space-y-3">
              @for (comp of detail.competencies; track comp.code) {
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-sm font-medium text-slate-900 dark:text-slate-100">{{ comp.name }}</span>
                    @if (comp.weight !== null) {
                      <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">peso: {{ comp.weight }}</span>
                    }
                  </div>
                  @if (comp.description) {
                    <p class="text-xs text-slate-500 dark:text-slate-400 mb-1">{{ comp.description }}</p>
                  }
                  <input type="number" [min]="+detail.scale_min" [max]="+detail.scale_max" step="0.5"
                    [(ngModel)]="scoresMap[comp.code]"
                    class="w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
                </div>
              }
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Comentarios</span>
                <textarea [(ngModel)]="evalComments" rows="3"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"></textarea>
              </label>
            </div>
            <div class="flex justify-end gap-2 pt-3 mt-4 border-t border-slate-200 dark:border-slate-700">
              <button type="button" (click)="closeRespond()"
                class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
              <button type="button" (click)="submitEvalResponse()" [disabled]="respondSaving()"
                class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                {{ respondSaving() ? 'Enviando...' : 'Enviar' }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrPortalHomeComponent implements OnInit {
  private readonly portal = inject(HrPortalService);
  private readonly router = inject(Router);

  readonly tabs: { value: Tab; label: string }[] = [
    { value: 'profile', label: 'Mi perfil' },
    { value: 'payrolls', label: 'Desprendibles' },
    { value: 'vacations', label: 'Vacaciones' },
    { value: 'leaves', label: 'Incapacidades' },
    { value: 'evaluations', label: 'Evaluaciones' },
    { value: 'training', label: 'Capacitaciones' },
    { value: 'documents', label: 'Documentos' },
  ];

  tab = signal<Tab>('profile');
  loading = signal(true);

  employee = signal<PortalEmployee | null>(null);
  contracts = signal<PortalContract[]>([]);
  payrolls = signal<PortalPayroll[]>([]);
  balances = signal<PortalVacationBalance[]>([]);
  vacationRequests = signal<PortalVacationRequest[]>([]);
  leaves = signal<PortalLeave[]>([]);
  evaluations = signal<PortalEvaluation[]>([]);
  trainings = signal<PortalTraining[]>([]);
  documents = signal<PortalDocument[]>([]);

  fullName = computed(() => {
    const e = this.employee();
    if (!e) return '';
    return [e.first_name, e.last_name].filter(Boolean).join(' ').trim();
  });

  vacFormOpen = signal(false);
  vacSaving = signal(false);
  vacError = signal('');
  vacForm = {
    request_type: 'paid',
    start_date: new Date().toISOString().slice(0, 10),
    end_date: new Date().toISOString().slice(0, 10),
    days_count: '1',
    request_reason: '',
  };

  respondOpen = signal(false);
  respondSaving = signal(false);
  respondError = signal('');
  evalDetail = signal<PortalEvaluationDetail | null>(null);
  scoresMap: Record<string, number> = {};
  evalComments = '';

  ngOnInit(): void {
    if (!this.portal.getToken()) {
      this.router.navigate(['/hr-portal']);
      return;
    }
    this.portal.me().subscribe({
      next: (e) => { this.employee.set(e); this.loading.set(false); },
      error: () => { this.portal.clear(); this.router.navigate(['/hr-portal']); },
    });
    this.portal.contracts().subscribe({ next: (r) => this.contracts.set(r) });
    this.portal.payrolls().subscribe({ next: (r) => this.payrolls.set(r) });
    this.portal.vacationBalances().subscribe({ next: (r) => this.balances.set(r) });
    this.portal.vacationRequests().subscribe({ next: (r) => this.vacationRequests.set(r) });
    this.portal.leaves().subscribe({ next: (r) => this.leaves.set(r) });
    this.portal.evaluations().subscribe({ next: (r) => this.evaluations.set(r) });
    this.portal.trainings().subscribe({ next: (r) => this.trainings.set(r) });
    this.portal.documents().subscribe({ next: (r) => this.documents.set(r) });
  }

  setTab(t: Tab): void { this.tab.set(t); }

  logout(): void {
    this.portal.clear();
    this.router.navigate(['/hr-portal']);
  }

  downloadPdf(p: PortalPayroll): void {
    this.portal.downloadPayrollPdf(p.id).subscribe({
      next: ({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `desprendible-${p.period_code}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      },
    });
  }

  // Vacations form
  openVacForm(): void {
    this.vacForm = {
      request_type: 'paid',
      start_date: new Date().toISOString().slice(0, 10),
      end_date: new Date().toISOString().slice(0, 10),
      days_count: '1',
      request_reason: '',
    };
    this.vacError.set('');
    this.vacFormOpen.set(true);
  }
  closeVacForm(): void { this.vacFormOpen.set(false); }
  updateDays(): void {
    if (!this.vacForm.start_date || !this.vacForm.end_date) return;
    const s = new Date(this.vacForm.start_date);
    const e = new Date(this.vacForm.end_date);
    const diff = Math.max(0, (e.getTime() - s.getTime()) / 86400000 + 1);
    this.vacForm.days_count = String(diff);
  }
  submitVac(): void {
    this.vacSaving.set(true);
    this.portal.createVacationRequest({
      request_type: this.vacForm.request_type,
      start_date: this.vacForm.start_date,
      end_date: this.vacForm.end_date,
      days_count: this.vacForm.days_count,
      request_reason: this.vacForm.request_reason || undefined,
    }).subscribe({
      next: () => {
        this.vacSaving.set(false);
        this.vacFormOpen.set(false);
        this.portal.vacationRequests().subscribe({ next: (r) => this.vacationRequests.set(r) });
        this.portal.vacationBalances().subscribe({ next: (r) => this.balances.set(r) });
      },
      error: (err) => {
        this.vacSaving.set(false);
        this.vacError.set(err?.error?.detail || 'No se pudo crear la solicitud.');
      },
    });
  }

  // Evaluations respond
  openRespond(e: PortalEvaluation): void {
    this.portal.evaluationDetail(e.id).subscribe({
      next: (d) => {
        this.evalDetail.set(d);
        this.scoresMap = {};
        for (const comp of d.competencies) this.scoresMap[comp.code] = +d.scale_min;
        this.evalComments = '';
        this.respondError.set('');
        this.respondOpen.set(true);
      },
    });
  }
  closeRespond(): void { this.respondOpen.set(false); }
  submitEvalResponse(): void {
    const detail = this.evalDetail();
    if (!detail) return;
    this.respondSaving.set(true);
    this.portal.submitEvaluationResponse(detail.id, {
      evaluator_type: 'self',
      scores: { ...this.scoresMap },
      comments: this.evalComments || null,
    }).subscribe({
      next: () => {
        this.respondSaving.set(false);
        this.respondOpen.set(false);
        this.portal.evaluations().subscribe({ next: (r) => this.evaluations.set(r) });
      },
      error: (err) => {
        this.respondSaving.set(false);
        this.respondError.set(err?.error?.detail || 'No se pudo enviar.');
      },
    });
  }

  // Labels
  workLocLabel(t: string): string {
    const map: Record<string, string> = { onsite: 'Presencial', remote: 'Remoto', hybrid: 'Híbrido' };
    return map[t] || t;
  }
  statusClass(s: string): string {
    const map: Record<string, string> = {
      paid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      approved: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
      closed: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    };
    return map[s] || 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
  }
  vacStatusLabel(s: string): string {
    const map: Record<string, string> = {
      pending: 'Pendiente', approved: 'Aprobada', rejected: 'Rechazada',
      cancelled: 'Cancelada', completed: 'Completada',
    };
    return map[s] || s;
  }
  vacStatusClass(s: string): string {
    const map: Record<string, string> = {
      pending: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      cancelled: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
    };
    return map[s] || '';
  }
  leaveTypeLabel(t: string): string {
    const map: Record<string, string> = {
      medical: 'Incapacidad médica', maternity: 'Licencia maternidad', paternity: 'Licencia paternidad',
      bereavement: 'Luto', unpaid: 'No remunerada', paid_other: 'Pagada (otros)',
      study: 'Estudio', remunerated_permit: 'Permiso remunerado',
    };
    return map[t] || t;
  }
  leaveStatusClass(s: string): string {
    const map: Record<string, string> = {
      active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
      cancelled: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    };
    return map[s] || '';
  }
  evalStatusLabel(s: string): string {
    const map: Record<string, string> = {
      pending: 'Pendiente', in_progress: 'En curso', completed: 'Completada', cancelled: 'Cancelada',
    };
    return map[s] || s;
  }
  evalStatusClass(s: string): string {
    const map: Record<string, string> = {
      pending: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      cancelled: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    };
    return map[s] || '';
  }
  trainStatusLabel(s: string): string {
    const map: Record<string, string> = {
      enrolled: 'Inscrito', in_progress: 'En curso', completed: 'Completado',
      failed: 'No aprobado', cancelled: 'Cancelado',
    };
    return map[s] || s;
  }
  trainStatusClass(s: string): string {
    const map: Record<string, string> = {
      enrolled: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      failed: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      cancelled: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    };
    return map[s] || '';
  }
  docTypeLabel(t: string): string {
    const map: Record<string, string> = {
      resume: 'Hoja de vida', contract: 'Contrato', id_copy: 'Documento ID',
      eps_affiliation: 'Afiliación EPS', pension_affiliation: 'Afiliación pensión',
      severance_affiliation: 'Afiliación cesantías', arl_affiliation: 'Afiliación ARL',
      compensation_fund_affiliation: 'Caja de compensación',
      medical_exam: 'Examen médico', background_check: 'Verificación antecedentes',
      study_certificate: 'Certificado estudios', work_certificate: 'Certificado laboral',
      training_certificate: 'Certificado capacitación', other: 'Otro',
    };
    return map[t] || t;
  }
}
