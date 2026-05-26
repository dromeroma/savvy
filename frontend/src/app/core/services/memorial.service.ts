import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  MemorialDashboardKpis,
  MemorialFamilyMember,
  MemorialFamilyMemberCreate,
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
}
