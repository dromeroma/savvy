import { Injectable, signal } from '@angular/core';
import { SoundManagerService, SoundType } from '../../core/services/sound-manager.service';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface AppNotification {
  id: number;
  type: NotificationType;
  title: string;
  message: string;
  duration: number;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private nextId = 1;
  notifications = signal<AppNotification[]>([]);

  private readonly typeToSound: Record<NotificationType, SoundType> = {
    success: 'success', error: 'error', warning: 'warning', info: 'info',
  };

  constructor(private sound: SoundManagerService) {}

  show(config: { type: NotificationType; title: string; message: string; duration?: number }): void {
    const id = this.nextId++;
    const notification: AppNotification = { id, type: config.type, title: config.title, message: config.message, duration: config.duration ?? 4000 };
    this.notifications.update(list => [...list, notification]);
    this.sound.play(this.typeToSound[config.type]);
    setTimeout(() => this.remove(id), notification.duration);
  }

  remove(id: number): void {
    this.notifications.update(list => list.filter(n => n.id !== id));
  }
}
