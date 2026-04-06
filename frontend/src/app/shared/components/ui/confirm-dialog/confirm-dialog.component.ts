import { Component, computed, inject } from '@angular/core';
import { ConfirmDialogService } from '../../../services/confirm-dialog.service';

@Component({
  selector: 'app-confirm-dialog',
  imports: [],
  templateUrl: './confirm-dialog.component.html',
})
export class ConfirmDialogComponent {
  private readonly confirmService = inject(ConfirmDialogService);
  config = computed(() => this.confirmService.config());

  get type(): string {
    return this.config()?.type ?? 'danger';
  }

  get confirmText(): string {
    return this.config()?.confirmText ?? 'Confirmar';
  }

  get cancelText(): string {
    return this.config()?.cancelText ?? 'Cancelar';
  }

  onConfirm(): void {
    this.confirmService.respond(true);
  }

  onCancel(): void {
    this.confirmService.respond(false);
  }
}
