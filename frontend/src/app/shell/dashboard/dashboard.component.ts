import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AppsService } from '../../core/services/apps.service';
import { MyApp, SavvyApp } from '../../core/models/app.model';
import { NotificationService } from '../../shared/services/notification.service';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly appsService = inject(AppsService);
  private readonly router = inject(Router);
  private readonly notify = inject(NotificationService);

  myApps = signal<MyApp[]>([]);
  catalog = signal<SavvyApp[]>([]);
  loading = signal(true);
  error = signal('');

  comingSoonApps = [
    {
      name: 'SavvyHealth',
      description: 'Gestión de clínicas y consultorios: pacientes, citas, historia clínica y facturación',
      color: '#EF4444',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
    },
    {
      name: 'SavvyCondo',
      description: 'Administración de propiedades horizontales: copropietarios, cuotas, áreas comunes y asambleas',
      color: '#F59E0B',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>`,
    },
  ];

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
        this.notify.show({ type: 'success', title: 'App activada', message: 'La aplicación se activó correctamente' });
        this.loadData(); // Reloads dashboard + triggers sidebar update via apps$ stream
      },
      error: (err) => {
        const msg = err.error?.detail ?? 'Error al activar la aplicación.';
        this.error.set(msg);
        this.notify.show({ type: 'error', title: 'Error', message: msg });
      },
    });
  }
}
