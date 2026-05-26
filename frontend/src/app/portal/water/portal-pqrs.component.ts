import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalService } from '../../core/services/portal.service';
import {
  PortalPqrsDetail,
  PortalPqrsListItem,
  PqrsCreate,
  PqrsType,
} from '../../core/models/portal.model';
import { NotificationService } from '../../shared/services/notification.service';
import { WhatsappShareButtonComponent } from '../../shared/components/whatsapp-share-button/whatsapp-share-button.component';

@Component({
  selector: 'app-portal-pqrs',
  imports: [CommonModule, FormsModule, WhatsappShareButtonComponent],
  template: `
    <div>
      <div class="flex items-start justify-between gap-3 mb-5">
        <div>
          <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Mis PQRS</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Peticiones, quejas, reclamos y sugerencias.</p>
        </div>
        <button (click)="openCreate()"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white text-sm font-medium">
          + Nueva PQRS
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-sky-200 border-t-sky-600"></div>
        </div>
      } @else if (items().length === 0) {
        <div class="rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-10 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No has enviado ninguna PQRS todavía.</p>
        </div>
      } @else {
        <div class="space-y-2">
          @for (p of items(); track p.id) {
            <button (click)="openDetail(p)"
              class="w-full text-left rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:border-sky-400 transition">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-mono text-xs text-gray-400">{{ p.code }}</span>
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize" [ngClass]="typeBadge(p.type)">{{ p.type }}</span>
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" [ngClass]="statusBadge(p.status)">{{ statusLabel(p.status) }}</span>
                  </div>
                  <div class="text-sm text-gray-800 dark:text-white/90 mt-1 truncate font-medium">{{ p.subject }}</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    Enviada: {{ p.created_at | date:'short' }}
                    @if (p.responded_at) {
                      · Respondida: {{ p.responded_at | date:'short' }}
                    }
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </div>
            </button>
          }
        </div>
      }

      <!-- Create modal -->
      @if (createOpen()) {
        <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 p-2 sm:p-4" (click)="closeCreate()">
          <div class="bg-white dark:bg-gray-800 rounded-t-xl sm:rounded-xl shadow-xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90 mb-1">Nueva PQRS</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-5">El acueducto te responderá lo antes posible.</p>

            @if (createError()) {
              <div class="mb-3 p-3 bg-error-50 border border-error-200 text-error-700 dark:bg-error-500/10 dark:border-error-500/30 dark:text-error-400 rounded text-sm">
                {{ createError() }}
              </div>
            }

            <div class="space-y-3">
              <div>
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo *</label>
                <select [(ngModel)]="form.type"
                  class="w-full h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="peticion">Petición</option>
                  <option value="queja">Queja</option>
                  <option value="reclamo">Reclamo</option>
                  <option value="sugerencia">Sugerencia</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Asunto *</label>
                <input [(ngModel)]="form.subject" maxlength="255"
                  class="w-full h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción *</label>
                <textarea [(ngModel)]="form.description" rows="5" placeholder="Describe lo más claro posible…"
                  class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea>
              </div>
            </div>

            <div class="flex gap-2 mt-5">
              <button (click)="closeCreate()" [disabled]="saving()"
                class="flex-1 px-4 py-3 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700">
                Cancelar
              </button>
              <button (click)="submit()" [disabled]="saving()"
                class="flex-1 px-4 py-3 rounded-lg text-sm font-semibold text-white bg-sky-500 hover:bg-sky-600 disabled:bg-sky-300">
                {{ saving() ? 'Enviando…' : 'Enviar' }}
              </button>
            </div>
          </div>
        </div>
      }

      <!-- Detail modal -->
      @if (detail()) {
        @let d = detail()!;
        <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 p-2 sm:p-4" (click)="closeDetail()">
          <div class="bg-white dark:bg-gray-800 rounded-t-xl sm:rounded-xl shadow-xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto" (click)="$event.stopPropagation()">
            <div class="flex items-center justify-between mb-4">
              <div>
                <div class="font-mono text-xs text-gray-400">{{ d.code }}</div>
                <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">{{ d.subject }}</h3>
              </div>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" [ngClass]="statusBadge(d.status)">{{ statusLabel(d.status) }}</span>
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Tipo: <span class="capitalize">{{ d.type }}</span> · Enviada: {{ d.created_at | date:'short' }}
            </div>
            <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-3 text-sm text-gray-700 dark:text-gray-300 mb-4 whitespace-pre-line">
              {{ d.description }}
            </div>

            <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2">Respuesta del acueducto</h4>
            @if (d.response) {
              <div class="rounded-lg border border-emerald-200 dark:border-emerald-700/40 bg-emerald-50/40 dark:bg-emerald-500/5 p-3 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">
                {{ d.response }}
              </div>
              <div class="text-xs text-gray-400 mt-1">Respondida: {{ d.responded_at | date:'short' }}</div>
            } @else {
              <div class="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 p-3 text-sm text-gray-500 dark:text-gray-400 italic">
                Aún sin respuesta. Te avisaremos cuando el acueducto responda.
              </div>
            }

            <div class="flex justify-end items-center gap-2 mt-5">
              <app-whatsapp-share [text]="whatsappTextFor(d)" label="Compartir" />
              <button (click)="closeDetail()" class="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700">
                Cerrar
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class PortalPqrsComponent implements OnInit {
  private readonly portal = inject(PortalService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  items = signal<PortalPqrsListItem[]>([]);

  createOpen = signal(false);
  saving = signal(false);
  createError = signal('');
  form: PqrsCreate = this.empty();

  detail = signal<PortalPqrsDetail | null>(null);

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.portal.myPqrs().subscribe({
      next: (data) => { this.items.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  openCreate(): void {
    this.form = this.empty();
    this.createError.set('');
    this.createOpen.set(true);
  }
  closeCreate(): void { this.createOpen.set(false); }

  submit(): void {
    if (!this.form.subject || this.form.subject.length < 3) {
      this.createError.set('El asunto debe tener al menos 3 caracteres.');
      return;
    }
    if (!this.form.description || this.form.description.length < 10) {
      this.createError.set('La descripción debe tener al menos 10 caracteres.');
      return;
    }
    this.saving.set(true);
    this.createError.set('');
    this.portal.createMyPqrs(this.form).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeCreate();
        this.notify.show({ type: 'success', title: 'PQRS enviada', message: 'Te avisaremos cuando el acueducto responda.' });
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.createError.set(err?.error?.detail || 'Error al enviar.');
      },
    });
  }

  openDetail(p: PortalPqrsListItem): void {
    this.portal.getMyPqrs(p.id).subscribe({
      next: (d) => this.detail.set(d),
    });
  }
  closeDetail(): void { this.detail.set(null); }

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

  private empty(): PqrsCreate {
    return { type: 'peticion', subject: '', description: '' };
  }

  whatsappTextFor(d: PortalPqrsDetail): string {
    const lines = [
      `PQRS ${d.code} · ${d.type.toUpperCase()}`,
      `Asunto: ${d.subject}`,
      `Estado: ${this.statusLabel(d.status)}`,
      '',
      d.description,
    ];
    if (d.response) {
      lines.push('', '— Respuesta del acueducto:', d.response);
    }
    return lines.join('\n');
  }
}
