import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  MemorialDriver,
  MemorialServiceListItem,
  MemorialTransferCreate,
  MemorialTransferListItem,
  MemorialVehicle,
  TransferStatus,
  TransferType,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-transfers-list',
  imports: [CommonModule, FormsModule, RouterLink, DatePipe],
  templateUrl: './transfers-list.component.html',
})
export class MemorialTransfersListComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  transfers = signal<MemorialTransferListItem[]>([]);

  vehiclesForPicker = signal<MemorialVehicle[]>([]);
  driversForPicker = signal<MemorialDriver[]>([]);
  servicesForPicker = signal<MemorialServiceListItem[]>([]);

  filterStatus = '';
  filterDateFrom = '';
  filterDateTo = '';

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: MemorialTransferCreate = this.emptyForm();

  readonly statuses: { value: TransferStatus | ''; label: string }[] = [
    { value: '', label: 'Todos los estados' },
    { value: 'scheduled', label: 'Agendado' },
    { value: 'in_progress', label: 'En curso' },
    { value: 'completed', label: 'Completado' },
    { value: 'cancelled', label: 'Cancelado' },
  ];

  readonly types: { value: TransferType; label: string }[] = [
    { value: 'pickup', label: 'Recogida del cuerpo' },
    { value: 'to_velation', label: 'A velación' },
    { value: 'to_cremation', label: 'A cremación' },
    { value: 'to_burial', label: 'Al cementerio' },
    { value: 'to_mass', label: 'A misa' },
    { value: 'family', label: 'Familiar' },
    { value: 'other', label: 'Otro' },
  ];

  ngOnInit(): void {
    this.load();
    this.memorial.listVehicles().subscribe({ next: (d) => this.vehiclesForPicker.set(d.filter(v => v.status === 'active')) });
    this.memorial.listDrivers().subscribe({ next: (d) => this.driversForPicker.set(d.filter(x => x.is_active)) });
    this.memorial.listServices({ limit: 200 }).subscribe({ next: (d) => this.servicesForPicker.set(d) });
  }

  load(): void {
    this.loading.set(true);
    this.memorial.listTransfers({
      status: this.filterStatus || undefined,
      date_from: this.filterDateFrom || undefined,
      date_to: this.filterDateTo || undefined,
    }).subscribe({
      next: (data) => { this.transfers.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  submit(): void {
    if (!this.form.transfer_type || !this.form.scheduled_at) {
      this.formError.set('Tipo de traslado y horario son obligatorios.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    this.memorial.createTransfer(this.form).subscribe({
      next: (t) => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({ type: 'success', title: 'Traslado agendado', message: t.code });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail;
        this.formError.set(typeof detail === 'string' ? detail : 'Error al agendar.');
      },
    });
  }

  transition(t: MemorialTransferListItem, newStatus: TransferStatus): void {
    const label = this.statusLabel(newStatus);
    if (!confirm(`¿Cambiar el traslado ${t.code} a "${label}"?`)) return;
    this.memorial.transitionTransfer(t.id, newStatus).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Actualizado', message: label }); this.load(); },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo cambiar el estado.',
      }),
    });
  }

  remove(t: MemorialTransferListItem): void {
    if (!confirm(`¿Eliminar el traslado ${t.code}?`)) return;
    this.memorial.deleteTransfer(t.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: t.code }); this.load(); },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo eliminar.',
      }),
    });
  }

  typeLabel(t: string): string {
    return this.types.find(x => x.value === t)?.label || t;
  }

  statusLabel(s: string): string {
    return this.statuses.find(x => x.value === s)?.label || s;
  }

  badge(s: string): string {
    switch (s) {
      case 'scheduled': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'in_progress': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'completed': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'cancelled': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 line-through';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  // Transiciones permitidas desde el estado actual
  allowedFrom(s: string): TransferStatus[] {
    switch (s) {
      case 'scheduled': return ['in_progress', 'cancelled'];
      case 'in_progress': return ['completed', 'cancelled'];
      default: return [];
    }
  }

  private emptyForm(): MemorialTransferCreate {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 60);
    return {
      service_id: null,
      transfer_type: 'pickup',
      vehicle_id: null,
      driver_id: null,
      scheduled_at: now.toISOString().slice(0, 16),  // datetime-local
      origin: '',
      destination: '',
    };
  }
}
