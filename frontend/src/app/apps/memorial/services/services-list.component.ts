import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  MemorialServiceCreate,
  MemorialServiceListItem,
  MemorialServiceStatus,
  MemorialServiceType,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-services-list',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './services-list.component.html',
})
export class MemorialServicesListComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);
  private readonly router = inject(Router);

  loading = signal(true);
  services = signal<MemorialServiceListItem[]>([]);

  search = '';
  filterStatus = '';
  filterType = '';
  private searchTimer: any;

  formOpen = signal(false);
  saving = signal(false);
  formError = signal('');
  form: MemorialServiceCreate = this.emptyForm();

  readonly statuses: { value: MemorialServiceStatus | ''; label: string }[] = [
    { value: '', label: 'Todos los estados' },
    { value: 'iniciado', label: 'Iniciado' },
    { value: 'en_proceso', label: 'En proceso' },
    { value: 'pendiente', label: 'Pendiente' },
    { value: 'finalizado', label: 'Finalizado' },
    { value: 'cancelado', label: 'Cancelado' },
  ];

  readonly types: { value: MemorialServiceType | ''; label: string }[] = [
    { value: '', label: 'Todos los tipos' },
    { value: 'velacion', label: 'Velación' },
    { value: 'cremacion', label: 'Cremación' },
    { value: 'entierro', label: 'Entierro' },
    { value: 'velacion_cremacion', label: 'Velación + Cremación' },
    { value: 'velacion_entierro', label: 'Velación + Entierro' },
    { value: 'velacion_cremacion_entierro', label: 'Velación + Cremación + Entierro' },
  ];

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.memorial.listServices({
      search: this.search || undefined,
      status: this.filterStatus || undefined,
      service_type: this.filterType || undefined,
    }).subscribe({
      next: (data) => { this.services.set(data); this.loading.set(false); },
      error: (err) => {
        this.loading.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudieron cargar los servicios.',
        });
      },
    });
  }

  onSearchChange(): void {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.load(), 300);
  }

  openCreate(): void {
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  submit(): void {
    if (!this.form.deceased_first_name || !this.form.deceased_death_date || !this.form.service_type) {
      this.formError.set('Nombres del fallecido, fecha de defunción y tipo de servicio son obligatorios.');
      return;
    }
    this.saving.set(true);
    this.formError.set('');
    this.memorial.createService(this.form).subscribe({
      next: (svc) => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({
          type: 'success', title: 'Servicio creado',
          message: `${svc.code} · ${svc.deceased_first_name} ${svc.deceased_last_name || ''}`.trim(),
        });
        this.router.navigate(['/memorial/services', svc.id]);
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail;
        this.formError.set(typeof detail === 'string' ? detail : 'Error al crear el servicio.');
      },
    });
  }

  badge(s: string): string {
    switch (s) {
      case 'iniciado': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'en_proceso': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'pendiente': return 'bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300';
      case 'finalizado': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'cancelado': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 line-through';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  statusLabel(s: string): string {
    switch (s) {
      case 'iniciado': return 'Iniciado';
      case 'en_proceso': return 'En proceso';
      case 'pendiente': return 'Pendiente';
      case 'finalizado': return 'Finalizado';
      case 'cancelado': return 'Cancelado';
      default: return s;
    }
  }

  typeLabel(t: string): string {
    const found = this.types.find((x) => x.value === t);
    return found?.label || t;
  }

  private emptyForm(): MemorialServiceCreate {
    return {
      deceased_first_name: '',
      deceased_last_name: '',
      deceased_document_type: null,
      deceased_document_number: null,
      deceased_death_date: new Date().toISOString().slice(0, 10),
      service_type: 'velacion',
      status: 'iniciado',
      estimated_total: '0',
      family_members: [
        {
          first_name: '',
          last_name: '',
          relationship: '',
          mobile: '',
          email: '',
          is_primary: true,
        },
      ],
    };
  }
}
