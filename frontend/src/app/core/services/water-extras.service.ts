import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  UnreadCount,
  WaterAnalyticsResponse,
  WaterAuditEntry,
  WaterNotification,
} from '../models/water-phase6.model';

@Injectable({ providedIn: 'root' })
export class WaterExtrasService {
  private readonly api = inject(ApiService);

  // Notifications
  listNotifications(unreadOnly = false, limit = 50): Observable<WaterNotification[]> {
    const params: Record<string, string | number | boolean> = { limit };
    if (unreadOnly) params['unread_only'] = true;
    return this.api.get<WaterNotification[]>('/water/notifications', params);
  }
  unreadCount(): Observable<UnreadCount> {
    return this.api.get<UnreadCount>('/water/notifications/unread-count');
  }
  markRead(ids: string[]): Observable<{ updated: number }> {
    return this.api.post<{ updated: number }>('/water/notifications/mark-read', { ids });
  }
  markAllRead(): Observable<{ updated: number }> {
    return this.api.post<{ updated: number }>('/water/notifications/mark-all-read', {});
  }

  // Audit
  listAudit(params?: {
    actor_id?: string;
    action?: string;
    resource_type?: string;
    limit?: number;
  }): Observable<WaterAuditEntry[]> {
    const clean: Record<string, string | number> = {};
    if (params?.actor_id) clean['actor_id'] = params.actor_id;
    if (params?.action) clean['action'] = params.action;
    if (params?.resource_type) clean['resource_type'] = params.resource_type;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    return this.api.get<WaterAuditEntry[]>('/water/audit', clean);
  }

  // Analytics
  analyticsOverview(): Observable<WaterAnalyticsResponse> {
    return this.api.get<WaterAnalyticsResponse>('/water/analytics/overview');
  }
}
