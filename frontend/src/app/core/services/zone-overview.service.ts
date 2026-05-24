import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface ZoneLeadership {
  id: string;
  number: number;
  name: string | null;
  denomination_name: string;
  role: string;
}

export interface ChurchMetrics {
  active_congregants: number;
  visitors_last_30d: number;
  events_last_30d: number;
  new_congregants_this_month: number;
  income_this_month: string;  // Decimal arrives as string
}

export interface ZoneChurch {
  id: string;
  name: string;
  slug: string;
  is_mine: boolean;
  metrics: ChurchMetrics;
}

export interface ZoneOverviewResponse {
  available_zones: ZoneLeadership[];
  selected_zone: ZoneLeadership | null;
  churches: ZoneChurch[];
}

@Injectable({ providedIn: 'root' })
export class ZoneOverviewService {
  private readonly api = inject(ApiService);

  getOverview(zoneId?: string): Observable<ZoneOverviewResponse> {
    const params = zoneId ? { zone_id: zoneId } : undefined;
    return this.api.get<ZoneOverviewResponse>('/church/zone/overview', params);
  }
}
