import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  BatchGenerateDuesResult,
  ContractStatus,
  CoverageLookupResult,
  ExequialBeneficiary,
  ExequialBeneficiaryCreate,
  ExequialContract,
  ExequialContractCreate,
  ExequialContractListItem,
  ExequialPlan,
  ExequialPlanCreate,
  ExequialPlanListItem,
  GenerateServiceInvoiceRequest,
  MemorialAgingReport,
  MemorialCarteraRecalcResult,
  MemorialDashboardKpis,
  MemorialFamilyMember,
  MemorialFamilyMemberCreate,
  MemorialInvoice,
  MemorialInvoiceListItem,
  MemorialOverdueDebtor,
  MemorialPayment,
  MemorialPaymentCreate,
  MemorialPaymentListItem,
  MemorialService,
  MemorialServiceCreate,
  MemorialServiceEvent,
  MemorialServiceListItem,
  MemorialServiceStatus,
  MemorialVehicle,
  MemorialVehicleCreate,
  MemorialDriver,
  MemorialDriverCreate,
  MemorialRoom,
  MemorialRoomCreate,
  MemorialOven,
  MemorialOvenCreate,
  MemorialLocation,
  MemorialLocationCreate,
  MemorialTransfer,
  MemorialTransferCreate,
  MemorialTransferListItem,
  TransferStatus,
  InventoryItem,
  InventoryItemCreate,
  InventoryItemListItem,
  InventoryMovement,
  InventoryMovementCreate,
  InventoryMovementListItem,
  HrPosition,
  HrPositionCreate,
  HrEmployee,
  HrEmployeeCreate,
  HrEmployeeListItem,
  HrAttendance,
  HrAttendanceCreate,
  HrAttendanceListItem,
  Lead,
  LeadCreate,
  LeadUpdate,
  LeadListItem,
  LeadCommunication,
  LeadCommunicationCreate,
} from '../models/memorial.model';

@Injectable({ providedIn: 'root' })
export class MemorialApiService {
  private readonly api = inject(ApiService);

  // ---- Dashboard ----
  getKpis(): Observable<MemorialDashboardKpis> {
    return this.api.get<MemorialDashboardKpis>('/memorial/dashboard/kpis');
  }

  // ---- Services ----
  listServices(params?: {
    search?: string; status?: string; service_type?: string;
    limit?: number; offset?: number;
  }): Observable<MemorialServiceListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.search) clean['search'] = params.search;
    if (params?.status) clean['status'] = params.status;
    if (params?.service_type) clean['service_type'] = params.service_type;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<MemorialServiceListItem[]>('/memorial/services', clean);
  }

  getService(id: string): Observable<MemorialService> {
    return this.api.get<MemorialService>(`/memorial/services/${id}`);
  }

  createService(data: MemorialServiceCreate): Observable<MemorialService> {
    return this.api.post<MemorialService>('/memorial/services', data);
  }

  updateService(id: string, data: Partial<MemorialServiceCreate>): Observable<MemorialService> {
    return this.api.patch<MemorialService>(`/memorial/services/${id}`, data);
  }

  transitionStatus(id: string, newStatus: MemorialServiceStatus, note?: string): Observable<MemorialService> {
    return this.api.post<MemorialService>(
      `/memorial/services/${id}/transition`,
      { new_status: newStatus, note: note ?? null },
    );
  }

  addNote(id: string, body: string): Observable<MemorialServiceEvent> {
    return this.api.post<MemorialServiceEvent>(
      `/memorial/services/${id}/notes`, { body },
    );
  }

  listEvents(id: string): Observable<MemorialServiceEvent[]> {
    return this.api.get<MemorialServiceEvent[]>(`/memorial/services/${id}/events`);
  }

  // ---- Family ----
  addFamilyMember(serviceId: string, data: MemorialFamilyMemberCreate): Observable<MemorialFamilyMember> {
    return this.api.post<MemorialFamilyMember>(`/memorial/services/${serviceId}/family`, data);
  }
  updateFamilyMember(serviceId: string, memberId: string, data: Partial<MemorialFamilyMemberCreate>): Observable<MemorialFamilyMember> {
    return this.api.patch<MemorialFamilyMember>(`/memorial/services/${serviceId}/family/${memberId}`, data);
  }
  removeFamilyMember(serviceId: string, memberId: string): Observable<void> {
    return this.api.delete(`/memorial/services/${serviceId}/family/${memberId}`);
  }

  // ---- Link contract to service ----
  linkContractToService(serviceId: string, contractId: string | null): Observable<MemorialService> {
    return this.api.post<MemorialService>(
      `/memorial/services/${serviceId}/link-contract`,
      { contract_id: contractId },
    );
  }

  // ---- Plans ----
  listPlans(params?: { active_only?: boolean; search?: string }): Observable<ExequialPlanListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.active_only) clean['active_only'] = true;
    if (params?.search) clean['search'] = params.search;
    return this.api.get<ExequialPlanListItem[]>('/memorial/plans', clean);
  }
  getPlan(id: string): Observable<ExequialPlan> {
    return this.api.get<ExequialPlan>(`/memorial/plans/${id}`);
  }
  createPlan(data: ExequialPlanCreate): Observable<ExequialPlan> {
    return this.api.post<ExequialPlan>('/memorial/plans', data);
  }
  updatePlan(id: string, data: Partial<ExequialPlanCreate>): Observable<ExequialPlan> {
    return this.api.patch<ExequialPlan>(`/memorial/plans/${id}`, data);
  }
  deletePlan(id: string): Observable<void> {
    return this.api.delete(`/memorial/plans/${id}`);
  }

  // ---- Contracts ----
  listContracts(params?: {
    search?: string; status?: string; plan_id?: string;
    limit?: number; offset?: number;
  }): Observable<ExequialContractListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.search) clean['search'] = params.search;
    if (params?.status) clean['status'] = params.status;
    if (params?.plan_id) clean['plan_id'] = params.plan_id;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<ExequialContractListItem[]>('/memorial/contracts', clean);
  }
  getContract(id: string): Observable<ExequialContract> {
    return this.api.get<ExequialContract>(`/memorial/contracts/${id}`);
  }
  createContract(data: ExequialContractCreate): Observable<ExequialContract> {
    return this.api.post<ExequialContract>('/memorial/contracts', data);
  }
  updateContract(id: string, data: Partial<ExequialContractCreate>): Observable<ExequialContract> {
    return this.api.patch<ExequialContract>(`/memorial/contracts/${id}`, data);
  }
  transitionContract(id: string, newStatus: ContractStatus, reason?: string): Observable<ExequialContract> {
    return this.api.post<ExequialContract>(
      `/memorial/contracts/${id}/transition`,
      { new_status: newStatus, reason: reason ?? null },
    );
  }
  addBeneficiary(contractId: string, data: ExequialBeneficiaryCreate): Observable<ExequialBeneficiary> {
    return this.api.post<ExequialBeneficiary>(`/memorial/contracts/${contractId}/beneficiaries`, data);
  }
  updateBeneficiary(contractId: string, beneficiaryId: string, data: Partial<ExequialBeneficiaryCreate>): Observable<ExequialBeneficiary> {
    return this.api.patch<ExequialBeneficiary>(`/memorial/contracts/${contractId}/beneficiaries/${beneficiaryId}`, data);
  }
  removeBeneficiary(contractId: string, beneficiaryId: string): Observable<void> {
    return this.api.delete(`/memorial/contracts/${contractId}/beneficiaries/${beneficiaryId}`);
  }

  // ---- Coverage lookup ----
  coverageLookup(documentNumber: string): Observable<CoverageLookupResult[]> {
    return this.api.get<CoverageLookupResult[]>(
      '/memorial/contracts/coverage-lookup',
      { document_number: documentNumber },
    );
  }

  // ---- Invoices ----
  listInvoices(params?: {
    source_type?: string; status?: string;
    contract_id?: string; service_id?: string;
    unpaid_only?: boolean; limit?: number; offset?: number;
  }): Observable<MemorialInvoiceListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.source_type) clean['source_type'] = params.source_type;
    if (params?.status) clean['status'] = params.status;
    if (params?.contract_id) clean['contract_id'] = params.contract_id;
    if (params?.service_id) clean['service_id'] = params.service_id;
    if (params?.unpaid_only) clean['unpaid_only'] = true;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<MemorialInvoiceListItem[]>('/memorial/invoices', clean);
  }
  getInvoice(id: string): Observable<MemorialInvoice> {
    return this.api.get<MemorialInvoice>(`/memorial/invoices/${id}`);
  }
  batchGenerateDues(asOfDate?: string): Observable<BatchGenerateDuesResult> {
    return this.api.post<BatchGenerateDuesResult>(
      '/memorial/invoices/batch-generate-dues',
      { as_of_date: asOfDate ?? null },
    );
  }
  generateInvoiceForService(data: GenerateServiceInvoiceRequest): Observable<MemorialInvoice> {
    return this.api.post<MemorialInvoice>(
      '/memorial/invoices/generate-for-service', data,
    );
  }
  annulInvoice(id: string): Observable<MemorialInvoice> {
    return this.api.post<MemorialInvoice>(`/memorial/invoices/${id}/annul`, {});
  }
  downloadInvoicePdf(id: string): Observable<{ blob: Blob; filename: string | null }> {
    return this.api.getBlob(`/memorial/invoices/${id}/pdf`);
  }

  // ---- Payments ----
  listPayments(params?: {
    contract_id?: string; service_id?: string;
    date_from?: string; date_to?: string; method?: string;
    limit?: number; offset?: number;
  }): Observable<MemorialPaymentListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.contract_id) clean['contract_id'] = params.contract_id;
    if (params?.service_id) clean['service_id'] = params.service_id;
    if (params?.date_from) clean['date_from'] = params.date_from;
    if (params?.date_to) clean['date_to'] = params.date_to;
    if (params?.method) clean['method'] = params.method;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<MemorialPaymentListItem[]>('/memorial/payments', clean);
  }
  getPayment(id: string): Observable<MemorialPayment> {
    return this.api.get<MemorialPayment>(`/memorial/payments/${id}`);
  }
  registerPayment(data: MemorialPaymentCreate): Observable<MemorialPayment> {
    return this.api.post<MemorialPayment>('/memorial/payments', data);
  }

  // ---- Cartera ----
  recalcCartera(): Observable<MemorialCarteraRecalcResult> {
    return this.api.post<MemorialCarteraRecalcResult>('/memorial/cartera/recalculate', {});
  }
  cartera_aging(): Observable<MemorialAgingReport> {
    return this.api.get<MemorialAgingReport>('/memorial/cartera/aging');
  }
  cartera_overdue(limit = 100): Observable<MemorialOverdueDebtor[]> {
    return this.api.get<MemorialOverdueDebtor[]>('/memorial/cartera/overdue', { limit });
  }

  // ---- Logistics: Vehicles ----
  listVehicles(search?: string): Observable<MemorialVehicle[]> {
    return this.api.get<MemorialVehicle[]>('/memorial/logistics/vehicles', search ? { search } : undefined);
  }
  createVehicle(data: MemorialVehicleCreate): Observable<MemorialVehicle> {
    return this.api.post<MemorialVehicle>('/memorial/logistics/vehicles', data);
  }
  updateVehicle(id: string, data: Partial<MemorialVehicleCreate>): Observable<MemorialVehicle> {
    return this.api.patch<MemorialVehicle>(`/memorial/logistics/vehicles/${id}`, data);
  }
  deleteVehicle(id: string): Observable<void> {
    return this.api.delete(`/memorial/logistics/vehicles/${id}`);
  }

  // ---- Logistics: Drivers ----
  listDrivers(search?: string): Observable<MemorialDriver[]> {
    return this.api.get<MemorialDriver[]>('/memorial/logistics/drivers', search ? { search } : undefined);
  }
  createDriver(data: MemorialDriverCreate): Observable<MemorialDriver> {
    return this.api.post<MemorialDriver>('/memorial/logistics/drivers', data);
  }
  updateDriver(id: string, data: Partial<MemorialDriverCreate>): Observable<MemorialDriver> {
    return this.api.patch<MemorialDriver>(`/memorial/logistics/drivers/${id}`, data);
  }
  deleteDriver(id: string): Observable<void> {
    return this.api.delete(`/memorial/logistics/drivers/${id}`);
  }

  // ---- Logistics: Rooms ----
  listRooms(): Observable<MemorialRoom[]> {
    return this.api.get<MemorialRoom[]>('/memorial/logistics/rooms');
  }
  createRoom(data: MemorialRoomCreate): Observable<MemorialRoom> {
    return this.api.post<MemorialRoom>('/memorial/logistics/rooms', data);
  }
  updateRoom(id: string, data: Partial<MemorialRoomCreate>): Observable<MemorialRoom> {
    return this.api.patch<MemorialRoom>(`/memorial/logistics/rooms/${id}`, data);
  }
  deleteRoom(id: string): Observable<void> {
    return this.api.delete(`/memorial/logistics/rooms/${id}`);
  }

  // ---- Logistics: Ovens ----
  listOvens(): Observable<MemorialOven[]> {
    return this.api.get<MemorialOven[]>('/memorial/logistics/ovens');
  }
  createOven(data: MemorialOvenCreate): Observable<MemorialOven> {
    return this.api.post<MemorialOven>('/memorial/logistics/ovens', data);
  }
  updateOven(id: string, data: Partial<MemorialOvenCreate>): Observable<MemorialOven> {
    return this.api.patch<MemorialOven>(`/memorial/logistics/ovens/${id}`, data);
  }
  deleteOven(id: string): Observable<void> {
    return this.api.delete(`/memorial/logistics/ovens/${id}`);
  }

  // ---- Logistics: Locations ----
  listLocations(kind?: string, search?: string): Observable<MemorialLocation[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (kind) clean['kind'] = kind;
    if (search) clean['search'] = search;
    return this.api.get<MemorialLocation[]>('/memorial/logistics/locations', clean);
  }
  createLocation(data: MemorialLocationCreate): Observable<MemorialLocation> {
    return this.api.post<MemorialLocation>('/memorial/logistics/locations', data);
  }
  updateLocation(id: string, data: Partial<MemorialLocationCreate>): Observable<MemorialLocation> {
    return this.api.patch<MemorialLocation>(`/memorial/logistics/locations/${id}`, data);
  }
  deleteLocation(id: string): Observable<void> {
    return this.api.delete(`/memorial/logistics/locations/${id}`);
  }

  // ---- Transfers ----
  listTransfers(params?: {
    service_id?: string; status?: string;
    date_from?: string; date_to?: string;
    limit?: number; offset?: number;
  }): Observable<MemorialTransferListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.service_id) clean['service_id'] = params.service_id;
    if (params?.status) clean['status'] = params.status;
    if (params?.date_from) clean['date_from'] = params.date_from;
    if (params?.date_to) clean['date_to'] = params.date_to;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<MemorialTransferListItem[]>('/memorial/transfers', clean);
  }
  getTransfer(id: string): Observable<MemorialTransfer> {
    return this.api.get<MemorialTransfer>(`/memorial/transfers/${id}`);
  }
  createTransfer(data: MemorialTransferCreate): Observable<MemorialTransfer> {
    return this.api.post<MemorialTransfer>('/memorial/transfers', data);
  }
  updateTransfer(id: string, data: Partial<MemorialTransferCreate>): Observable<MemorialTransfer> {
    return this.api.patch<MemorialTransfer>(`/memorial/transfers/${id}`, data);
  }
  transitionTransfer(id: string, newStatus: TransferStatus): Observable<MemorialTransfer> {
    return this.api.post<MemorialTransfer>(`/memorial/transfers/${id}/transition`, { new_status: newStatus });
  }
  deleteTransfer(id: string): Observable<void> {
    return this.api.delete(`/memorial/transfers/${id}`);
  }

  // ---- Inventory: Items ----
  listInventoryItems(params?: {
    category?: string; active_only?: boolean; low_stock_only?: boolean; search?: string;
  }): Observable<InventoryItemListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.category) clean['category'] = params.category;
    if (params?.active_only) clean['active_only'] = true;
    if (params?.low_stock_only) clean['low_stock_only'] = true;
    if (params?.search) clean['search'] = params.search;
    return this.api.get<InventoryItemListItem[]>('/memorial/inventory/items', clean);
  }
  getInventoryItem(id: string): Observable<InventoryItem> {
    return this.api.get<InventoryItem>(`/memorial/inventory/items/${id}`);
  }
  createInventoryItem(data: InventoryItemCreate): Observable<InventoryItem> {
    return this.api.post<InventoryItem>('/memorial/inventory/items', data);
  }
  updateInventoryItem(id: string, data: Partial<InventoryItemCreate>): Observable<InventoryItem> {
    return this.api.patch<InventoryItem>(`/memorial/inventory/items/${id}`, data);
  }
  deleteInventoryItem(id: string): Observable<void> {
    return this.api.delete(`/memorial/inventory/items/${id}`);
  }

  // ---- Inventory: Movements ----
  listInventoryMovements(params?: {
    item_id?: string; movement_type?: string;
    date_from?: string; date_to?: string;
    limit?: number; offset?: number;
  }): Observable<InventoryMovementListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.item_id) clean['item_id'] = params.item_id;
    if (params?.movement_type) clean['movement_type'] = params.movement_type;
    if (params?.date_from) clean['date_from'] = params.date_from;
    if (params?.date_to) clean['date_to'] = params.date_to;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<InventoryMovementListItem[]>('/memorial/inventory/movements', clean);
  }
  recordInventoryMovement(data: InventoryMovementCreate): Observable<InventoryMovement> {
    return this.api.post<InventoryMovement>('/memorial/inventory/movements', data);
  }

  // ---- HR: Positions ----
  listPositions(active_only = false): Observable<HrPosition[]> {
    return this.api.get<HrPosition[]>('/memorial/hr/positions', active_only ? { active_only: true } : undefined);
  }
  createPosition(data: HrPositionCreate): Observable<HrPosition> {
    return this.api.post<HrPosition>('/memorial/hr/positions', data);
  }
  updatePosition(id: string, data: Partial<HrPositionCreate>): Observable<HrPosition> {
    return this.api.patch<HrPosition>(`/memorial/hr/positions/${id}`, data);
  }
  deletePosition(id: string): Observable<void> {
    return this.api.delete(`/memorial/hr/positions/${id}`);
  }

  // ---- HR: Employees ----
  listEmployees(params?: { status?: string; position_id?: string; search?: string }): Observable<HrEmployeeListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.status) clean['status'] = params.status;
    if (params?.position_id) clean['position_id'] = params.position_id;
    if (params?.search) clean['search'] = params.search;
    return this.api.get<HrEmployeeListItem[]>('/memorial/hr/employees', clean);
  }
  getEmployee(id: string): Observable<HrEmployee> {
    return this.api.get<HrEmployee>(`/memorial/hr/employees/${id}`);
  }
  createEmployee(data: HrEmployeeCreate): Observable<HrEmployee> {
    return this.api.post<HrEmployee>('/memorial/hr/employees', data);
  }
  updateEmployee(id: string, data: Partial<HrEmployeeCreate>): Observable<HrEmployee> {
    return this.api.patch<HrEmployee>(`/memorial/hr/employees/${id}`, data);
  }
  deleteEmployee(id: string): Observable<void> {
    return this.api.delete(`/memorial/hr/employees/${id}`);
  }

  // ---- HR: Attendance ----
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
    return this.api.get<HrAttendanceListItem[]>('/memorial/hr/attendance', clean);
  }
  upsertAttendance(data: HrAttendanceCreate): Observable<HrAttendance> {
    return this.api.post<HrAttendance>('/memorial/hr/attendance', data);
  }
  updateAttendance(id: string, data: Partial<HrAttendanceCreate>): Observable<HrAttendance> {
    return this.api.patch<HrAttendance>(`/memorial/hr/attendance/${id}`, data);
  }
  deleteAttendance(id: string): Observable<void> {
    return this.api.delete(`/memorial/hr/attendance/${id}`);
  }

  // ---- CRM: Leads ----
  listLeads(params?: {
    status?: string; source?: string; assigned_to?: string;
    search?: string; limit?: number; offset?: number;
  }): Observable<LeadListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.status) clean['status'] = params.status;
    if (params?.source) clean['source'] = params.source;
    if (params?.assigned_to) clean['assigned_to'] = params.assigned_to;
    if (params?.search) clean['search'] = params.search;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<LeadListItem[]>('/memorial/crm/leads', clean);
  }
  getLead(id: string): Observable<Lead> {
    return this.api.get<Lead>(`/memorial/crm/leads/${id}`);
  }
  createLead(data: LeadCreate): Observable<Lead> {
    return this.api.post<Lead>('/memorial/crm/leads', data);
  }
  updateLead(id: string, data: LeadUpdate): Observable<Lead> {
    return this.api.patch<Lead>(`/memorial/crm/leads/${id}`, data);
  }
  deleteLead(id: string): Observable<void> {
    return this.api.delete(`/memorial/crm/leads/${id}`);
  }
  convertLeadToContract(id: string, contractId: string): Observable<Lead> {
    return this.api.post<Lead>(`/memorial/crm/leads/${id}/convert-contract`, { contract_id: contractId });
  }
  convertLeadToService(id: string, serviceId: string): Observable<Lead> {
    return this.api.post<Lead>(`/memorial/crm/leads/${id}/convert-service`, { service_id: serviceId });
  }
  markLeadLost(id: string, reason: string): Observable<Lead> {
    return this.api.post<Lead>(`/memorial/crm/leads/${id}/mark-lost`, { lost_reason: reason });
  }

  // ---- CRM: Communications ----
  listLeadCommunications(leadId: string): Observable<LeadCommunication[]> {
    return this.api.get<LeadCommunication[]>(`/memorial/crm/leads/${leadId}/communications`);
  }
  createLeadCommunication(leadId: string, data: LeadCommunicationCreate): Observable<LeadCommunication> {
    return this.api.post<LeadCommunication>(`/memorial/crm/leads/${leadId}/communications`, data);
  }
  deleteLeadCommunication(commId: string): Observable<void> {
    return this.api.delete(`/memorial/crm/communications/${commId}`);
  }
}
