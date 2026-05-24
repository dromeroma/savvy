import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { BusinessType, Denomination, Zone } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class OnboardingService {
  private readonly api = inject(ApiService);

  listBusinessTypes(): Observable<BusinessType[]> {
    return this.api.get<BusinessType[]>('/onboarding/business-types');
  }

  listDenominations(businessType?: string): Observable<Denomination[]> {
    const params = businessType ? { business_type: businessType } : undefined;
    return this.api.get<Denomination[]>('/onboarding/denominations', params);
  }

  listZones(denominationId: string): Observable<Zone[]> {
    return this.api.get<Zone[]>('/onboarding/zones', { denomination_id: denominationId });
  }
}
