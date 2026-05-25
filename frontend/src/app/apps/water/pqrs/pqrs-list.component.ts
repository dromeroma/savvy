import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalService } from '../../../core/services/portal.service';
import {
  AdminPqrsListItem,
  PortalPqrsDetail,
  PqrsStatus,
  PqrsType,
} from '../../../core/models/portal.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-pqrs-list',
  imports: [CommonModule, FormsModule],
  templateUrl: './pqrs-list.component.html',
})
export class PqrsListComponent implements OnInit {
  private readonly portal = inject(PortalService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  items = signal<AdminPqrsListItem[]>([]);

  filterStatus = '';
  filterType = '';

  // Detail / respond
  detail = signal<PortalPqrsDetail | null>(null);
  responseText = '';
  responseStatus: PqrsStatus = 'resolved';
  saving = signal(false);
  detailError = signal('');

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.portal.adminListPqrs({
      status: this.filterStatus || undefined,
      type: this.filterType || undefined,
    }).subscribe({
      next: (data) => { this.items.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openDetail(p: AdminPqrsListItem): void {
    this.portal.adminGetPqrs(p.id).subscribe({
      next: (d) => {
        this.detail.set(d);
        this.responseText = d.response ?? '';
        this.responseStatus = d.status === 'closed' ? 'closed' : 'resolved';
        this.detailError.set('');
      },
    });
  }
  closeDetail(): void { this.detail.set(null); }

  respond(): void {
    const d = this.detail();
    if (!d) return;
    if (!this.responseText.trim()) {
      this.detailError.set('Escribe una respuesta.');
      return;
    }
    this.saving.set(true);
    this.detailError.set('');
    this.portal.adminRespondPqrs(d.id, this.responseText, this.responseStatus).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeDetail();
        this.notify.show({ type: 'success', title: 'Respondida', message: 'PQRS respondida.' });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.detailError.set(err?.error?.detail || 'Error al responder.');
      },
    });
  }

  typeBadge(t: PqrsType): string {
    switch (t) {
      case 'peticion': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'queja': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'reclamo': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'sugerencia': return 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300';
    }
  }

  statusBadge(s: string): string {
    switch (s) {
      case 'open': return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
      case 'in_progress': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'resolved': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'closed': return 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  statusLabel(s: string): string {
    switch (s) {
      case 'open': return 'Abierta';
      case 'in_progress': return 'En revisión';
      case 'resolved': return 'Resuelta';
      case 'closed': return 'Cerrada';
      default: return s;
    }
  }
}
