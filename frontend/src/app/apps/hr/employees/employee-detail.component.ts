import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HrApiService } from '../../../core/services/hr.service';
import {
  HrContract,
  HrContractCreate,
  HrEmployee,
  HrEmployeeDocument,
  HrEmployeeDocumentCreate,
  HrEmployeeStatus,
} from '../../../core/models/hr.model';
import { NotificationService } from '../../../shared/services/notification.service';

type Tab = 'profile' | 'contracts' | 'documents';

@Component({
  selector: 'app-hr-employee-detail',
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="px-4 sm:px-6 py-6 space-y-5">
      @if (loading()) {
        <p class="text-sm text-slate-500 dark:text-slate-400">Cargando...</p>
      } @else if (employee(); as e) {
        <header class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <a routerLink="/hr/employees" class="text-xs text-brand-600 hover:underline">← Volver a empleados</a>
            <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {{ e.first_name }} {{ e.last_name }}
            </h1>
            <p class="text-sm text-slate-600 dark:text-slate-400 font-mono">
              {{ e.employee_code }}
              @if (e.document_number) { · {{ e.document_type }} {{ e.document_number }} }
            </p>
          </div>
          <span class="text-xs px-3 py-1 rounded-md self-start" [class]="statusClass(e.status)">
            {{ statusLabel(e.status) }}
          </span>
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

          @case ('profile') {
            <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
                <h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Datos personales</h3>
                <dl class="grid grid-cols-2 gap-3 text-sm">
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Fecha nac.</dt><dd>{{ e.birth_date || '—' }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Género</dt><dd>{{ e.gender || '—' }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Email</dt><dd>{{ e.email || '—' }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Celular</dt><dd>{{ e.mobile || '—' }}</dd></div>
                  <div class="col-span-2"><dt class="text-xs text-slate-500 dark:text-slate-400">Dirección</dt><dd>{{ e.address || '—' }}</dd></div>
                </dl>
              </div>
              <div class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
                <h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Datos laborales</h3>
                <dl class="grid grid-cols-2 gap-3 text-sm">
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Fecha ingreso</dt><dd>{{ e.hire_date }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Tipo</dt><dd>{{ employmentLabel(e.employment_type) }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Modalidad</dt><dd>{{ workLabel(e.work_location) }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">País</dt><dd>{{ e.country_code || '—' }}</dd></div>
                </dl>
              </div>
              <div class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 md:col-span-2">
                <h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Contacto de emergencia</h3>
                <dl class="grid grid-cols-3 gap-3 text-sm">
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Nombre</dt><dd>{{ e.emergency_contact_name || '—' }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Teléfono</dt><dd>{{ e.emergency_contact_phone || '—' }}</dd></div>
                  <div><dt class="text-xs text-slate-500 dark:text-slate-400">Parentesco</dt><dd>{{ e.emergency_contact_relationship || '—' }}</dd></div>
                </dl>
              </div>
            </section>
          }

          @case ('contracts') {
            <section class="space-y-3">
              <div class="flex justify-end">
                <button (click)="openNewContract()" type="button"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
                  + Nuevo contrato
                </button>
              </div>

              @if (contracts().length === 0) {
                <p class="text-sm text-slate-500 dark:text-slate-400">Sin contratos registrados.</p>
              } @else {
                <ul class="space-y-2">
                  @for (c of contracts(); track c.id) {
                    <li class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
                      <div class="flex justify-between items-start">
                        <div>
                          <p class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ c.contract_number }}</p>
                          <p class="font-semibold text-slate-900 dark:text-slate-100">{{ contractTypeLabel(c.contract_type) }}</p>
                          <p class="text-sm text-slate-600 dark:text-slate-400">
                            {{ c.start_date }} {{ c.end_date ? '→ ' + c.end_date : '(sin término)' }}
                          </p>
                        </div>
                        <span class="text-xs px-2 py-0.5 rounded-md" [class]="contractStatusClass(c.status)">{{ c.status }}</span>
                      </div>
                      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
                        <div><span class="text-xs text-slate-500 dark:text-slate-400">Salario base</span><p class="font-mono">{{ c.currency }} {{ (+c.base_salary) | number:'1.0-0' }}</p></div>
                        <div><span class="text-xs text-slate-500 dark:text-slate-400">Horas/sem</span><p>{{ c.weekly_hours }}</p></div>
                        <div><span class="text-xs text-slate-500 dark:text-slate-400">Frecuencia</span><p>{{ freqLabel(c.payment_frequency) }}</p></div>
                        <div><span class="text-xs text-slate-500 dark:text-slate-400">EPS</span><p>{{ c.eps_provider || '—' }}</p></div>
                      </div>
                    </li>
                  }
                </ul>
              }
            </section>
          }

          @case ('documents') {
            <section class="space-y-3">
              <div class="flex justify-end">
                <button (click)="openNewDoc()" type="button"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
                  + Nuevo documento
                </button>
              </div>

              @if (documents().length === 0) {
                <p class="text-sm text-slate-500 dark:text-slate-400">Sin documentos registrados.</p>
              } @else {
                <ul class="space-y-2">
                  @for (d of documents(); track d.id) {
                    <li class="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 flex items-center justify-between">
                      <div>
                        <p class="text-xs text-slate-500 dark:text-slate-400">{{ docTypeLabel(d.document_type) }}</p>
                        <p class="font-medium text-slate-900 dark:text-slate-100">{{ d.title }}</p>
                        <p class="text-xs text-slate-500 dark:text-slate-400">
                          @if (d.issue_date) { Emitido {{ d.issue_date }} }
                          @if (d.expiration_date) { · Vence {{ d.expiration_date }} }
                        </p>
                      </div>
                      <div class="flex items-center gap-2">
                        @if (d.file_url) {
                          <a [href]="d.file_url" target="_blank" rel="noopener" class="text-xs text-brand-600 hover:underline">Ver</a>
                        }
                        <span class="text-xs px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">{{ d.status }}</span>
                      </div>
                    </li>
                  }
                </ul>
              }
            </section>
          }
        }
      }

      <!-- Modal nuevo contrato -->
      @if (contractFormOpen() && employee()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeContractForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Nuevo contrato</h3>
            @if (contractFormError()) { <p class="text-sm text-rose-600 mb-3">{{ contractFormError() }}</p> }
            <form (ngSubmit)="saveContract()" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Número contrato *</span>
                <input [(ngModel)]="contractForm.contract_number" name="cn" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo *</span>
                <select [(ngModel)]="contractForm.contract_type" name="ct"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  <option value="indefinido">Indefinido</option>
                  <option value="fijo">Término fijo</option>
                  <option value="obra_labor">Obra/labor</option>
                  <option value="prestacion">Prestación servicios</option>
                  <option value="aprendiz">Aprendizaje</option>
                  <option value="practicante">Practicante</option>
                  <option value="otro">Otro</option>
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Inicio *</span>
                <input type="date" [(ngModel)]="contractForm.start_date" name="sd" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fin</span>
                <input type="date" [(ngModel)]="contractForm.end_date" name="ed"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Salario base *</span>
                <input type="number" [(ngModel)]="contractForm.base_salary" name="bs" min="0" step="1000" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Moneda</span>
                <input [(ngModel)]="contractForm.currency" name="cur" maxlength="3"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm uppercase" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Aux. transporte</span>
                <input type="number" [(ngModel)]="contractForm.transport_allowance" name="ta" min="0" step="1000"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Horas/sem</span>
                <input type="number" [(ngModel)]="contractForm.weekly_hours" name="wh" min="0" max="168" step="0.5"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">EPS</span>
                <input [(ngModel)]="contractForm.eps_provider" name="eps"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">AFP / Pensión</span>
                <input [(ngModel)]="contractForm.pension_provider" name="pen"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Banco</span>
                <input [(ngModel)]="contractForm.bank_name" name="bn"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Cuenta bancaria</span>
                <input [(ngModel)]="contractForm.bank_account_number" name="ban"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <div class="sm:col-span-2 flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeContractForm()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="savingContract()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ savingContract() ? 'Guardando...' : 'Crear contrato' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }

      <!-- Modal nuevo documento -->
      @if (docFormOpen() && employee()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
             (click)="$event.target === $event.currentTarget && closeDocForm()">
          <div class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Nuevo documento</h3>
            @if (docFormError()) { <p class="text-sm text-rose-600 mb-3">{{ docFormError() }}</p> }
            <form (ngSubmit)="saveDoc()" class="space-y-3">
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Tipo *</span>
                <select [(ngModel)]="docForm.document_type" name="dt" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                  @for (t of docTypes; track t.value) {
                    <option [value]="t.value">{{ t.label }}</option>
                  }
                </select>
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Título *</span>
                <input [(ngModel)]="docForm.title" name="dtitle" required
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">URL del archivo</span>
                <input [(ngModel)]="docForm.file_url" name="durl" placeholder="https://..."
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fecha emisión</span>
                <input type="date" [(ngModel)]="docForm.issue_date" name="dissue"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <label class="block">
                <span class="text-xs text-slate-600 dark:text-slate-400">Fecha vencimiento</span>
                <input type="date" [(ngModel)]="docForm.expiration_date" name="dexp"
                  class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
              </label>
              <div class="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
                <button type="button" (click)="closeDocForm()"
                  class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm">Cancelar</button>
                <button type="submit" [disabled]="savingDoc()"
                  class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
                  {{ savingDoc() ? 'Guardando...' : 'Guardar' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }
    </div>
  `,
})
export class HrEmployeeDetailComponent implements OnInit {
  private readonly hr = inject(HrApiService);
  private readonly notify = inject(NotificationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly tabs: { value: Tab; label: string }[] = [
    { value: 'profile', label: 'Ficha' },
    { value: 'contracts', label: 'Contratos' },
    { value: 'documents', label: 'Documentos' },
  ];
  readonly docTypes: { value: string; label: string }[] = [
    { value: 'resume', label: 'Hoja de vida' },
    { value: 'contract', label: 'Contrato' },
    { value: 'id_copy', label: 'Copia documento ID' },
    { value: 'eps_affiliation', label: 'Afiliación EPS' },
    { value: 'pension_affiliation', label: 'Afiliación pensión' },
    { value: 'severance_affiliation', label: 'Afiliación cesantías' },
    { value: 'arl_affiliation', label: 'Afiliación ARL' },
    { value: 'compensation_fund_affiliation', label: 'Caja de compensación' },
    { value: 'medical_exam', label: 'Examen médico' },
    { value: 'background_check', label: 'Verificación antecedentes' },
    { value: 'study_certificate', label: 'Certificado estudios' },
    { value: 'work_certificate', label: 'Certificado laboral' },
    { value: 'training_certificate', label: 'Certificado capacitación' },
    { value: 'other', label: 'Otro' },
  ];

  tab = signal<Tab>('profile');
  loading = signal(true);
  employee = signal<HrEmployee | null>(null);
  contracts = signal<HrContract[]>([]);
  documents = signal<HrEmployeeDocument[]>([]);

  contractFormOpen = signal(false);
  savingContract = signal(false);
  contractFormError = signal('');
  contractForm: HrContractCreate = this.emptyContract();

  docFormOpen = signal(false);
  savingDoc = signal(false);
  docFormError = signal('');
  docForm: HrEmployeeDocumentCreate = this.emptyDoc();

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) { this.router.navigate(['/hr/employees']); return; }
    this.load(id);
  }

  private load(id: string): void {
    this.loading.set(true);
    this.hr.getEmployee(id).subscribe({
      next: (e) => { this.employee.set(e); this.loading.set(false); },
      error: () => { this.loading.set(false); this.router.navigate(['/hr/employees']); },
    });
    this.hr.listContracts({ employee_id: id }).subscribe({ next: (r) => this.contracts.set(r) });
    this.hr.listDocuments({ employee_id: id }).subscribe({ next: (r) => this.documents.set(r) });
  }

  emptyContract(): HrContractCreate {
    const e = this.employee();
    return {
      employee_id: e?.id || '',
      contract_number: '',
      contract_type: 'indefinido',
      start_date: new Date().toISOString().slice(0, 10),
      end_date: null,
      base_salary: '0',
      currency: 'COP',
      payment_frequency: 'monthly',
      weekly_hours: '48',
      transport_allowance: '0',
    };
  }

  emptyDoc(): HrEmployeeDocumentCreate {
    return {
      employee_id: this.employee()?.id || '',
      document_type: 'resume',
      title: '',
    };
  }

  openNewContract(): void {
    this.contractForm = this.emptyContract();
    this.contractFormError.set('');
    this.contractFormOpen.set(true);
  }
  closeContractForm(): void { this.contractFormOpen.set(false); }

  saveContract(): void {
    this.savingContract.set(true);
    this.hr.createContract(this.contractForm).subscribe({
      next: (c) => {
        this.contracts.set([c, ...this.contracts()]);
        this.savingContract.set(false);
        this.contractFormOpen.set(false);
        this.notify.show({ type: 'success', title: 'Creado', message: c.contract_number });
      },
      error: (err) => {
        this.savingContract.set(false);
        this.contractFormError.set(err?.error?.detail || 'No se pudo crear.');
      },
    });
  }

  openNewDoc(): void {
    this.docForm = this.emptyDoc();
    this.docFormError.set('');
    this.docFormOpen.set(true);
  }
  closeDocForm(): void { this.docFormOpen.set(false); }

  saveDoc(): void {
    this.savingDoc.set(true);
    this.hr.createDocument(this.docForm).subscribe({
      next: (d) => {
        this.documents.set([d, ...this.documents()]);
        this.savingDoc.set(false);
        this.docFormOpen.set(false);
        this.notify.show({ type: 'success', title: 'Guardado', message: d.title });
      },
      error: (err) => {
        this.savingDoc.set(false);
        this.docFormError.set(err?.error?.detail || 'No se pudo guardar.');
      },
    });
  }

  statusLabel(s: HrEmployeeStatus): string {
    const map = { active: 'Activo', on_leave: 'Licencia', suspended: 'Suspendido', terminated: 'Terminado' };
    return map[s];
  }
  statusClass(s: HrEmployeeStatus): string {
    const map = {
      active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      on_leave: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      suspended: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      terminated: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    };
    return map[s];
  }
  employmentLabel(t: string): string {
    const map: Record<string, string> = {
      full_time: 'Tiempo completo', part_time: 'Medio tiempo',
      intern: 'Practicante', contractor: 'Contratista', temporary: 'Temporal',
    };
    return map[t] || t;
  }
  workLabel(t: string): string {
    const map: Record<string, string> = { onsite: 'Presencial', remote: 'Remoto', hybrid: 'Híbrido' };
    return map[t] || t;
  }
  contractTypeLabel(t: string): string {
    const map: Record<string, string> = {
      indefinido: 'Indefinido', fijo: 'Término fijo', obra_labor: 'Obra/labor',
      prestacion: 'Prestación servicios', aprendiz: 'Aprendizaje',
      practicante: 'Practicante', otro: 'Otro',
    };
    return map[t] || t;
  }
  freqLabel(f: string): string {
    const map: Record<string, string> = { monthly: 'Mensual', biweekly: 'Quincenal', weekly: 'Semanal' };
    return map[f] || f;
  }
  contractStatusClass(s: string): string {
    const map: Record<string, string> = {
      active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
      draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      suspended: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
      terminated: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
      expired: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    };
    return map[s] || '';
  }
  docTypeLabel(t: string): string {
    return this.docTypes.find((x) => x.value === t)?.label || t;
  }
}
