import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  AttendanceStatus,
  ContractType,
  EmployeeStatus,
  HrAttendanceCreate,
  HrAttendanceListItem,
  HrEmployee,
  HrEmployeeCreate,
  HrEmployeeListItem,
  HrPosition,
  HrPositionCreate,
  ShiftKind,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

type Tab = 'employees' | 'positions' | 'attendance';

@Component({
  selector: 'app-memorial-hr',
  imports: [CommonModule, FormsModule, DatePipe],
  templateUrl: './hr.component.html',
})
export class MemorialHrComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  tab = signal<Tab>('employees');
  loading = signal(false);

  employees = signal<HrEmployeeListItem[]>([]);
  positions = signal<HrPosition[]>([]);
  attendance = signal<HrAttendanceListItem[]>([]);

  // Filtros
  searchEmp = '';
  filterEmpStatus = '';
  filterEmpPosition = '';
  attDateFrom = '';
  attDateTo = '';
  attEmployeeFilter = '';

  // Forms
  posFormOpen = signal(false);
  editingPosId = signal<string | null>(null);
  posForm: HrPositionCreate = this.emptyPos();
  savingPos = signal(false);
  posFormError = signal('');

  empFormOpen = signal(false);
  editingEmpId = signal<string | null>(null);
  empForm: HrEmployeeCreate = this.emptyEmp();
  savingEmp = signal(false);
  empFormError = signal('');

  attFormOpen = signal(false);
  attForm: HrAttendanceCreate = this.emptyAtt();
  savingAtt = signal(false);
  attFormError = signal('');

  readonly contractTypes: { value: ContractType; label: string }[] = [
    { value: 'indefinido', label: 'Indefinido' },
    { value: 'fijo', label: 'Término fijo' },
    { value: 'obra_labor', label: 'Obra/labor' },
    { value: 'prestacion', label: 'Prestación' },
    { value: 'aprendiz', label: 'Aprendiz' },
    { value: 'otro', label: 'Otro' },
  ];

  readonly shifts: { value: ShiftKind; label: string }[] = [
    { value: 'morning', label: 'Mañana' },
    { value: 'afternoon', label: 'Tarde' },
    { value: 'night', label: 'Noche' },
    { value: 'rotating', label: 'Rotativo' },
    { value: 'administrative', label: 'Administrativo' },
  ];

  readonly empStatuses: { value: EmployeeStatus; label: string }[] = [
    { value: 'active', label: 'Activo' },
    { value: 'on_leave', label: 'En licencia' },
    { value: 'suspended', label: 'Suspendido' },
    { value: 'terminated', label: 'Retirado' },
  ];

  readonly attStatuses: { value: AttendanceStatus; label: string }[] = [
    { value: 'present', label: 'Presente' },
    { value: 'absent', label: 'Ausente' },
    { value: 'late', label: 'Tarde' },
    { value: 'justified', label: 'Justificado' },
    { value: 'vacation', label: 'Vacaciones' },
    { value: 'sick_leave', label: 'Incapacidad' },
  ];

  ngOnInit(): void {
    this.load();
    // Cache de cargos para los picker
    this.memorial.listPositions(true).subscribe({ next: (d) => this.positions.set(d) });
  }

  setTab(t: Tab): void {
    if (this.tab() === t) return;
    this.tab.set(t);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const done = () => this.loading.set(false);
    switch (this.tab()) {
      case 'employees':
        this.memorial.listEmployees({
          status: this.filterEmpStatus || undefined,
          position_id: this.filterEmpPosition || undefined,
          search: this.searchEmp || undefined,
        }).subscribe({ next: (d) => { this.employees.set(d); done(); }, error: done });
        break;
      case 'positions':
        this.memorial.listPositions().subscribe({ next: (d) => { this.positions.set(d); done(); }, error: done });
        break;
      case 'attendance':
        this.memorial.listAttendance({
          employee_id: this.attEmployeeFilter || undefined,
          date_from: this.attDateFrom || undefined,
          date_to: this.attDateTo || undefined,
        }).subscribe({ next: (d) => { this.attendance.set(d); done(); }, error: done });
        // si no hay empleados cargados, cargarlos para el picker
        if (this.employees().length === 0) {
          this.memorial.listEmployees({ status: 'active' }).subscribe({ next: (d) => this.employees.set(d) });
        }
        break;
    }
  }

  // -------- Positions
  openCreatePos(): void {
    this.editingPosId.set(null);
    this.posForm = this.emptyPos();
    this.posFormError.set('');
    this.posFormOpen.set(true);
  }
  openEditPos(p: HrPosition): void {
    this.editingPosId.set(p.id);
    this.posForm = { code: p.code, name: p.name, description: p.description, is_active: p.is_active };
    this.posFormError.set('');
    this.posFormOpen.set(true);
  }
  closePosForm(): void { this.posFormOpen.set(false); }
  submitPos(): void {
    if (!this.posForm.code || !this.posForm.name) {
      this.posFormError.set('Código y nombre son obligatorios.');
      return;
    }
    this.savingPos.set(true);
    this.posFormError.set('');
    const id = this.editingPosId();
    const obs = id
      ? this.memorial.updatePosition(id, { name: this.posForm.name, description: this.posForm.description, is_active: this.posForm.is_active })
      : this.memorial.createPosition(this.posForm);
    obs.subscribe({
      next: (r) => {
        this.savingPos.set(false);
        this.closePosForm();
        this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: r.name });
        this.load();
      },
      error: (err) => {
        this.savingPos.set(false);
        const detail = err?.error?.detail;
        this.posFormError.set(typeof detail === 'string' ? detail : 'Error al guardar.');
      },
    });
  }
  deletePos(p: HrPosition): void {
    if (!confirm(`¿Eliminar el cargo "${p.name}"?`)) return;
    this.memorial.deletePosition(p.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: p.name }); this.load(); },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo eliminar.',
      }),
    });
  }

  // -------- Employees
  openCreateEmp(): void {
    this.editingEmpId.set(null);
    this.empForm = this.emptyEmp();
    this.empFormError.set('');
    this.empFormOpen.set(true);
  }
  openEditEmp(e: HrEmployeeListItem): void {
    this.memorial.getEmployee(e.id).subscribe({
      next: (full) => {
        this.editingEmpId.set(full.id);
        this.empForm = {
          code: full.code,
          first_name: full.first_name, last_name: full.last_name,
          document_type: full.document_type, document_number: full.document_number,
          birth_date: full.birth_date, gender: full.gender,
          email: full.email, phone: full.phone, mobile: full.mobile,
          address: full.address,
          position_id: full.position_id,
          contract_type: full.contract_type as ContractType,
          hire_date: full.hire_date, end_date: full.end_date,
          base_salary: full.base_salary,
          default_shift: full.default_shift,
          status: full.status as EmployeeStatus,
          notes: full.notes,
        };
        this.empFormOpen.set(true);
      },
    });
  }
  closeEmpForm(): void { this.empFormOpen.set(false); }
  submitEmp(): void {
    if (!this.empForm.code || !this.empForm.first_name || !this.empForm.hire_date) {
      this.empFormError.set('Código, nombre y fecha de ingreso son obligatorios.');
      return;
    }
    this.savingEmp.set(true);
    this.empFormError.set('');
    const id = this.editingEmpId();
    const obs = id
      ? this.memorial.updateEmployee(id, this.stripImmutableEmp(this.empForm))
      : this.memorial.createEmployee(this.empForm);
    obs.subscribe({
      next: (r) => {
        this.savingEmp.set(false);
        this.closeEmpForm();
        this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: `${r.first_name} ${r.last_name || ''}`.trim() });
        this.load();
      },
      error: (err) => {
        this.savingEmp.set(false);
        const detail = err?.error?.detail;
        this.empFormError.set(typeof detail === 'string' ? detail : 'Error al guardar.');
      },
    });
  }
  deleteEmp(e: HrEmployeeListItem): void {
    if (!confirm(`¿Eliminar el empleado "${e.first_name} ${e.last_name || ''}"?`)) return;
    this.memorial.deleteEmployee(e.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: e.code }); this.load(); },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo eliminar.',
      }),
    });
  }

  // -------- Attendance
  openCreateAtt(employeeId?: string): void {
    this.attForm = this.emptyAtt();
    if (employeeId) this.attForm.employee_id = employeeId;
    this.attFormError.set('');
    this.attFormOpen.set(true);
  }
  closeAttForm(): void { this.attFormOpen.set(false); }
  submitAtt(): void {
    if (!this.attForm.employee_id || !this.attForm.work_date) {
      this.attFormError.set('Empleado y fecha son obligatorios.');
      return;
    }
    this.savingAtt.set(true);
    this.attFormError.set('');
    this.memorial.upsertAttendance(this.attForm).subscribe({
      next: () => {
        this.savingAtt.set(false);
        this.closeAttForm();
        this.notify.show({ type: 'success', title: 'Asistencia registrada', message: '' });
        this.load();
      },
      error: (err) => {
        this.savingAtt.set(false);
        const detail = err?.error?.detail;
        this.attFormError.set(typeof detail === 'string' ? detail : 'Error al guardar.');
      },
    });
  }

  // -------- Labels
  contractLabel(c: string): string {
    return this.contractTypes.find(x => x.value === c)?.label || c;
  }
  shiftLabel(s: string | null): string {
    if (!s) return '—';
    return this.shifts.find(x => x.value === s)?.label || s;
  }
  empStatusLabel(s: string): string {
    return this.empStatuses.find(x => x.value === s)?.label || s;
  }
  empStatusBadge(s: string): string {
    switch (s) {
      case 'active': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'on_leave': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'suspended': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'terminated': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-700';
    }
  }
  attStatusLabel(s: string): string {
    return this.attStatuses.find(x => x.value === s)?.label || s;
  }
  attStatusBadge(s: string): string {
    switch (s) {
      case 'present': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'late': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'absent': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'justified': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'vacation': case 'sick_leave': return 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  private emptyPos(): HrPositionCreate {
    return { code: '', name: '', is_active: true };
  }

  private emptyEmp(): HrEmployeeCreate {
    return {
      code: '', first_name: '',
      contract_type: 'indefinido',
      hire_date: new Date().toISOString().slice(0, 10),
      base_salary: 0,
      status: 'active',
    };
  }

  private emptyAtt(): HrAttendanceCreate {
    return {
      employee_id: '',
      work_date: new Date().toISOString().slice(0, 10),
      status: 'present',
    };
  }

  private stripImmutableEmp(data: HrEmployeeCreate): Partial<HrEmployeeCreate> {
    const { code, hire_date, ...rest } = data;
    return rest;
  }
}
