import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  WaterDashboardKpis,
  WaterMeter,
  WaterMeterCreate,
  WaterMeterListItem,
  WaterSubscriber,
  WaterSubscriberCreate,
  WaterSubscriberListItem,
} from '../models/water.model';

@Injectable({ providedIn: 'root' })
export class WaterService {
  private readonly api = inject(ApiService);

  // ---- Dashboard ----
  getKpis(): Observable<WaterDashboardKpis> {
    return this.api.get<WaterDashboardKpis>('/water/dashboard/kpis');
  }

  // ---- Subscribers ----
  listSubscribers(params?: {
    search?: string;
    status?: string;
    subscriber_type?: string;
    limit?: number;
    offset?: number;
  }): Observable<WaterSubscriberListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.search) clean['search'] = params.search;
    if (params?.status) clean['status'] = params.status;
    if (params?.subscriber_type) clean['subscriber_type'] = params.subscriber_type;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterSubscriberListItem[]>('/water/subscribers', clean);
  }

  getSubscriber(id: string): Observable<WaterSubscriber> {
    return this.api.get<WaterSubscriber>(`/water/subscribers/${id}`);
  }

  createSubscriber(data: WaterSubscriberCreate): Observable<WaterSubscriber> {
    return this.api.post<WaterSubscriber>('/water/subscribers', data);
  }

  updateSubscriber(id: string, data: Partial<WaterSubscriberCreate>): Observable<WaterSubscriber> {
    return this.api.patch<WaterSubscriber>(`/water/subscribers/${id}`, data);
  }

  deleteSubscriber(id: string): Observable<void> {
    return this.api.delete(`/water/subscribers/${id}`);
  }

  // ---- Meters ----
  listMeters(params?: {
    search?: string;
    status?: string;
    subscriber_id?: string;
    unassigned_only?: boolean;
    limit?: number;
    offset?: number;
  }): Observable<WaterMeterListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.search) clean['search'] = params.search;
    if (params?.status) clean['status'] = params.status;
    if (params?.subscriber_id) clean['subscriber_id'] = params.subscriber_id;
    if (params?.unassigned_only) clean['unassigned_only'] = true;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterMeterListItem[]>('/water/meters', clean);
  }

  getMeter(id: string): Observable<WaterMeter> {
    return this.api.get<WaterMeter>(`/water/meters/${id}`);
  }

  createMeter(data: WaterMeterCreate): Observable<WaterMeter> {
    return this.api.post<WaterMeter>('/water/meters', data);
  }

  updateMeter(id: string, data: Partial<WaterMeterCreate>): Observable<WaterMeter> {
    return this.api.patch<WaterMeter>(`/water/meters/${id}`, data);
  }

  deleteMeter(id: string): Observable<void> {
    return this.api.delete(`/water/meters/${id}`);
  }
}
