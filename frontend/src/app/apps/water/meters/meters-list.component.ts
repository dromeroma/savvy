import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  MeterStatus,
  WaterMeterCreate,
  WaterMeterListItem,
  WaterSubscriberListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-meters-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './meters-list.component.html',
})
export class MetersListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  meters = signal<WaterMeterListItem[]>([]);
  subscribers = signal<WaterSubscriberListItem[]>([]);

  // Filters
  search = '';
  filterStatus = '';
  unassignedOnly = false;
  private searchTimer: any;

  // Form
  formOpen = signal(false);
  editing = signal<WaterMeterListItem | null>(null);
  saving = signal(false);
  formError = signal('');
  form: WaterMeterCreate = this.emptyForm();

  readonly statuses: { value: MeterStatus | ''; label: string }[] = [
    { value: '', label: 'Todos los estados' },
    { value: 'active', label: 'Activo' },
    { value: 'replaced', label: 'Reemplazado' },
    { value: 'damaged', label: 'Dañado' },
    { value: 'inactive', label: 'Inactivo' },
  ];

  ngOnInit(): void {
    // Load subscribers once for the picker (small datasets in phase 1)
    this.water.listSubscribers({ limit: 500 }).subscribe({
      next: (data) => this.subscribers.set(data),
    });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.water.listMeters({
      search: this.search || undefined,
      status: this.filterStatus || undefined,
      unassigned_only: this.unassignedOnly || undefined,
    }).subscribe({
      next: (data) => {
        this.meters.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudieron cargar los medidores.',
        });
      },
    });
  }

  onSearchChange(): void {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.load(), 300);
  }

  openCreate(): void {
    this.editing.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(m: WaterMeterListItem): void {
    this.editing.set(m);
    this.water.getMeter(m.id).subscribe({
      next: (full) => {
        this.form = {
          subscriber_id: full.subscriber_id,
          serial_number: full.serial_number,
          brand: full.brand,
          model: full.model,
          diameter: full.diameter,
          install_date: full.install_date,
          initial_reading: full.initial_reading,
          last_reading: full.last_reading,
          last_reading_date: full.last_reading_date,
          status: full.status,
          location_notes: full.location_notes,
        };
        this.formError.set('');
        this.formOpen.set(true);
      },
    });
  }

  closeForm(): void {
    this.formOpen.set(false);
  }

  submit(): void {
    if (!this.form.serial_number) {
      this.formError.set('El número de serie es obligatorio.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    const e = this.editing();
    const obs = e
      ? this.water.updateMeter(e.id, this.stripImmutable(this.form))
      : this.water.createMeter(this.form);
    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({
          type: 'success',
          title: e ? 'Actualizado' : 'Creado',
          message: e ? 'Medidor actualizado.' : 'Medidor creado.',
        });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail;
        this.formError.set(typeof detail === 'string' ? detail : 'Error al guardar.');
      },
    });
  }

  confirmDelete(m: WaterMeterListItem): void {
    if (!confirm(`¿Eliminar el medidor ${m.serial_number}?`)) return;
    this.water.deleteMeter(m.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminado', message: 'Medidor eliminado.' });
        this.load();
      },
      error: (err) => {
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo eliminar.',
        });
      },
    });
  }

  badgeClass(status: string): string {
    switch (status) {
      case 'active': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'replaced': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'damaged': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'inactive': return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  private emptyForm(): WaterMeterCreate {
    return {
      serial_number: '',
      initial_reading: '0',
      last_reading: '0',
      status: 'active',
    };
  }

  private stripImmutable(data: WaterMeterCreate): Partial<WaterMeterCreate> {
    const { serial_number, ...rest } = data;
    return rest;
  }
}
