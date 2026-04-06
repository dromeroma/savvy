import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService, AppNotification } from '../../services/notification.service';

@Component({
  selector: 'app-notification-container',
  imports: [CommonModule],
  templateUrl: './notification-container.component.html',
})
export class NotificationContainerComponent {
  private readonly notificationService = inject(NotificationService);
  notifications = computed(() => this.notificationService.notifications());

  remove(id: number) { this.notificationService.remove(id); }

  getTypeClasses(type: string): string {
    switch (type) {
      case 'success': return 'text-emerald-900 border-emerald-300/90 bg-emerald-100/70 backdrop-blur dark:text-white dark:bg-emerald-600/30 dark:border-emerald-400/40';
      case 'error': return 'text-rose-900 border-rose-300/90 bg-rose-100/70 backdrop-blur dark:text-white dark:bg-rose-600/30 dark:border-rose-400/40';
      case 'warning': return 'text-amber-900 border-amber-300/90 bg-amber-100/70 backdrop-blur dark:text-white dark:bg-amber-600/30 dark:border-amber-400/40';
      default: return 'text-blue-900 border-blue-300/90 bg-blue-100/70 backdrop-blur dark:text-white dark:bg-blue-600/30 dark:border-blue-400/40';
    }
  }

  getIcon(type: string): string {
    switch (type) {
      case 'success': return '\u2705';
      case 'error': return '\u274C';
      case 'warning': return '\u26A0\uFE0F';
      default: return '\u2139\uFE0F';
    }
  }
}
