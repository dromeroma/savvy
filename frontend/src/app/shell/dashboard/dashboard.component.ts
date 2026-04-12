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
      name: 'SavvyChain',
      description: 'Gestión de cadena de suministro: proveedores, compras, inventarios, logística y trazabilidad',
      color: '#6366F1',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
    },
    {
      name: 'SavvyPay',
      description: 'Pasarela de pagos y facturación electrónica: cobros online, recurrentes, wallets y conciliación',
      color: '#10B981',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/><path d="M7 15h2m4 0h4"/></svg>`,
    },
    {
      name: 'SavvyWater',
      description: 'Gestión de acueductos y servicios de agua: medidores, consumo, facturación, redes y cortes',
      color: '#06B6D4',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>`,
    },
    {
      name: 'SavvyFlow',
      description: 'Automatización de procesos y workflows: flujos de aprobación, tareas, reglas y notificaciones',
      color: '#8B5CF6',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    },
    {
      name: 'SavvyMarket',
      description: 'Marketplace y e-commerce: catálogo, carrito, pedidos, envíos y pagos integrados',
      color: '#F97316',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`,
    },
    {
      name: 'SavvyAnalytics',
      description: 'Business intelligence y dashboards avanzados: reportes, KPIs, visualización y exportación',
      color: '#3B82F6',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
    },
    {
      name: 'SavvyLegal',
      description: 'Gestión jurídica: contratos, casos, vencimientos, documentos legales y seguimiento procesal',
      color: '#64748B',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`,
    },
    {
      name: 'SavvyHR',
      description: 'Gestión de talento humano: empleados, nómina, vacaciones, evaluaciones y capacitación',
      color: '#EC4899',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>`,
    },
    {
      name: 'SavvySecure',
      description: 'Seguridad física y vigilancia: cámaras, rondas, control de acceso, incidentes y reportes',
      color: '#EF4444',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
    },
    {
      name: 'SavvyAI',
      description: 'Inteligencia artificial: agentes IA, asistentes, automatización inteligente, análisis predictivo',
      color: '#A855F7',
      icon: `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/><path d="M9 17v-2"/><path d="M15 17v-2"/></svg>`,
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
