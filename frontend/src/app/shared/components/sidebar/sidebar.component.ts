import { Component, inject, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Subscription } from 'rxjs';
import { SidebarService } from '../../services/sidebar.service';
import { AppsService } from '../../../core/services/apps.service';
import { MyApp } from '../../../core/models/app.model';
import { APP_VERSION } from '../../../version';

interface AppMenu {
  code: string;
  name: string;
  icon: string;
  open: boolean;
  items: { label: string; route: string }[];
}

// Define sub-menu items per app
const APP_MENUS: Record<string, { icon: string; items: { label: string; route: string }[] }> = {
  church: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><path d="M18 21V7L12 3L6 7V21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 21H21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M10 21V15H14V21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 3V1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/church/dashboard' },
      { label: 'Congregantes', route: '/church/congregants' },
      { label: 'Visitantes', route: '/church/visitors' },
      { label: 'Grupos', route: '/church/groups' },
      { label: 'Eventos', route: '/church/events' },
      { label: 'Asistencia', route: '/church/attendance' },
      { label: 'Finanzas', route: '/church/finance' },
      { label: 'Reportes', route: '/church/reports' },
    ],
  },
  accounting: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><path d="M4 2V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M4 4H13L11 6L13 8H4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 12H10L8 14L10 16H4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><rect x="14" y="12" width="6" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/><path d="M16 16H18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    items: [
      { label: 'Catálogo de Cuentas', route: '/accounting/chart' },
      { label: 'Asientos Contables', route: '/accounting/journal' },
      { label: 'Períodos Fiscales', route: '/accounting/periods' },
      { label: 'Estado de Resultados', route: '/accounting/income-statement' },
      { label: 'Balance General', route: '/accounting/balance-sheet' },
    ],
  },
  edu: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><path d="M12 3L1 9L5 11.18V17.18L12 21L19 17.18V11.18L21 10.09V17H23V9L12 3Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M7 12.83V16.83L12 19.5L17 16.83V12.83L12 15.5L7 12.83Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/edu/dashboard' },
      { label: 'Configuración', route: '/edu/config' },
      { label: 'Programas', route: '/edu/programs' },
      { label: 'Cursos', route: '/edu/courses' },
      { label: 'Estudiantes', route: '/edu/students' },
      { label: 'Docentes', route: '/edu/teachers' },
      { label: 'Secciones', route: '/edu/enrollment' },
      { label: 'Horarios', route: '/edu/scheduling' },
      { label: 'Asistencia', route: '/edu/attendance' },
      { label: 'Calificaciones', route: '/edu/grading' },
      { label: 'Finanzas', route: '/edu/finance' },
      { label: 'Documentos', route: '/edu/documents' },
    ],
  },
  health: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/health/dashboard' },
      { label: 'Pacientes', route: '/health/patients' },
      { label: 'Profesionales', route: '/health/providers' },
      { label: 'Citas', route: '/health/appointments' },
      { label: 'Historias', route: '/health/clinical' },
      { label: 'Servicios', route: '/health/services' },
    ],
  },
  parking: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M9 17V7h4a3 3 0 0 1 0 6H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/parking/dashboard' },
      { label: 'Infraestructura', route: '/parking/infrastructure' },
      { label: 'Vehículos', route: '/parking/vehicles' },
      { label: 'Sesiones', route: '/parking/sessions' },
      { label: 'Tarifas', route: '/parking/pricing' },
      { label: 'Servicios', route: '/parking/services' },
    ],
  },
  condo: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><rect x="4" y="2" width="16" height="20" rx="2" ry="2" stroke="currentColor" stroke-width="1.5"/><path d="M9 22v-4h6v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/condo/dashboard' },
      { label: 'Propiedades', route: '/condo/properties' },
      { label: 'Residentes', route: '/condo/residents' },
      { label: 'Cuotas', route: '/condo/fees' },
      { label: 'Areas Comunes', route: '/condo/areas' },
      { label: 'Mantenimiento', route: '/condo/maintenance' },
      { label: 'Asambleas', route: '/condo/governance' },
      { label: 'Comunicados', route: '/condo/announcements' },
    ],
  },
  crm: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/><path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M21 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/crm/dashboard' },
      { label: 'Contactos', route: '/crm/contacts' },
      { label: 'Empresas', route: '/crm/companies' },
      { label: 'Leads', route: '/crm/leads' },
      { label: 'Pipelines', route: '/crm/pipelines' },
      { label: 'Deals', route: '/crm/deals' },
      { label: 'Actividades', route: '/crm/activities' },
    ],
  },
  credit: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><rect x="1" y="4" width="22" height="16" rx="2" ry="2" stroke="currentColor" stroke-width="1.5"/><line x1="1" y1="10" x2="23" y2="10" stroke="currentColor" stroke-width="1.5"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/credit/dashboard' },
      { label: 'Productos', route: '/credit/products' },
      { label: 'Prestatarios', route: '/credit/borrowers' },
      { label: 'Solicitudes', route: '/credit/applications' },
      { label: 'Préstamos', route: '/credit/loans' },
      { label: 'Pagos', route: '/credit/payments' },
    ],
  },
  family: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/><path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    items: [
      { label: 'Dashboard', route: '/family/dashboard' },
      { label: 'Familias', route: '/family/list' },
    ],
  },
  pos: {
    icon: `<svg class="size-6" viewBox="0 0 24 24" fill="none"><path d="M3 3H5L5.4 5M7 13H17L21 5H5.4M7 13L5.4 5M7 13L4.707 15.293C4.077 15.923 4.523 17 5.414 17H17M17 17C15.895 17 15 17.895 15 19C15 20.105 15.895 21 17 21C18.105 21 19 20.105 19 19C19 17.895 18.105 17 17 17ZM9 19C9 20.105 8.105 21 7 21C5.895 21 5 20.105 5 19C5 17.895 5.895 17 7 17C8.105 17 9 17.895 9 19Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    items: [
      { label: 'Ventas', route: '/pos/sales' },
      { label: 'Productos', route: '/pos/products' },
      { label: 'Inventario', route: '/pos/inventory' },
    ],
  },
};

@Component({
  selector: 'app-sidebar',
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
})
export class SidebarComponent implements OnInit, OnDestroy {
  private readonly sidebarService = inject(SidebarService);
  private readonly appsService = inject(AppsService);
  private appsSub?: Subscription;

  isExpanded$ = this.sidebarService.isExpanded$;
  isMobileOpen$ = this.sidebarService.isMobileOpen$;
  isHovered$ = this.sidebarService.isHovered$;

  readonly appVersion = APP_VERSION;
  appMenus = signal<AppMenu[]>([]);

  ngOnInit(): void {
    // Subscribe to reactive apps stream — updates automatically when apps change
    this.appsSub = this.appsService.apps$.subscribe((apps) => {
      const currentOpen = new Set(this.appMenus().filter(m => m.open).map(m => m.code));
      const menus = apps
        .filter(a => APP_MENUS[a.app.code])
        .map(a => ({
          code: a.app.code,
          name: a.app.name,
          icon: APP_MENUS[a.app.code].icon,
          open: currentOpen.has(a.app.code),
          items: APP_MENUS[a.app.code].items,
        }));
      this.appMenus.set(menus);
    });

    // Trigger initial load
    this.appsService.getMyApps().subscribe();
  }

  ngOnDestroy(): void {
    this.appsSub?.unsubscribe();
  }

  onMouseEnter(): void {
    if (!this.sidebarService.isExpanded) {
      this.sidebarService.setHovered(true);
    }
  }

  onMouseLeave(): void {
    this.sidebarService.setHovered(false);
  }

  toggleMenu(menu: AppMenu): void {
    menu.open = !menu.open;
  }
}
