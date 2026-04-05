import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { SidebarService } from '../../shared/services/sidebar.service';
import { ThemeService } from '../../shared/services/theme.service';
import { ThemeToggleComponent } from '../../shared/components/common/theme-toggle/theme-toggle.component';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';

@Component({
  selector: 'app-layout',
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    ThemeToggleComponent,
    AlertComponent,
  ],
  templateUrl: './layout.component.html',
})
export class LayoutComponent implements OnInit, OnDestroy {
  readonly sidebarService = inject(SidebarService);
  private readonly auth = inject(AuthService);
  private readonly themeService = inject(ThemeService);
  private subs: Subscription[] = [];

  isExpanded = true;
  isMobileOpen = false;
  isHovered = false;
  churchMenuOpen = false;

  userName = '';
  orgName = '';

  get showFull(): boolean {
    return this.isExpanded || this.isHovered || this.isMobileOpen;
  }

  ngOnInit() {
    this.subs.push(
      this.sidebarService.isExpanded$.subscribe(v => this.isExpanded = v),
      this.sidebarService.isMobileOpen$.subscribe(v => this.isMobileOpen = v),
      this.sidebarService.isHovered$.subscribe(v => this.isHovered = v),
    );

    const user = this.auth.getCurrentUser();
    this.userName = user?.name || 'Usuario';
    this.orgName = this.getOrgNameFromToken();
  }

  ngOnDestroy() {
    this.subs.forEach(s => s.unsubscribe());
  }

  onSidebarHover(hovered: boolean) {
    if (!this.isExpanded) {
      this.sidebarService.setHovered(hovered);
    }
  }

  toggleChurchMenu() {
    this.churchMenuOpen = !this.churchMenuOpen;
  }

  logout() {
    this.auth.logout();
  }

  private getOrgNameFromToken(): string {
    const token = this.auth.getToken();
    if (!token) return '';
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.org_name ?? payload.organization?.name ?? '';
    } catch {
      return '';
    }
  }
}
