import { Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';
import { DatePickerComponent } from '../../../shared/components/form/date-picker/date-picker.component';
import { LocationSelectorComponent, LocationSelection } from '../../../shared/components/form/location-selector/location-selector.component';

interface Member {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  status: string;
  membership_date: string;
}

interface PaginatedResponse {
  items: Member[];
  total: number;
  page: number;
  page_size: number;
}

@Component({
  selector: 'app-member-list',
  imports: [FormsModule, DatePickerComponent, LocationSelectorComponent],
  templateUrl: './member-list.component.html',
})
export class MemberListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  members = signal<Member[]>([]);
  loading = signal(true);
  total = signal(0);
  page = signal(1);
  pageSize = signal(20);
  search = '';
  statusFilter = '';

  // Modal
  showModal = signal(false);
  saving = signal(false);
  editingId = signal<string | null>(null);  // null = creating, string = editing
  location: LocationSelection = { country_id: null, country_name: '', state_id: null, state_name: '', city_id: null, city_name: '' };
  form = {
    first_name: '',
    last_name: '',
    document_type: '',
    document_number: '',
    email: '',
    phone: '',
    gender: '',
    occupation: '',
    date_of_birth: '',
    membership_date: '',
    baptism_date: '',
    holy_spirit_baptism: false,
  };

  ngOnInit(): void {
    this.loadMembers();
  }

  loadMembers(): void {
    this.loading.set(true);
    const params: Record<string, string | number> = {
      page: this.page(),
      page_size: this.pageSize(),
    };
    if (this.search) params['search'] = this.search;
    if (this.statusFilter) params['status'] = this.statusFilter;

    this.api.get<PaginatedResponse>('/church/congregants', params).subscribe({
      next: (res) => {
        this.members.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  onSearch(): void {
    this.page.set(1);
    this.loadMembers();
  }

  onFilterChange(): void {
    this.page.set(1);
    this.loadMembers();
  }

  nextPage(): void {
    if (this.page() * this.pageSize() < this.total()) {
      this.page.update((p) => p + 1);
      this.loadMembers();
    }
  }

  prevPage(): void {
    if (this.page() > 1) {
      this.page.update((p) => p - 1);
      this.loadMembers();
    }
  }

  get totalPages(): number {
    return Math.ceil(this.total() / this.pageSize());
  }

  openModal(): void {
    this.editingId.set(null);
    this.form = {
      first_name: '',
      last_name: '',
      document_type: '',
      document_number: '',
      email: '',
      phone: '',
      gender: '',
      occupation: '',
      date_of_birth: '',
      membership_date: '',
      baptism_date: '',
      holy_spirit_baptism: false,
    };
    this.showModal.set(true);
  }

  openEditModal(member: Member): void {
    this.editingId.set(member.id);
    this.form = {
      first_name: member.first_name || '',
      last_name: member.last_name || '',
      document_type: (member as any).document_type || '',
      document_number: (member as any).document_number || '',
      email: member.email || '',
      phone: member.phone || '',
      gender: (member as any).gender || '',
      occupation: (member as any).occupation || '',
      date_of_birth: (member as any).date_of_birth || '',
      membership_date: (member as any).membership_date || '',
      baptism_date: (member as any).baptism_date || '',
      holy_spirit_baptism: (member as any).holy_spirit_baptism || false,
    };
    this.showModal.set(true);
  }

  closeModal(): void {
    this.showModal.set(false);
    this.editingId.set(null);
  }

  onLocationChange(loc: LocationSelection): void {
    this.location = loc;
  }

  async deleteMember(member: Member): Promise<void> {
    const confirmed = await this.confirmDialog.confirm({
      title: 'Eliminar congregante',
      message: `¿Estás seguro de que deseas eliminar a ${member.first_name} ${member.last_name}? Esta acción no se puede deshacer.`,
      type: 'danger',
      confirmText: 'Eliminar',
    });
    if (!confirmed) return;

    this.api.delete(`/church/congregants/${member.id}`).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Eliminado', message: 'Congregante eliminado correctamente' });
        this.loadMembers();
      },
      error: () => {
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar el congregante' });
      },
    });
  }

  saveMember(): void {
    this.saving.set(true);
    const body: Record<string, any> = {
      first_name: this.form.first_name,
      last_name: this.form.last_name,
    };
    if (this.form.document_type) body['document_type'] = this.form.document_type;
    if (this.form.document_number) body['document_number'] = this.form.document_number;
    if (this.form.email) body['email'] = this.form.email;
    if (this.form.phone) body['phone'] = this.form.phone;
    if (this.form.gender) body['gender'] = this.form.gender;
    if (this.form.occupation) body['occupation'] = this.form.occupation;
    if (this.location.country_name) body['country'] = this.location.country_name;
    if (this.location.state_name) body['state'] = this.location.state_name;
    if (this.location.city_name) body['city'] = this.location.city_name;
    if (this.form.date_of_birth) body['date_of_birth'] = this.form.date_of_birth;
    if (this.form.membership_date) body['membership_date'] = this.form.membership_date;
    if (this.form.baptism_date) body['baptism_date'] = this.form.baptism_date;
    body['holy_spirit_baptism'] = this.form.holy_spirit_baptism;

    const id = this.editingId();
    const request$ = id
      ? this.api.patch(`/church/congregants/${id}`, body)
      : this.api.post('/church/congregants', body);

    request$.subscribe({
      next: () => {
        this.saving.set(false);
        this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: id ? 'Congregante actualizado correctamente' : 'Congregante creado correctamente' });
        this.closeModal();
        this.loadMembers();
      },
      error: (err) => {
        this.saving.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo guardar el congregante' });
        console.error('Save error:', err);
      },
    });
  }
}
