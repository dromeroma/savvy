import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { SidebarService } from '../../shared/services/sidebar.service';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';

@Component({
  selector: 'app-layout',
  imports: [
    CommonModule,
    RouterOutlet,
    SidebarComponent,
    AlertComponent,
  ],
  templateUrl: './layout.component.html',
})
export class LayoutComponent implements OnInit {
  readonly sidebarService = inject(SidebarService);
  private readonly auth = inject(AuthService);

  isExpanded$ = this.sidebarService.isExpanded$;
  isMobileOpen$ = this.sidebarService.isMobileOpen$;

  userName = '';
  orgName = '';

  ngOnInit() {
    const user = this.auth.getCurrentUser();
    this.userName = user?.name || 'Usuario';
    this.orgName = this.getOrgNameFromToken();
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
