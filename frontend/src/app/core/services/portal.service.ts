import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  AdminPqrsListItem,
  InvitePortalRequest,
  InvitePortalResponse,
  PortalConsumptionItem,
  PortalDashboard,
  PortalInvoiceItem,
  PortalMe,
  PortalPaymentItem,
  PortalPqrsDetail,
  PortalPqrsListItem,
  PqrsCreate,
} from '../models/portal.model';

@Injectable({ providedIn: 'root' })
export class PortalService {
  private readonly api = inject(ApiService);

  // ---- Subscriber portal (own data) ----
  me(): Observable<PortalMe> {
    return this.api.get<PortalMe>('/water/portal/me');
  }
  dashboard(): Observable<PortalDashboard> {
    return this.api.get<PortalDashboard>('/water/portal/dashboard');
  }
  invoices(): Observable<PortalInvoiceItem[]> {
    return this.api.get<PortalInvoiceItem[]>('/water/portal/invoices');
  }
  payments(): Observable<PortalPaymentItem[]> {
    return this.api.get<PortalPaymentItem[]>('/water/portal/payments');
  }
  consumption(): Observable<PortalConsumptionItem[]> {
    return this.api.get<PortalConsumptionItem[]>('/water/portal/consumption');
  }

  // ---- PQRS (customer) ----
  myPqrs(): Observable<PortalPqrsListItem[]> {
    return this.api.get<PortalPqrsListItem[]>('/water/portal/pqrs');
  }
  getMyPqrs(id: string): Observable<PortalPqrsDetail> {
    return this.api.get<PortalPqrsDetail>(`/water/portal/pqrs/${id}`);
  }
  createMyPqrs(data: PqrsCreate): Observable<PortalPqrsDetail> {
    return this.api.post<PortalPqrsDetail>('/water/portal/pqrs', data);
  }

  // ---- Admin: PQRS ----
  adminListPqrs(params?: { status?: string; type?: string; subscriber_id?: string }): Observable<AdminPqrsListItem[]> {
    const clean: Record<string, string> = {};
    if (params?.status) clean['status'] = params.status;
    if (params?.type) clean['type'] = params.type;
    if (params?.subscriber_id) clean['subscriber_id'] = params.subscriber_id;
    return this.api.get<AdminPqrsListItem[]>('/water/pqrs', clean);
  }
  adminGetPqrs(id: string): Observable<PortalPqrsDetail> {
    return this.api.get<PortalPqrsDetail>(`/water/pqrs/${id}`);
  }
  adminRespondPqrs(id: string, response: string, status: string = 'resolved'): Observable<PortalPqrsDetail> {
    return this.api.post<PortalPqrsDetail>(`/water/pqrs/${id}/respond`, { response, status });
  }

  // ---- Admin: invite portal ----
  invitePortal(subscriberId: string, data: InvitePortalRequest): Observable<InvitePortalResponse> {
    return this.api.post<InvitePortalResponse>(
      `/water/subscribers/${subscriberId}/invite-portal`, data,
    );
  }
}
