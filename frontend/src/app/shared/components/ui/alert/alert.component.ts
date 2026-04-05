import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { AlertService, AlertConfig } from '../../../services/alert.service';

@Component({
  selector: 'app-alert',
  imports: [CommonModule],
  templateUrl: './alert.component.html',
})
export class AlertComponent implements OnInit, OnDestroy {
  private readonly alertService = inject(AlertService);
  private sub!: Subscription;
  private timer: any;

  config: AlertConfig = { isOpen: false, type: 'info', title: '', message: '' };

  ngOnInit() {
    this.sub = this.alertService.alertState$.subscribe(state => {
      this.config = state;
      if (state.isOpen && state.autoClose) {
        clearTimeout(this.timer);
        this.timer = setTimeout(() => this.close(), state.autoCloseDelay || 3000);
      }
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
    clearTimeout(this.timer);
  }

  close() {
    this.alertService.close();
  }

  get iconColor(): string {
    const map: Record<string, string> = {
      success: 'text-success-500', error: 'text-error-500',
      warning: 'text-warning-500', info: 'text-blue-light-500',
    };
    return map[this.config.type] || 'text-blue-light-500';
  }

  get bgColor(): string {
    const map: Record<string, string> = {
      success: 'bg-success-50 border-success-200 dark:bg-success-500/10 dark:border-success-500/30',
      error: 'bg-error-50 border-error-200 dark:bg-error-500/10 dark:border-error-500/30',
      warning: 'bg-warning-50 border-warning-200 dark:bg-warning-500/10 dark:border-warning-500/30',
      info: 'bg-blue-light-50 border-blue-light-200 dark:bg-blue-light-500/10 dark:border-blue-light-500/30',
    };
    return map[this.config.type] || '';
  }
}
