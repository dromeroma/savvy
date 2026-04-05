import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { MyApp, SavvyApp } from '../models/app.model';

@Injectable({ providedIn: 'root' })
export class AppsService {
  private readonly api = inject(ApiService);

  getMyApps(): Observable<MyApp[]> {
    return this.api.get<MyApp[]>('/apps/me');
  }

  getCatalog(): Observable<SavvyApp[]> {
    return this.api.get<SavvyApp[]>('/apps/catalog');
  }

  activateApp(appCode: string): Observable<unknown> {
    return this.api.post(`/apps/${appCode}/activate`, {});
  }
}
