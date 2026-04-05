import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type AlertType = 'success' | 'info' | 'warning' | 'error';

export interface AlertConfig {
  isOpen: boolean;
  type: AlertType;
  title: string;
  message: string;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

@Injectable({ providedIn: 'root' })
export class AlertService {
  private _alertState = new BehaviorSubject<AlertConfig>({
    isOpen: false,
    type: 'info',
    title: '',
    message: '',
    autoClose: true,
    autoCloseDelay: 3000,
  });

  alertState$ = this._alertState.asObservable();
  private ignoreOpenUntil = 0;

  get isAlertOpen(): boolean {
    return this._alertState.value.isOpen;
  }

  show(config: Omit<AlertConfig, 'isOpen'>) {
    if (Date.now() < this.ignoreOpenUntil) return;
    this._alertState.next({ ...config, isOpen: true });
  }

  close() {
    const current = this._alertState.value;
    this._alertState.next({ ...current, isOpen: false });
    this.ignoreOpenUntil = Date.now() + 300;
  }
}
