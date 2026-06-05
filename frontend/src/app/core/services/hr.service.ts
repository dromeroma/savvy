import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  HrAttendance,
  HrAttendanceCreate,
  HrAttendanceListItem,
  HrContract,
  HrContractCreate,
  HrDepartment,
  HrDepartmentCreate,
  HrEmployee,
  HrEmployeeCreate,
  HrEmployeeDocument,
  HrEmployeeDocumentCreate,
  HrEmployeeListItem,
  HrEmployeeUpdate,
  HrLeave,
  HrLeaveCreate,
  HrPosition,
  HrPositionCreate,
  HrShift,
  HrShiftCreate,
  HrVacationBalance,
  HrVacationBalanceAdjust,
  HrVacationRequest,
  HrVacationRequestCreate,
} from '../models/hr.model';

@Injectable({ providedIn: 'root' })
export class HrApiService {
  private readonly api = inject(ApiService);

  // ---- Departments ----
  listDepartments(activeOnly = false): Observable<HrDepartment[]> {
    return this.api.get<HrDepartment[]>('/hr/departments', { active_only: activeOnly });
  }
  getDepartment(id: string): Observable<HrDepartment> {
    return this.api.get<HrDepartment>(`/hr/departments/${id}`);
  }
  createDepartment(data: HrDepartmentCreate): Observable<HrDepartment> {
    return this.api.post<HrDepartment>('/hr/departments', data);
  }
  updateDepartment(id: string, data: Partial<HrDepartmentCreate>): Observable<HrDepartment> {
    return this.api.patch<HrDepartment>(`/hr/departments/${id}`, data);
  }
  deleteDepartment(id: string): Observable<void> {
    return this.api.delete(`/hr/departments/${id}`);
  }

  // ---- Positions ----
  listPositions(params?: { active_only?: boolean; department_id?: string }): Observable<HrPosition[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.active_only !== undefined) clean['active_only'] = params.active_only;
    if (params?.department_id) clean['department_id'] = params.department_id;
    return this.api.get<HrPosition[]>('/hr/positions', clean);
  }
  getPosition(id: string): Observable<HrPosition> {
    return this.api.get<HrPosition>(`/hr/positions/${id}`);
  }
  createPosition(data: HrPositionCreate): Observable<HrPosition> {
    return this.api.post<HrPosition>('/hr/positions', data);
  }
  updatePosition(id: string, data: Partial<HrPositionCreate>): Observable<HrPosition> {
    return this.api.patch<HrPosition>(`/hr/positions/${id}`, data);
  }
  deletePosition(id: string): Observable<void> {
    return this.api.delete(`/hr/positions/${id}`);
  }

  // ---- Employees ----
  listEmployees(params?: {
    status?: string; department_id?: string; position_id?: string; search?: string;
  }): Observable<HrEmployeeListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.status) clean['status'] = params.status;
    if (params?.department_id) clean['department_id'] = params.department_id;
    if (params?.position_id) clean['position_id'] = params.position_id;
    if (params?.search) clean['search'] = params.search;
    return this.api.get<HrEmployeeListItem[]>('/hr/employees', clean);
  }
  getEmployee(id: string): Observable<HrEmployee> {
    return this.api.get<HrEmployee>(`/hr/employees/${id}`);
  }
  createEmployee(data: HrEmployeeCreate): Observable<HrEmployee> {
    return this.api.post<HrEmployee>('/hr/employees', data);
  }
  updateEmployee(id: string, data: HrEmployeeUpdate): Observable<HrEmployee> {
    return this.api.patch<HrEmployee>(`/hr/employees/${id}`, data);
  }
  deleteEmployee(id: string): Observable<void> {
    return this.api.delete(`/hr/employees/${id}`);
  }

  // ---- Contracts ----
  listContracts(params?: { employee_id?: string; status?: string }): Observable<HrContract[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrContract[]>('/hr/contracts', clean);
  }
  getContract(id: string): Observable<HrContract> {
    return this.api.get<HrContract>(`/hr/contracts/${id}`);
  }
  createContract(data: HrContractCreate): Observable<HrContract> {
    return this.api.post<HrContract>('/hr/contracts', data);
  }
  updateContract(id: string, data: Partial<HrContractCreate> & { status?: string }): Observable<HrContract> {
    return this.api.patch<HrContract>(`/hr/contracts/${id}`, data);
  }
  deleteContract(id: string): Observable<void> {
    return this.api.delete(`/hr/contracts/${id}`);
  }

  // ---- Documents ----
  listDocuments(params?: { employee_id?: string; document_type?: string }): Observable<HrEmployeeDocument[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.document_type) clean['document_type'] = params.document_type;
    return this.api.get<HrEmployeeDocument[]>('/hr/documents', clean);
  }
  getDocument(id: string): Observable<HrEmployeeDocument> {
    return this.api.get<HrEmployeeDocument>(`/hr/documents/${id}`);
  }
  createDocument(data: HrEmployeeDocumentCreate): Observable<HrEmployeeDocument> {
    return this.api.post<HrEmployeeDocument>('/hr/documents', data);
  }
  updateDocument(id: string, data: Partial<HrEmployeeDocumentCreate> & { status?: string }): Observable<HrEmployeeDocument> {
    return this.api.patch<HrEmployeeDocument>(`/hr/documents/${id}`, data);
  }
  deleteDocument(id: string): Observable<void> {
    return this.api.delete(`/hr/documents/${id}`);
  }

  // ============================================================ Fase 2

  // ---- Shifts ----
  listShifts(activeOnly = false): Observable<HrShift[]> {
    return this.api.get<HrShift[]>('/hr/shifts', { active_only: activeOnly });
  }
  createShift(data: HrShiftCreate): Observable<HrShift> {
    return this.api.post<HrShift>('/hr/shifts', data);
  }
  updateShift(id: string, data: Partial<HrShiftCreate>): Observable<HrShift> {
    return this.api.patch<HrShift>(`/hr/shifts/${id}`, data);
  }
  deleteShift(id: string): Observable<void> {
    return this.api.delete(`/hr/shifts/${id}`);
  }

  // ---- Attendance ----
  listAttendance(params?: {
    employee_id?: string; date_from?: string; date_to?: string;
    status?: string; limit?: number; offset?: number;
  }): Observable<HrAttendanceListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.date_from) clean['date_from'] = params.date_from;
    if (params?.date_to) clean['date_to'] = params.date_to;
    if (params?.status) clean['status'] = params.status;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<HrAttendanceListItem[]>('/hr/attendance', clean);
  }
  upsertAttendance(data: HrAttendanceCreate): Observable<HrAttendance> {
    return this.api.post<HrAttendance>('/hr/attendance', data);
  }
  updateAttendance(id: string, data: Partial<HrAttendanceCreate>): Observable<HrAttendance> {
    return this.api.patch<HrAttendance>(`/hr/attendance/${id}`, data);
  }
  deleteAttendance(id: string): Observable<void> {
    return this.api.delete(`/hr/attendance/${id}`);
  }

  // ---- Vacation balances ----
  listVacationBalances(period_year?: number): Observable<HrVacationBalance[]> {
    const clean: Record<string, string | number> = {};
    if (period_year !== undefined) clean['period_year'] = period_year;
    return this.api.get<HrVacationBalance[]>('/hr/vacation-balances', clean);
  }
  employeeVacationBalances(employeeId: string): Observable<HrVacationBalance[]> {
    return this.api.get<HrVacationBalance[]>(`/hr/employees/${employeeId}/vacation-balances`);
  }
  adjustVacationBalance(employeeId: string, data: HrVacationBalanceAdjust): Observable<HrVacationBalance> {
    return this.api.post<HrVacationBalance>(`/hr/employees/${employeeId}/vacation-balances/adjust`, data);
  }
  runMonthlyAccrual(daysPerMonth = 1.25): Observable<{ accrued_employees: number }> {
    return this.api.post<{ accrued_employees: number }>(`/hr/vacation-balances/accrue?days_per_month=${daysPerMonth}`, {});
  }

  // ---- Vacation requests ----
  listVacationRequests(params?: { employee_id?: string; status?: string }): Observable<HrVacationRequest[]> {
    const clean: Record<string, string> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrVacationRequest[]>('/hr/vacation-requests', clean);
  }
  createVacationRequest(data: HrVacationRequestCreate): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>('/hr/vacation-requests', data);
  }
  approveVacation(rid: string, notes?: string): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>(`/hr/vacation-requests/${rid}/approve`, { notes });
  }
  rejectVacation(rid: string, rejection_reason: string): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>(`/hr/vacation-requests/${rid}/reject`, { rejection_reason });
  }
  cancelVacation(rid: string): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>(`/hr/vacation-requests/${rid}/cancel`, {});
  }

  // ---- Leaves ----
  listLeaves(params?: { employee_id?: string; leave_type?: string; status?: string }): Observable<HrLeave[]> {
    const clean: Record<string, string> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.leave_type) clean['leave_type'] = params.leave_type;
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrLeave[]>('/hr/leaves', clean);
  }
  getLeave(id: string): Observable<HrLeave> {
    return this.api.get<HrLeave>(`/hr/leaves/${id}`);
  }
  createLeave(data: HrLeaveCreate): Observable<HrLeave> {
    return this.api.post<HrLeave>('/hr/leaves', data);
  }
  updateLeave(id: string, data: Partial<HrLeaveCreate> & { status?: string }): Observable<HrLeave> {
    return this.api.patch<HrLeave>(`/hr/leaves/${id}`, data);
  }
  deleteLeave(id: string): Observable<void> {
    return this.api.delete(`/hr/leaves/${id}`);
  }
}
