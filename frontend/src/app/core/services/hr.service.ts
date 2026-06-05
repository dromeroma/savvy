import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
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
  HrPosition,
  HrPositionCreate,
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
}
