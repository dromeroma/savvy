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
}
