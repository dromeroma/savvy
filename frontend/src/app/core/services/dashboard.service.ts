import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface DashboardOrganization {
  id: string;
  name: string;
  slug: string;
  type: string;
  business_type: string | null;
  business_type_label: string | null;
  denomination_name: string | null;
  zone_label: string | null;
  member_count: number;
  created_at: string;
}

export interface DashboardSubscription {
  plan_code: string;
  plan_name: string;
  status: string;
  billing_cycle: string;
  started_at: string;
  trial_ends_at: string | null;
}

export interface DashboardApp {
  code: string;
  name: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  status: string;
  user_role: string | null;
}

export interface DashboardMetric {
  key: string;
  label: string;
  value: string;
  raw_value: number | null;
  icon: string | null;
  color: string | null;
  app_code: string | null;
}

export interface DashboardSummaryResponse {
  organization: DashboardOrganization;
  subscription: DashboardSubscription | null;
  active_apps: DashboardApp[];
  metrics: DashboardMetric[];
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly api = inject(ApiService);

  getSummary(): Observable<DashboardSummaryResponse> {
    return this.api.get<DashboardSummaryResponse>('/dashboard/summary');
  }
}
