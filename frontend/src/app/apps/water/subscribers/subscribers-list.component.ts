import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  SubscriberStatus,
  SubscriberType,
  WaterSubscriberCreate,
  WaterSubscriberListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-subscribers-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './subscribers-list.component.html',
})
export class SubscribersListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  subscribers = signal<WaterSubscriberListItem[]>([]);

  // Filters
  search = '';
  filterStatus = '';
  filterType = '';
  private searchTimer: any;

  // Form / modal
  formOpen = signal(false);
  editing = signal<WaterSubscriberListItem | null>(null);
  saving = signal(false);
  formError = signal('');

  form: WaterSubscriberCreate = this.emptyForm();

  readonly statuses: { value: SubscriberStatus | ''; label: string }[] = [
    { value: '', label: 'Todos los estados' },
    { value: 'active', label: 'Activo' },
    { value: 'suspended', label: 'Suspendido' },
    { value: 'overdue', label: 'En mora' },
    { value: 'retired', label: 'Retirado' },
  ];
  readonly types: { value: SubscriberType | ''; label: string }[] = [
    { value: '', label: 'Todos los tipos' },
    { value: 'residential', label: 'Residencial' },
    { value: 'commercial', label: 'Comercial' },
    { value: 'industrial', label: 'Industrial' },
    { value: 'official', label: 'Oficial' },
  ];

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.water.listSubscribers({
      search: this.search || undefined,
      status: this.filterStatus || undefined,
      subscriber_type: this.filterType || undefined,
    }).subscribe({
      next: (data) => {
        this.subscribers.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.notify.show({
          type: 'error',
          title: 'Error',
          message: err?.error?.detail || 'No se pudieron cargar los suscriptores.',
        });
      },
    });
  }

  onSearchChange(): void {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.load(), 300);
  }

  // ---- Form ----
  openCreate(): void {
    this.editing.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(s: WaterSubscriberListItem): void {
    this.editing.set(s);
    this.water.getSubscriber(s.id).subscribe({
      next: (full) => {
        this.form = {
          code: full.code,
          document_type: full.document_type,
          document_number: full.document_number,
          first_name: full.first_name,
          last_name: full.last_name,
          business_name: full.business_name,
          email: full.email,
          phone: full.phone,
          mobile: full.mobile,
          address: full.address,
          neighborhood: full.neighborhood,
          stratum: full.stratum,
          subscriber_type: full.subscriber_type,
          status: full.status,
          notes: full.notes,
          registered_at: full.registered_at,
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
    if (!this.form.code || !this.form.first_name) {
      this.formError.set('Código y nombre son obligatorios.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    const e = this.editing();
    const obs = e
      ? this.water.updateSubscriber(e.id, this.stripImmutable(this.form))
      : this.water.createSubscriber(this.form);
    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({
          type: 'success',
          title: e ? 'Actualizado' : 'Creado',
          message: e ? 'Suscriptor actualizado.' : 'Suscriptor creado.',
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

  confirmDelete(s: WaterSubscriberListItem): void {
    if (!confirm(`¿Eliminar al suscriptor ${s.code} — ${s.first_name}?`)) return;
    this.water.deleteSubscriber(s.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminado', message: 'Suscriptor eliminado.' });
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
      case 'suspended': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'overdue': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'retired': return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  displayName(s: WaterSubscriberListItem): string {
    if (s.business_name) return s.business_name;
    return [s.first_name, s.last_name].filter(Boolean).join(' ');
  }

  private emptyForm(): WaterSubscriberCreate {
    return {
      code: '',
      first_name: '',
      subscriber_type: 'residential',
      status: 'active',
    };
  }

  private stripImmutable(data: WaterSubscriberCreate): Partial<WaterSubscriberCreate> {
    const { code, ...rest } = data;
    return rest;
  }
}
