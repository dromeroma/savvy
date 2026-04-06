import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';
import { SidebarService } from '../../shared/services/sidebar.service';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';
import { ThemeToggleComponent } from '../../shared/components/common/theme-toggle/theme-toggle.component';
import { NotificationContainerComponent } from '../../shared/components/notifications/notification-container.component';

@Component({
  selector: 'app-layout',
  imports: [CommonModule, RouterOutlet, SidebarComponent, AlertComponent, ThemeToggleComponent, NotificationContainerComponent],
  templateUrl: './layout.component.html',
})
export class LayoutComponent implements OnInit {
  readonly sidebarService = inject(SidebarService);
  private readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);

  isExpanded$ = this.sidebarService.isExpanded$;
  isMobileOpen$ = this.sidebarService.isMobileOpen$;

  userName = '';
  userEmail = '';
  orgName = '';
  userInitials = '';

  ngOnInit() {
    // Fetch real user profile from API
    this.api.get<{ name: string; email: string }>('/auth/me').subscribe({
      next: (user) => {
        this.userName = user.name || 'Usuario';
        this.userEmail = user.email || '';
        this.userInitials = this.getInitials(user.name);
      },
      error: () => {
        this.userName = 'Usuario';
        this.userInitials = 'U';
      },
    });
  }

  handleToggle() {
    if (window.innerWidth >= 1280) {
      this.sidebarService.toggleExpanded();
    } else {
      this.sidebarService.toggleMobileOpen();
    }
  }

  logout() {
    this.auth.logout();
  }

  private getInitials(name: string): string {
    if (!name) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name[0].toUpperCase();
  }
}
