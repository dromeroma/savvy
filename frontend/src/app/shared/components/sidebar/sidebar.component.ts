import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
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
      { label: 'Miembros', route: '/church/members' },
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
export class SidebarComponent implements OnInit {
  private readonly sidebarService = inject(SidebarService);
  private readonly appsService = inject(AppsService);

  isExpanded$ = this.sidebarService.isExpanded$;
  isMobileOpen$ = this.sidebarService.isMobileOpen$;
  isHovered$ = this.sidebarService.isHovered$;

  readonly appVersion = APP_VERSION;
  appMenus = signal<AppMenu[]>([]);

  ngOnInit(): void {
    this.appsService.getMyApps().subscribe({
      next: (apps) => {
        const menus = apps
          .filter(a => APP_MENUS[a.app.code])
          .map(a => ({
            code: a.app.code,
            name: a.app.name,
            icon: APP_MENUS[a.app.code].icon,
            open: false,
            items: APP_MENUS[a.app.code].items,
          }));
        this.appMenus.set(menus);
      },
      error: () => {},
    });
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
