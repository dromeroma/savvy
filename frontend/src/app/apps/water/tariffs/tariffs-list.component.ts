import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import { SubscriberType, WaterTariff, WaterTariffCreate } from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-tariffs-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './tariffs-list.component.html',
})
export class TariffsListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  tariffs = signal<WaterTariff[]>([]);
  activeOnly = false;

  formOpen = signal(false);
  editing = signal<WaterTariff | null>(null);
  saving = signal(false);
  formError = signal('');
  form: WaterTariffCreate = this.emptyForm();

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.water.listTariffs(this.activeOnly).subscribe({
      next: (data) => {
        this.tariffs.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.editing.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(t: WaterTariff): void {
    this.editing.set(t);
    this.form = {
      code: t.code,
      name: t.name,
      subscriber_type: t.subscriber_type,
      stratum: t.stratum,
      fixed_charge: t.fixed_charge,
      price_per_cubic: t.price_per_cubic,
      basic_limit_cubic: t.basic_limit_cubic,
      surplus_price_per_cubic: t.surplus_price_per_cubic,
      reconnection_fee: t.reconnection_fee,
      suspension_fee: t.suspension_fee,
      late_interest_rate: t.late_interest_rate,
      is_active: t.is_active,
      valid_from: t.valid_from,
      valid_to: t.valid_to,
    };
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  submit(): void {
    if (!this.form.code || !this.form.name || !this.form.valid_from) {
      this.formError.set('Código, nombre y fecha de inicio son obligatorios.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    const e = this.editing();
    const obs = e
      ? this.water.updateTariff(e.id, this.stripImmutable(this.form))
      : this.water.createTariff(this.form);
    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({ type: 'success', title: e ? 'Actualizada' : 'Creada', message: 'Tarifa guardada.' });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'Error al guardar.');
      },
    });
  }

  confirmDelete(t: WaterTariff): void {
    if (!confirm(`¿Eliminar la tarifa "${t.name}"?`)) return;
    this.water.deleteTariff(t.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminada', message: 'Tarifa eliminada.' });
        this.load();
      },
      error: (err) => {
        this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo eliminar.' });
      },
    });
  }

  typeBadge(t: SubscriberType): string {
    switch (t) {
      case 'residential': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'commercial': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'industrial': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'official': return 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300';
    }
  }

  private emptyForm(): WaterTariffCreate {
    return {
      code: '',
      name: '',
      subscriber_type: 'residential',
      fixed_charge: 0,
      price_per_cubic: 0,
      reconnection_fee: 0,
      suspension_fee: 0,
      late_interest_rate: 0,
      is_active: true,
      valid_from: new Date().toISOString().slice(0, 10),
    };
  }

  private stripImmutable(data: WaterTariffCreate): Partial<WaterTariffCreate> {
    const { code, ...rest } = data;
    return rest;
  }
}
