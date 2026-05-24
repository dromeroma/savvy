import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  WaterConsumptionCreate,
  WaterConsumptionListItem,
  WaterMeterListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-consumptions-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './consumptions-list.component.html',
})
export class ConsumptionsListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  rows = signal<WaterConsumptionListItem[]>([]);
  meters = signal<WaterMeterListItem[]>([]);

  // Filters
  filterYear = new Date().getFullYear();
  filterMonth = new Date().getMonth() + 1;

  // Form
  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: WaterConsumptionCreate = this.emptyForm();
  /** previous_reading from the selected meter — shown so the user knows the floor */
  previousFromMeter = signal<string>('0');

  readonly consumptionPreview = computed(() => {
    const prev = parseFloat(this.previousFromMeter() || '0');
    const curr = parseFloat(String(this.form.current_reading || 0));
    if (isNaN(prev) || isNaN(curr)) return '—';
    const diff = curr - prev;
    if (diff < 0) return 'Inválida (< anterior)';
    return diff.toFixed(2) + ' m³';
  });

  readonly years = (() => {
    const y = new Date().getFullYear();
    return [y - 2, y - 1, y, y + 1];
  })();
  readonly months = [
    { v: 1, n: 'Enero' }, { v: 2, n: 'Febrero' }, { v: 3, n: 'Marzo' },
    { v: 4, n: 'Abril' }, { v: 5, n: 'Mayo' }, { v: 6, n: 'Junio' },
    { v: 7, n: 'Julio' }, { v: 8, n: 'Agosto' }, { v: 9, n: 'Septiembre' },
    { v: 10, n: 'Octubre' }, { v: 11, n: 'Noviembre' }, { v: 12, n: 'Diciembre' },
  ];

  ngOnInit(): void {
    this.water.listMeters({ limit: 500 }).subscribe({
      next: (data) => this.meters.set(data),
    });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.water.listConsumptions({
      period_year: this.filterYear,
      period_month: this.filterMonth,
    }).subscribe({
      next: (data) => {
        this.rows.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.previousFromMeter.set('0');
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  onMeterChange(meterId: string): void {
    this.form.meter_id = meterId;
    const m = this.meters().find((x) => x.id === meterId);
    this.previousFromMeter.set(m?.last_reading ?? '0');
  }

  submit(): void {
    if (!this.form.meter_id) {
      this.formError.set('Selecciona un medidor.');
      return;
    }
    const prev = parseFloat(this.previousFromMeter() || '0');
    const curr = parseFloat(String(this.form.current_reading || 0));
    if (curr < prev) {
      this.formError.set(`La lectura actual (${curr}) no puede ser menor a la anterior (${prev}).`);
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    this.water.createConsumption(this.form).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({ type: 'success', title: 'Registrada', message: 'Lectura registrada.' });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'Error al guardar.');
      },
    });
  }

  confirmDelete(c: WaterConsumptionListItem): void {
    if (c.has_invoice) {
      this.notify.show({ type: 'error', title: 'No permitido', message: 'Esta lectura tiene una factura asociada.' });
      return;
    }
    if (!confirm(`¿Eliminar la lectura del medidor ${c.meter_serial} del ${c.period_year}-${c.period_month}?`)) return;
    this.water.deleteConsumption(c.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminada', message: 'Lectura eliminada.' });
        this.load();
      },
      error: (err) => {
        this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo eliminar.' });
      },
    });
  }

  /** Assigned meters only — readings require a subscriber. */
  get assignedMeters(): WaterMeterListItem[] {
    return this.meters().filter((m) => m.subscriber_id);
  }

  private emptyForm(): WaterConsumptionCreate {
    const now = new Date();
    return {
      meter_id: '',
      period_year: now.getFullYear(),
      period_month: now.getMonth() + 1,
      reading_date: now.toISOString().slice(0, 10),
      current_reading: 0,
      is_estimated: false,
    };
  }
}
