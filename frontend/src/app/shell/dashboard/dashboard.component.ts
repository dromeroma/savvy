import { Component, inject, signal, computed, OnInit } from '@angular/core';
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

  // Computed: separate internal from external
  myInternalApps = computed(() => this.myApps().filter(a => !a.app.is_external));
  myExternalApps = computed(() => this.myApps().filter(a => a.app.is_external));
  catalogInternal = computed(() => this.catalog().filter(a => !a.is_external));
  catalogExternal = computed(() => this.catalog().filter(a => a.is_external));

  ngOnInit(): void {
    this.loadData();
  }

  private loadData(): void {
    this.loading.set(true);
    this.error.set('');

    this.appsService.getMyApps().subscribe({
      next: (apps) => {
        this.myApps.set(apps);
        this.loadCatalog(apps);
      },
      error: () => {
        this.loadCatalog([]);
      },
    });
  }

  private loadCatalog(myApps: MyApp[]): void {
    this.appsService.getCatalog().subscribe({
      next: (allApps) => {
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
    if (app.app.is_external && app.app.external_url) {
      window.open(app.app.external_url, '_blank');
    } else {
      this.router.navigate([`/${app.app.code}`]);
    }
  }

  openExternalApp(app: SavvyApp): void {
    if (app.external_url) {
      window.open(app.external_url, '_blank');
    }
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
