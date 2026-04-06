import { Injectable, signal } from '@angular/core';

export interface ConfirmConfig {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning' | 'info';
}

@Injectable({ providedIn: 'root' })
export class ConfirmDialogService {
  config = signal<ConfirmConfig | null>(null);
  private resolver?: (value: boolean) => void;

  confirm(config: ConfirmConfig): Promise<boolean> {
    this.config.set(config);
    return new Promise<boolean>(resolve => {
      this.resolver = resolve;
    });
  }

  respond(value: boolean): void {
    if (this.resolver) {
      this.resolver(value);
      this.resolver = undefined;
    }
    this.config.set(null);
  }
}
