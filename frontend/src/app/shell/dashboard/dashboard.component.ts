import { Component, inject, signal, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AppsService } from '../../core/services/apps.service';
import { MyApp } from '../../core/models/app.model';

@Component({
  selector: 'app-dashboard',
  imports: [],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly appsService = inject(AppsService);
  private readonly router = inject(Router);

  myApps = signal<MyApp[]>([]);
  loading = signal(true);
  error = signal('');

  ngOnInit(): void {
    this.appsService.getMyApps().subscribe({
      next: (apps) => {
        this.myApps.set(apps);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Error al cargar las aplicaciones.');
        this.loading.set(false);
      },
    });
  }

  openApp(app: MyApp): void {
    if (app.status === 'active') {
      this.router.navigate([`/${app.app.code}`]);
    }
  }

  activateApp(app: MyApp): void {
    this.appsService.activateApp(app.app.code).subscribe({
      next: () => {
        this.ngOnInit();
      },
    });
  }
}
