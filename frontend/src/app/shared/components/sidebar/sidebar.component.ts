import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { SidebarService } from '../../services/sidebar.service';
import { ThemeToggleComponent } from '../common/theme-toggle/theme-toggle.component';

@Component({
  selector: 'app-sidebar',
  imports: [CommonModule, RouterLink, RouterLinkActive, ThemeToggleComponent],
  templateUrl: './sidebar.component.html',
})
export class SidebarComponent {
  private readonly sidebarService = inject(SidebarService);

  isExpanded$ = this.sidebarService.isExpanded$;
  isMobileOpen$ = this.sidebarService.isMobileOpen$;
  isHovered$ = this.sidebarService.isHovered$;

  churchMenuOpen = false;

  onMouseEnter(): void {
    if (!this.sidebarService.isExpanded) {
      this.sidebarService.setHovered(true);
    }
  }

  onMouseLeave(): void {
    this.sidebarService.setHovered(false);
  }

  toggleExpanded(): void {
    this.sidebarService.toggleExpanded();
  }

  toggleChurchMenu(): void {
    this.churchMenuOpen = !this.churchMenuOpen;
  }
}
