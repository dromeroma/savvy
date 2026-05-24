import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import { ApiService } from '../../../core/services/api.service';
import {
  RouteAssignment,
  WaterRoute,
  WaterRouteCreate,
  WaterRouteListItem,
  WaterSubscriberListItem,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

interface PlatformUserSummary {
  id: string;
  name: string;
  email: string;
}

@Component({
  selector: 'app-routes-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './routes-list.component.html',
})
export class RoutesListComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  routes = signal<WaterRouteListItem[]>([]);
  subscribers = signal<WaterSubscriberListItem[]>([]);
  /** Cached "users assignable as collector" — we reuse /platform/users via super
   * admin OR /apps/{code}/users if non-admin. For phase 3 we ask the user to
   * type the user UUID; future iteration: org members picker. */
  collectorPicker = signal<string>('');

  // Route form
  formOpen = signal(false);
  editing = signal<WaterRouteListItem | null>(null);
  saving = signal(false);
  formError = signal('');
  form: WaterRouteCreate = this.emptyForm();

  // Assignments panel
  assignOpen = signal(false);
  assignRoute = signal<WaterRouteListItem | null>(null);
  assignments = signal<RouteAssignment[]>([]);
  newAssignSubscriberId = '';

  ngOnInit(): void {
    this.water.listSubscribers({ limit: 500 }).subscribe({
      next: (data) => this.subscribers.set(data),
    });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.water.listRoutes().subscribe({
      next: (data) => {
        this.routes.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  // --- Route CRUD ---
  openCreate(): void {
    this.editing.set(null);
    this.form = this.emptyForm();
    this.collectorPicker.set('');
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(r: WaterRouteListItem): void {
    this.editing.set(r);
    this.water.getRoute(r.id).subscribe({
      next: (full) => {
        this.form = {
          code: full.code,
          name: full.name,
          description: full.description,
          collector_user_id: full.collector_user_id,
          is_active: full.is_active,
        };
        this.collectorPicker.set(full.collector_user_id ?? '');
        this.formError.set('');
        this.formOpen.set(true);
      },
    });
  }

  closeForm(): void { this.formOpen.set(false); }

  submit(): void {
    if (!this.form.code || !this.form.name) {
      this.formError.set('Código y nombre son obligatorios.');
      return;
    }
    this.form.collector_user_id = this.collectorPicker().trim() || null;
    this.saving.set(true);
    this.formError.set('');
    const e = this.editing();
    const obs = e
      ? this.water.updateRoute(e.id, this.stripImmutable(this.form))
      : this.water.createRoute(this.form);
    obs.subscribe({
      next: () => {
        this.saving.set(false);
        this.closeForm();
        this.notify.show({ type: 'success', title: e ? 'Actualizada' : 'Creada', message: 'Ruta guardada.' });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.formError.set(err?.error?.detail || 'Error al guardar.');
      },
    });
  }

  confirmDelete(r: WaterRouteListItem): void {
    if (!confirm(`¿Eliminar la ruta "${r.name}" y todas sus asignaciones?`)) return;
    this.water.deleteRoute(r.id).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminada', message: 'Ruta eliminada.' });
        this.load();
      },
      error: (err) => {
        this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo eliminar.' });
      },
    });
  }

  // --- Assignments ---
  openAssign(r: WaterRouteListItem): void {
    this.assignRoute.set(r);
    this.water.listRouteAssignments(r.id).subscribe({
      next: (data) => {
        this.assignments.set(data);
        this.newAssignSubscriberId = '';
        this.assignOpen.set(true);
      },
    });
  }
  closeAssign(): void { this.assignOpen.set(false); }

  addAssignment(): void {
    const r = this.assignRoute();
    if (!r || !this.newAssignSubscriberId) return;
    this.water.assignToRoute(r.id, this.newAssignSubscriberId).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Asignado', message: 'Suscriptor agregado a la ruta.' });
        this.openAssign(r);
        this.load();
      },
      error: (err) => {
        this.notify.show({ type: 'error', title: 'Error', message: err?.error?.detail || 'No se pudo asignar.' });
      },
    });
  }

  removeAssignment(a: RouteAssignment): void {
    const r = this.assignRoute();
    if (!r) return;
    if (!confirm(`¿Quitar ${a.subscriber_code} de la ruta?`)) return;
    this.water.unassignFromRoute(r.id, a.subscriber_id).subscribe({
      next: () => {
        this.openAssign(r);
        this.load();
      },
    });
  }

  /** Subscribers NOT yet assigned to the current route (for the picker). */
  get availableForAssignment(): WaterSubscriberListItem[] {
    const taken = new Set(this.assignments().map((a) => a.subscriber_id));
    return this.subscribers().filter((s) => !taken.has(s.id));
  }

  private emptyForm(): WaterRouteCreate {
    return {
      code: '',
      name: '',
      description: null,
      collector_user_id: null,
      is_active: true,
    };
  }

  private stripImmutable(data: WaterRouteCreate): Partial<WaterRouteCreate> {
    const { code, ...rest } = data;
    return rest;
  }
}
