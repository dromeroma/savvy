import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-edu-documents',
  imports: [CommonModule, FormsModule],
  template: `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">Documentos</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Plantillas de certificados, boletines y paz y salvo</p>
        </div>
        <button (click)="showModal = true"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
          + Nueva Plantilla
        </button>
      </div>

      <div class="grid gap-4">
        @for (tpl of templates(); track tpl.id) {
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 flex justify-between items-center">
            <div>
              <h4 class="font-semibold text-gray-800 dark:text-white/90">{{ tpl.name }}</h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">Tipo: {{ typeLabel(tpl.type) }}</p>
            </div>
            <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
              {{ typeLabel(tpl.type) }}
            </span>
          </div>
        }
        @if (templates().length === 0) {
          <p class="text-sm text-gray-400 text-center py-8">No hay plantillas configuradas</p>
        }
      </div>

      <!-- Issued Documents -->
      @if (issued().length > 0) {
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mt-8 mb-3">Documentos Emitidos</h3>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Plantilla</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Estudiante</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Fecha</th>
                </tr>
              </thead>
              <tbody>
                @for (doc of issued(); track doc.id) {
                  <tr class="border-b border-gray-100 dark:border-gray-700/50">
                    <td class="px-4 py-3 text-gray-800 dark:text-white/90">{{ getTemplateName(doc.template_id) }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ doc.student_id }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ doc.issued_at | date:'short' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      }

      @if (showModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Plantilla</h3>
            <div class="space-y-3">
              <input [(ngModel)]="form.name" placeholder="Nombre" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
              <select [(ngModel)]="form.type" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                <option value="certificate">Certificado</option>
                <option value="transcript">Historial Académico</option>
                <option value="report_card">Boletín</option>
                <option value="paz_y_salvo">Paz y Salvo</option>
              </select>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="save()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class EduDocumentsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  templates = signal<any[]>([]);
  issued = signal<any[]>([]);
  showModal = false;
  form: any = { name: '', type: 'certificate' };

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.api.get<any[]>('/edu/documents/templates').subscribe({ next: (r) => this.templates.set(r) });
    this.api.get<any[]>('/edu/documents/issued').subscribe({ next: (r) => this.issued.set(r) });
  }

  save(): void {
    this.api.post('/edu/documents/templates', this.form).subscribe({
      next: () => { this.showModal = false; this.form = { name: '', type: 'certificate' }; this.notify.show({ type: 'success', title: 'Listo', message: 'Plantilla creada' }); this.load(); },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }

  typeLabel(t: string): string {
    return { certificate: 'Certificado', transcript: 'Historial', report_card: 'Boletín', paz_y_salvo: 'Paz y Salvo' }[t] || t;
  }

  getTemplateName(id: string): string {
    return this.templates().find((t) => t.id === id)?.name || id;
  }
}
