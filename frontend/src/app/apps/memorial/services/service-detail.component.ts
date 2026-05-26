import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MemorialApiService } from '../../../core/services/memorial.service';
import {
  CoverageLookupResult,
  MemorialFamilyMemberCreate,
  MemorialService,
  MemorialServiceEvent,
  MemorialServiceStatus,
} from '../../../core/models/memorial.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-memorial-service-detail',
  imports: [CommonModule, FormsModule, RouterLink, DatePipe],
  templateUrl: './service-detail.component.html',
})
export class MemorialServiceDetailComponent implements OnInit {
  private readonly memorial = inject(MemorialApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  service = signal<MemorialService | null>(null);
  events = signal<MemorialServiceEvent[]>([]);

  // Notas
  newNote = '';
  postingNote = signal(false);

  // Familia
  addingFamily = signal(false);
  familyForm: MemorialFamilyMemberCreate = this.emptyFamily();
  savingFamily = signal(false);

  // Edición rápida de campos de ejecución
  editingExecution = signal(false);
  savingExecution = signal(false);

  // Transición de estado
  transitioning = signal(false);

  // Cobertura exequial
  lookupOpen = signal(false);
  lookupResults = signal<CoverageLookupResult[]>([]);
  lookupLoading = signal(false);
  lookupError = signal('');

  // Estados permitidos según estado actual
  allowedTransitions = computed<MemorialServiceStatus[]>(() => {
    const s = this.service()?.status;
    switch (s) {
      case 'iniciado': return ['en_proceso', 'pendiente', 'cancelado'];
      case 'en_proceso': return ['pendiente', 'finalizado', 'cancelado'];
      case 'pendiente': return ['en_proceso', 'finalizado', 'cancelado'];
      default: return [];
    }
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading.set(true);
    this.memorial.getService(id).subscribe({
      next: (svc) => {
        this.service.set(svc);
        this.loading.set(false);
        this.loadEvents(id);
      },
      error: () => {
        this.loading.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: 'No se pudo cargar el servicio.',
        });
      },
    });
  }

  private loadEvents(id: string): void {
    this.memorial.listEvents(id).subscribe({
      next: (e) => this.events.set(e),
    });
  }

  // ---------------- Notes
  addNote(): void {
    const s = this.service();
    if (!s || !this.newNote.trim()) return;
    this.postingNote.set(true);
    this.memorial.addNote(s.id, this.newNote.trim()).subscribe({
      next: () => {
        this.postingNote.set(false);
        this.newNote = '';
        this.loadEvents(s.id);
      },
      error: () => {
        this.postingNote.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo agregar la nota.' });
      },
    });
  }

  // ---------------- Status transition
  transition(newStatus: MemorialServiceStatus): void {
    const s = this.service();
    if (!s) return;
    const label = this.statusLabel(newStatus);
    if (!confirm(`¿Cambiar el estado del servicio a "${label}"?`)) return;
    this.transitioning.set(true);
    this.memorial.transitionStatus(s.id, newStatus).subscribe({
      next: (svc) => {
        this.service.set(svc);
        this.transitioning.set(false);
        this.notify.show({ type: 'success', title: 'Estado actualizado', message: label });
        this.loadEvents(s.id);
      },
      error: (err) => {
        this.transitioning.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo cambiar el estado.',
        });
      },
    });
  }

  // ---------------- Family
  openAddFamily(): void {
    this.familyForm = this.emptyFamily();
    this.addingFamily.set(true);
  }
  closeAddFamily(): void { this.addingFamily.set(false); }

  saveFamily(): void {
    const s = this.service();
    if (!s || !this.familyForm.first_name.trim()) return;
    this.savingFamily.set(true);
    this.memorial.addFamilyMember(s.id, this.familyForm).subscribe({
      next: () => {
        this.savingFamily.set(false);
        this.closeAddFamily();
        this.load(s.id);
      },
      error: (err) => {
        this.savingFamily.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo agregar el familiar.',
        });
      },
    });
  }

  removeFamily(memberId: string): void {
    const s = this.service();
    if (!s) return;
    if (!confirm('¿Eliminar este familiar del servicio?')) return;
    this.memorial.removeFamilyMember(s.id, memberId).subscribe({
      next: () => this.load(s.id),
      error: () => this.notify.show({
        type: 'error', title: 'Error', message: 'No se pudo eliminar.',
      }),
    });
  }

  // ---------------- Execution editing
  toggleExecutionEdit(): void {
    this.editingExecution.set(!this.editingExecution());
  }

  saveExecution(): void {
    const s = this.service();
    if (!s) return;
    this.savingExecution.set(true);
    const payload = {
      velation_start_at: s.velation_start_at,
      velation_end_at: s.velation_end_at,
      velation_location: s.velation_location,
      cremation_at: s.cremation_at,
      cremation_location: s.cremation_location,
      burial_at: s.burial_at,
      burial_cemetery: s.burial_cemetery,
      burial_section: s.burial_section,
      mass_at: s.mass_at,
      mass_church: s.mass_church,
      final_total: s.final_total,
      notes: s.notes,
    };
    this.memorial.updateService(s.id, payload as any).subscribe({
      next: (svc) => {
        this.service.set(svc);
        this.savingExecution.set(false);
        this.editingExecution.set(false);
        this.notify.show({ type: 'success', title: 'Guardado', message: 'Ejecución actualizada.' });
        this.loadEvents(s.id);
      },
      error: (err) => {
        this.savingExecution.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo guardar.',
        });
      },
    });
  }

  // ---------------- Labels
  badge(s: string): string {
    switch (s) {
      case 'iniciado': return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300';
      case 'en_proceso': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'pendiente': return 'bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300';
      case 'finalizado': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'cancelado': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400';
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
    switch (t) {
      case 'velacion': return 'Velación';
      case 'cremacion': return 'Cremación';
      case 'entierro': return 'Entierro';
      case 'velacion_cremacion': return 'Velación + Cremación';
      case 'velacion_entierro': return 'Velación + Entierro';
      case 'velacion_cremacion_entierro': return 'Velación + Cremación + Entierro';
      default: return t;
    }
  }

  eventLabel(t: string): string {
    switch (t) {
      case 'created': return 'Servicio creado';
      case 'updated': return 'Datos actualizados';
      case 'status_changed': return 'Cambio de estado';
      case 'note': return 'Nota';
      case 'family_added': return 'Familiar añadido';
      case 'family_removed': return 'Familiar eliminado';
      case 'contract_linked': return 'Contrato exequial vinculado';
      case 'contract_unlinked': return 'Contrato exequial desvinculado';
      default: return t;
    }
  }

  private emptyFamily(): MemorialFamilyMemberCreate {
    return {
      first_name: '',
      last_name: '',
      relationship: '',
      mobile: '',
      phone: '',
      email: '',
      is_primary: false,
    };
  }

  // -------- Coverage lookup --------
  openLookup(): void {
    this.lookupResults.set([]);
    this.lookupError.set('');
    this.lookupOpen.set(true);
    const s = this.service();
    if (s?.deceased_document_number) {
      this.runLookup(s.deceased_document_number);
    }
  }

  closeLookup(): void { this.lookupOpen.set(false); }

  runLookup(doc: string): void {
    if (!doc?.trim()) {
      this.lookupError.set('Ingresa el documento del fallecido.');
      this.lookupResults.set([]);
      return;
    }
    this.lookupLoading.set(true);
    this.lookupError.set('');
    this.memorial.coverageLookup(doc.trim()).subscribe({
      next: (results) => {
        this.lookupResults.set(results);
        this.lookupLoading.set(false);
        if (results.length === 0) {
          this.lookupError.set('No se encontró cobertura activa con ese documento.');
        }
      },
      error: () => {
        this.lookupLoading.set(false);
        this.lookupError.set('Error al consultar cobertura.');
      },
    });
  }

  linkContract(contractId: string): void {
    const s = this.service();
    if (!s) return;
    this.memorial.linkContractToService(s.id, contractId).subscribe({
      next: (upd) => {
        this.service.set(upd);
        this.notify.show({
          type: 'success', title: 'Contrato vinculado',
          message: 'El servicio quedó asociado al contrato exequial.',
        });
        this.closeLookup();
        this.loadEvents(s.id);
      },
      error: (err) => this.notify.show({
        type: 'error', title: 'Error',
        message: err?.error?.detail || 'No se pudo vincular el contrato.',
      }),
    });
  }

  unlinkContract(): void {
    const s = this.service();
    if (!s) return;
    if (!confirm('¿Desvincular el contrato exequial de este servicio?')) return;
    this.memorial.linkContractToService(s.id, null).subscribe({
      next: (upd) => {
        this.service.set(upd);
        this.notify.show({ type: 'success', title: 'Desvinculado', message: 'Contrato desvinculado.' });
        this.loadEvents(s.id);
      },
    });
  }
}
