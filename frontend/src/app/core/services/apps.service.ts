import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import { MyApp, SavvyApp } from '../models/app.model';

@Injectable({ providedIn: 'root' })
export class AppsService {
  private readonly api = inject(ApiService);

  private readonly myApps$ = new BehaviorSubject<MyApp[]>([]);

  /** Observable stream of the user's active apps. Sidebar subscribes to this. */
  readonly apps$ = this.myApps$.asObservable();

  getMyApps(): Observable<MyApp[]> {
    return this.api.get<MyApp[]>('/apps/me').pipe(
      tap((apps) => this.myApps$.next(apps)),
    );
  }

  getCatalog(): Observable<SavvyApp[]> {
    return this.api.get<SavvyApp[]>('/apps/catalog');
  }

  activateApp(appCode: string): Observable<unknown> {
    return this.api.post('/apps/activate', { app_code: appCode });
  }

  /** Force refresh the apps list and notify all subscribers (sidebar, dashboard, etc.) */
  refreshApps(): void {
    this.api.get<MyApp[]>('/apps/me').subscribe({
      next: (apps) => this.myApps$.next(apps),
    });
  }
}
