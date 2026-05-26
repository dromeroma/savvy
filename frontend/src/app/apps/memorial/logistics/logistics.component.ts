import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  LocationKind,
  MemorialDriver,
  MemorialDriverCreate,
  MemorialLocation,
  MemorialLocationCreate,
  MemorialOven,
  MemorialOvenCreate,
  MemorialRoom,
  MemorialRoomCreate,
  MemorialVehicle,
  MemorialVehicleCreate,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

type Tab = 'vehicles' | 'drivers' | 'rooms' | 'ovens' | 'locations';

@Component({
  selector: 'app-memorial-logistics',
  imports: [CommonModule, FormsModule],
  templateUrl: './logistics.component.html',
})
export class MemorialLogisticsComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  tab = signal<Tab>('vehicles');
  loading = signal(false);

  readonly tabs: Tab[] = ['vehicles', 'drivers', 'rooms', 'ovens', 'locations'];

  // Datos por tab
  vehicles = signal<MemorialVehicle[]>([]);
  drivers = signal<MemorialDriver[]>([]);
  rooms = signal<MemorialRoom[]>([]);
  ovens = signal<MemorialOven[]>([]);
  locations = signal<MemorialLocation[]>([]);

  filterLocationKind: LocationKind | '' = '';

  // Modal form
  formOpen = signal(false);
  editingId = signal<string | null>(null);
  formError = signal('');
  saving = signal(false);

  // Una sola estructura para todos los formularios — usamos any para que
  // el binding sea simple. El submit traduce al tipo correcto.
  form: any = {};

  ngOnInit(): void { this.load(); }

  setTab(t: Tab): void {
    if (this.tab() === t) return;
    this.tab.set(t);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    const done = () => this.loading.set(false);
    switch (this.tab()) {
      case 'vehicles':
        this.memorial.listVehicles().subscribe({
          next: (d) => { this.vehicles.set(d); done(); },
          error: done,
        });
        break;
      case 'drivers':
        this.memorial.listDrivers().subscribe({
          next: (d) => { this.drivers.set(d); done(); },
          error: done,
        });
        break;
      case 'rooms':
        this.memorial.listRooms().subscribe({
          next: (d) => { this.rooms.set(d); done(); },
          error: done,
        });
        break;
      case 'ovens':
        this.memorial.listOvens().subscribe({
          next: (d) => { this.ovens.set(d); done(); },
          error: done,
        });
        break;
      case 'locations':
        this.memorial.listLocations(this.filterLocationKind || undefined).subscribe({
          next: (d) => { this.locations.set(d); done(); },
          error: done,
        });
        break;
    }
  }

  openCreate(): void {
    this.editingId.set(null);
    this.form = this.emptyForm();
    this.formError.set('');
    this.formOpen.set(true);
  }

  openEdit(item: any): void {
    this.editingId.set(item.id);
    this.form = { ...item };
    this.formError.set('');
    this.formOpen.set(true);
  }

  closeForm(): void { this.formOpen.set(false); }

  submit(): void {
    const t = this.tab();
    const id = this.editingId();
    this.saving.set(true);
    this.formError.set('');

    const ok = (msg: string) => {
      this.saving.set(false);
      this.closeForm();
      this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: msg });
      this.load();
    };
    const err = (e: any) => {
      this.saving.set(false);
      const detail = e?.error?.detail;
      this.formError.set(typeof detail === 'string' ? detail : 'Error al guardar.');
    };

    switch (t) {
      case 'vehicles': {
        const payload = this.form as MemorialVehicleCreate;
        if (id) {
          const { code, ...rest } = payload as any;
          this.memorial.updateVehicle(id, rest).subscribe({
            next: (r) => ok(r.plate), error: err,
          });
        } else {
          this.memorial.createVehicle(payload).subscribe({
            next: (r) => ok(r.plate), error: err,
          });
        }
        break;
      }
      case 'drivers': {
        const payload = this.form as MemorialDriverCreate;
        if (id) {
          const { code, ...rest } = payload as any;
          this.memorial.updateDriver(id, rest).subscribe({
            next: (r) => ok(`${r.first_name} ${r.last_name || ''}`.trim()), error: err,
          });
        } else {
          this.memorial.createDriver(payload).subscribe({
            next: (r) => ok(`${r.first_name} ${r.last_name || ''}`.trim()), error: err,
          });
        }
        break;
      }
      case 'rooms': {
        const payload = this.form as MemorialRoomCreate;
        if (id) {
          const { code, ...rest } = payload as any;
          this.memorial.updateRoom(id, rest).subscribe({
            next: (r) => ok(r.name), error: err,
          });
        } else {
          this.memorial.createRoom(payload).subscribe({
            next: (r) => ok(r.name), error: err,
          });
        }
        break;
      }
      case 'ovens': {
        const payload = this.form as MemorialOvenCreate;
        if (id) {
          const { code, ...rest } = payload as any;
          this.memorial.updateOven(id, rest).subscribe({
            next: (r) => ok(r.name), error: err,
          });
        } else {
          this.memorial.createOven(payload).subscribe({
            next: (r) => ok(r.name), error: err,
          });
        }
        break;
      }
      case 'locations': {
        const payload = this.form as MemorialLocationCreate;
        if (id) {
          const { code, kind, ...rest } = payload as any;
          this.memorial.updateLocation(id, rest).subscribe({
            next: (r) => ok(r.name), error: err,
          });
        } else {
          this.memorial.createLocation(payload).subscribe({
            next: (r) => ok(r.name), error: err,
          });
        }
        break;
      }
    }
  }

  confirmDelete(item: any): void {
    if (!confirm(`¿Eliminar este registro?`)) return;
    const t = this.tab();
    const ok = () => {
      this.notify.show({ type: 'success', title: 'Eliminado', message: '' });
      this.load();
    };
    const err = (e: any) => this.notify.show({
      type: 'error', title: 'Error',
      message: e?.error?.detail || 'No se pudo eliminar.',
    });
    switch (t) {
      case 'vehicles': this.memorial.deleteVehicle(item.id).subscribe({ next: ok, error: err }); break;
      case 'drivers': this.memorial.deleteDriver(item.id).subscribe({ next: ok, error: err }); break;
      case 'rooms': this.memorial.deleteRoom(item.id).subscribe({ next: ok, error: err }); break;
      case 'ovens': this.memorial.deleteOven(item.id).subscribe({ next: ok, error: err }); break;
      case 'locations': this.memorial.deleteLocation(item.id).subscribe({ next: ok, error: err }); break;
    }
  }

  vehicleTypeLabel(t: string): string {
    switch (t) {
      case 'hearse': return 'Carroza fúnebre';
      case 'family': return 'Familiar';
      case 'utility': return 'Utilitario';
      default: return 'Otro';
    }
  }

  vehicleStatusBadge(s: string): string {
    switch (s) {
      case 'active': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'maintenance': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'inactive': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  vehicleStatusLabel(s: string): string {
    switch (s) {
      case 'active': return 'Activo';
      case 'maintenance': return 'Mantenimiento';
      case 'inactive': return 'Inactivo';
      default: return s;
    }
  }

  locationKindLabel(k: string): string {
    switch (k) {
      case 'cemetery': return 'Cementerio';
      case 'church': return 'Iglesia';
      default: return 'Otro';
    }
  }

  locationKindBadge(k: string): string {
    switch (k) {
      case 'cemetery': return 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300';
      case 'church': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  private emptyForm(): any {
    switch (this.tab()) {
      case 'vehicles':
        return { code: '', plate: '', type: 'hearse', status: 'active' } as MemorialVehicleCreate;
      case 'drivers':
        return { code: '', first_name: '', is_active: true } as MemorialDriverCreate;
      case 'rooms':
        return { code: '', name: '', is_active: true } as MemorialRoomCreate;
      case 'ovens':
        return { code: '', name: '', is_active: true } as MemorialOvenCreate;
      case 'locations':
        return { code: '', name: '', kind: 'cemetery', is_active: true } as MemorialLocationCreate;
    }
  }
}
