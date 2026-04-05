import { Component, inject, signal, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AppsService } from '../../core/services/apps.service';
import { MyApp, SavvyApp } from '../../core/models/app.model';

@Component({
  selector: 'app-dashboard',
  imports: [],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly appsService = inject(AppsService);
  private readonly router = inject(Router);

  myApps = signal<MyApp[]>([]);
  catalog = signal<SavvyApp[]>([]);
  loading = signal(true);
  error = signal('');

  ngOnInit(): void {
    this.loadData();
  }

  private loadData(): void {
    this.loading.set(true);
    this.error.set('');

    // Load my apps
    this.appsService.getMyApps().subscribe({
      next: (apps) => {
        this.myApps.set(apps);
        this.loadCatalog(apps);
      },
      error: () => {
        // If /apps/me fails (no apps), load catalog anyway
        this.loadCatalog([]);
      },
    });
  }

  private loadCatalog(myApps: MyApp[]): void {
    this.appsService.getCatalog().subscribe({
      next: (allApps) => {
        // Filter out apps the user already has
        const myCodes = new Set(myApps.map(a => a.app.code));
        const available = allApps.filter(a => !myCodes.has(a.code));
        this.catalog.set(available);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      },
    });
  }

  openApp(app: MyApp): void {
    this.router.navigate([`/${app.app.code}`]);
  }

  activateApp(appCode: string): void {
    this.appsService.activateApp(appCode).subscribe({
      next: () => {
        this.loadData();
      },
      error: (err) => {
        this.error.set(err.error?.detail ?? 'Error al activar la aplicación.');
      },
    });
  }
}
