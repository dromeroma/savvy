import { Component, inject, OnInit, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PaginationComponent } from '../../../shared/components/pagination/pagination.component';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  CommChannel,
  CommDirection,
  Lead,
  LeadCommunication,
  LeadCommunicationCreate,
  LeadCreate,
  LeadInterest,
  LeadListItem,
  LeadPriority,
  LeadSource,
  LeadStatus,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-crm',
  imports: [CommonModule, FormsModule, PaginationComponent],
  templateUrl: './crm.component.html',
})
export class MemorialCrmComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly notify = inject(NotificationService);

  loading = signal(false);
  leads = signal<LeadListItem[]>([]);

  page = signal(0);
  pageSize = signal(20);
  paginatedLeads = computed(() => {
    const s = this.page() * this.pageSize();
    return this.leads().slice(s, s + this.pageSize());
  });

  constructor() {
    effect(() => { this.leads(); this.page.set(0); }, { allowSignalWrites: true });
  }

  search = '';
  filterStatus = '';
  filterSource = '';

  // Modal form lead
  formOpen = signal(false);
  editingId = signal<string | null>(null);
  form: LeadCreate & { status?: LeadStatus; lost_reason?: string | null } = this.emptyForm();
  savingForm = signal(false);
  formError = signal('');

  // Drawer detalle
  detailOpen = signal(false);
  detail = signal<Lead | null>(null);
  comms = signal<LeadCommunication[]>([]);
  loadingDetail = signal(false);

  // Form comunicación
  commForm: LeadCommunicationCreate = this.emptyComm();
  savingComm = signal(false);
  commError = signal('');

  // Convert
  convertContractCode = '';
  convertServiceCode = '';
  marking = signal(false);
  lostReasonInput = '';

  readonly statuses: { value: LeadStatus; label: string; class: string }[] = [
    { value: 'new', label: 'Nuevo', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200' },
    { value: 'contacted', label: 'Contactado', class: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-200' },
    { value: 'qualified', label: 'Calificado', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200' },
    { value: 'proposal', label: 'Propuesta', class: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200' },
    { value: 'won', label: 'Ganado', class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' },
    { value: 'lost', label: 'Perdido', class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200' },
  ];

  readonly sources: { value: LeadSource; label: string }[] = [
    { value: 'referral', label: 'Referido' },
    { value: 'walk_in', label: 'Presencial' },
    { value: 'web', label: 'Sitio web' },
    { value: 'social', label: 'Redes sociales' },
    { value: 'whatsapp', label: 'WhatsApp' },
    { value: 'phone', label: 'Teléfono' },
    { value: 'event', label: 'Evento' },
    { value: 'other', label: 'Otro' },
  ];

  readonly interests: { value: LeadInterest; label: string }[] = [
    { value: 'exequial_plan', label: 'Plan exequial' },
    { value: 'service_immediate', label: 'Servicio inmediato' },
    { value: 'service_future', label: 'Servicio futuro' },
    { value: 'info', label: 'Solo información' },
    { value: 'other', label: 'Otro' },
  ];

  readonly priorities: { value: LeadPriority; label: string; class: string }[] = [
    { value: 'low', label: 'Baja', class: 'text-slate-500' },
    { value: 'medium', label: 'Media', class: 'text-slate-700 dark:text-slate-300' },
    { value: 'high', label: 'Alta', class: 'text-amber-600 dark:text-amber-400' },
    { value: 'urgent', label: 'Urgente', class: 'text-rose-600 dark:text-rose-400' },
  ];

  readonly channels: { value: CommChannel; label: string }[] = [
    { value: 'call', label: 'Llamada' },
    { value: 'email', label: 'Email' },
    { value: 'whatsapp', label: 'WhatsApp' },
    { value: 'visit', label: 'Visita' },
    { value: 'sms', label: 'SMS' },
    { value: 'meeting', label: 'Reunión' },
    { value: 'note', label: 'Nota interna' },
  ];

  readonly directions: { value: CommDirection; label: string }[] = [
    { value: 'inbound', label: 'Entrante' },
    { value: 'outbound', label: 'Saliente' },
    { value: 'internal', label: 'Interna' },
  ];

  funnelCounts = computed(() => {
    const counts: Record<LeadStatus, number> = {
      new: 0, contacted: 0, qualified: 0, proposal: 0, won: 0, lost: 0,
    };
    for (const l of this.leads()) counts[l.status]++;
    return counts;
  });

  ngOnInit(): void {
    this.refresh();
  }

  emptyForm(): LeadCreate & { status?: LeadStatus; lost_reason?: string | null } {
    return {
      first_name: null, last_name: null, business_name: null,
      document_type: null, document_number: null,
      email: null, phone: null, mobile: null, address: null,
      source: 'walk_in', interest: 'info', priority: 'medium',
      assigned_to: null, next_follow_up_at: null, notes: null,
    };
  }

  emptyComm(): LeadCommunicationCreate {
    return {
      channel: 'call', direction: 'outbound',
      subject: null, content: null, outcome: null,
    };
  }

  refresh(): void {
    this.loading.set(true);
    const params: Record<string, string> = {};
    if (this.search) params['search'] = this.search;
    if (this.filterStatus) params['status'] = this.filterStatus;
    if (this.filterSource) params['source'] = this.filterSource;
    this.memorial.listLeads(params).subscribe({
      next: (r) => { this.leads.set(r); this.loading.set(false); },
      error: () => { this.loading.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar los leads.' }); },
    });
  }

  // ----- Lead form

  openForm(lead?: LeadListItem): void {
    this.formError.set('');
    if (lead) {
      this.editingId.set(lead.id);
      this.memorial.getLead(lead.id).subscribe((full) => {
        this.form = {
          first_name: full.first_name, last_name: full.last_name, business_name: full.business_name,
          document_type: full.document_type, document_number: full.document_number,
          email: full.email, phone: full.phone, mobile: full.mobile, address: full.address,
          source: full.source, interest: full.interest, priority: full.priority,
          assigned_to: full.assigned_to,
          next_follow_up_at: full.next_follow_up_at ? full.next_follow_up_at.slice(0, 16) : null,
          notes: full.notes, status: full.status, lost_reason: full.lost_reason,
        };
        this.formOpen.set(true);
      });
    } else {
      this.editingId.set(null);
      this.form = this.emptyForm();
      this.formOpen.set(true);
    }
  }

  closeForm(): void { this.formOpen.set(false); }

  saveForm(): void {
    if (!this.form.first_name && !this.form.last_name && !this.form.business_name) {
      this.formError.set('Indique al menos un nombre (persona o empresa).');
      return;
    }
    this.savingForm.set(true);
    const payload = { ...this.form };
    if (payload.next_follow_up_at) {
      payload.next_follow_up_at = new Date(payload.next_follow_up_at).toISOString();
    }
    const id = this.editingId();
    const obs = id
      ? this.memorial.updateLead(id, payload)
      : this.memorial.createLead(payload);
    obs.subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: id ? 'Actualizado' : 'Creado', message: 'Lead guardado.' });
        this.savingForm.set(false);
        this.formOpen.set(false);
        this.refresh();
      },
      error: (err) => {
        this.savingForm.set(false);
        this.formError.set(err?.error?.detail || 'No se pudo guardar.');
      },
    });
  }

  removeLead(lead: LeadListItem): void {
    if (!confirm(`¿Eliminar lead ${lead.code}?`)) return;
    this.memorial.deleteLead(lead.id).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Eliminado', message: lead.code }); this.refresh(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }

  // ----- Detalle / comunicaciones

  openDetail(lead: LeadListItem): void {
    this.detailOpen.set(true);
    this.loadingDetail.set(true);
    this.comms.set([]);
    this.commForm = this.emptyComm();
    this.commError.set('');
    this.convertContractCode = '';
    this.convertServiceCode = '';
    this.lostReasonInput = '';
    this.memorial.getLead(lead.id).subscribe({
      next: (full) => {
        this.detail.set(full);
        this.memorial.listLeadCommunications(full.id).subscribe({
          next: (cs) => { this.comms.set(cs); this.loadingDetail.set(false); },
          error: () => this.loadingDetail.set(false),
        });
      },
      error: () => this.loadingDetail.set(false),
    });
  }

  closeDetail(): void {
    this.detailOpen.set(false);
    this.detail.set(null);
  }

  addComm(): void {
    const d = this.detail();
    if (!d) return;
    if (!this.commForm.channel) {
      this.commError.set('Seleccione un canal.');
      return;
    }
    this.savingComm.set(true);
    this.memorial.createLeadCommunication(d.id, this.commForm).subscribe({
      next: (c) => {
        this.comms.set([c, ...this.comms()]);
        this.commForm = this.emptyComm();
        this.savingComm.set(false);
        this.notify.show({ type: 'success', title: 'Registrada', message: 'Comunicación registrada.' });
      },
      error: (err) => {
        this.savingComm.set(false);
        this.commError.set(err?.error?.detail || 'No se pudo registrar.');
      },
    });
  }

  removeComm(c: LeadCommunication): void {
    if (!confirm('¿Eliminar esta comunicación?')) return;
    this.memorial.deleteLeadCommunication(c.id).subscribe({
      next: () => {
        this.comms.set(this.comms().filter((x) => x.id !== c.id));
        this.notify.show({ type: 'success', title: 'Eliminada', message: 'Comunicación eliminada.' });
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo eliminar.' }),
    });
  }

  changeStatus(status: LeadStatus): void {
    const d = this.detail();
    if (!d) return;
    this.memorial.updateLead(d.id, { status }).subscribe({
      next: (full) => {
        this.detail.set(full);
        this.notify.show({ type: 'success', title: 'Actualizado', message: 'Estado del lead actualizado.' });
        this.refresh();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo actualizar.' }),
    });
  }

  markLost(): void {
    const d = this.detail();
    if (!d) return;
    if (!this.lostReasonInput.trim()) {
      this.commError.set('Indique el motivo de pérdida.');
      return;
    }
    this.marking.set(true);
    this.memorial.markLeadLost(d.id, this.lostReasonInput.trim()).subscribe({
      next: (full) => {
        this.detail.set(full);
        this.marking.set(false);
        this.notify.show({ type: 'success', title: 'Marcado', message: 'Lead marcado como perdido.' });
        this.refresh();
      },
      error: () => { this.marking.set(false); this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo marcar.' }); },
    });
  }

  statusLabel(s: LeadStatus): string {
    return this.statuses.find((x) => x.value === s)?.label || s;
  }
  statusClass(s: LeadStatus): string {
    return this.statuses.find((x) => x.value === s)?.class || '';
  }
  sourceLabel(s: LeadSource): string {
    return this.sources.find((x) => x.value === s)?.label || s;
  }
  interestLabel(i: LeadInterest): string {
    return this.interests.find((x) => x.value === i)?.label || i;
  }
  priorityClass(p: LeadPriority): string {
    return this.priorities.find((x) => x.value === p)?.class || '';
  }
  channelLabel(c: CommChannel): string {
    return this.channels.find((x) => x.value === c)?.label || c;
  }
  directionLabel(d: CommDirection): string {
    return this.directions.find((x) => x.value === d)?.label || d;
  }

  leadName(l: LeadListItem | Lead): string {
    if (l.business_name) return l.business_name;
    return [l.first_name, l.last_name].filter(Boolean).join(' ').trim() || '—';
  }
}
