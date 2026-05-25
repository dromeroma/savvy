import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { WaterService } from '../../../core/services/water.service';
import {
  ImportCommitResponse,
  ImportCommitRow,
  ImportPreviewResponse,
  ImportRowPreview,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

type Tab = 'subscribers' | 'meters';

@Component({
  selector: 'app-water-imports',
  imports: [CommonModule],
  templateUrl: './imports.component.html',
})
export class WaterImportsComponent {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  tab = signal<Tab>('subscribers');
  selectedFile = signal<File | null>(null);
  preview = signal<ImportPreviewResponse | null>(null);
  uploading = signal(false);
  committing = signal(false);
  showErrorsOnly = signal(false);

  canCommit = computed(() => {
    const p = this.preview();
    return !!p && p.total_valid > 0 && p.total_errors === 0;
  });

  visibleRows = computed<ImportRowPreview[]>(() => {
    const p = this.preview();
    if (!p) return [];
    if (this.showErrorsOnly()) {
      return p.rows.filter(r => r.action === 'error');
    }
    return p.rows;
  });

  setTab(t: Tab): void {
    if (this.tab() === t) return;
    this.tab.set(t);
    this.reset();
  }

  reset(): void {
    this.selectedFile.set(null);
    this.preview.set(null);
    this.showErrorsOnly.set(false);
    // also clear the file input
    const input = document.getElementById('csv-file-input') as HTMLInputElement | null;
    if (input) input.value = '';
  }

  onFileSelected(ev: Event): void {
    const input = ev.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      this.notify.show({
        type: 'error', title: 'Archivo inválido',
        message: 'El archivo debe ser un CSV (.csv).',
      });
      return;
    }
    this.selectedFile.set(file);
    this.preview.set(null);
    this.runPreview();
  }

  onDrop(ev: DragEvent): void {
    ev.preventDefault();
    const file = ev.dataTransfer?.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      this.notify.show({
        type: 'error', title: 'Archivo inválido',
        message: 'El archivo debe ser un CSV (.csv).',
      });
      return;
    }
    this.selectedFile.set(file);
    this.preview.set(null);
    this.runPreview();
  }

  onDragOver(ev: DragEvent): void {
    ev.preventDefault();
  }

  runPreview(): void {
    const file = this.selectedFile();
    if (!file) return;
    this.uploading.set(true);
    const obs: Observable<ImportPreviewResponse> = this.tab() === 'subscribers'
      ? this.water.previewSubscribersImport(file)
      : this.water.previewMetersImport(file);
    obs.subscribe({
      next: (resp) => {
        this.uploading.set(false);
        this.preview.set(resp);
      },
      error: (err) => {
        this.uploading.set(false);
        this.notify.show({
          type: 'error', title: 'Error al procesar',
          message: err?.error?.detail || 'No se pudo procesar el archivo CSV.',
        });
      },
    });
  }

  commit(): void {
    const p = this.preview();
    if (!p || p.total_errors > 0) return;
    const rows: ImportCommitRow[] = p.rows
      .filter(r => r.action !== 'error')
      .map(r => ({
        row_number: r.row_number,
        action: r.action as 'create' | 'update',
        data: r.data,
        existing_id: r.existing_id,
      }));
    if (rows.length === 0) return;
    if (!confirm(
      `Se van a crear ${p.total_create} y actualizar ${p.total_update} ${this.tab() === 'subscribers' ? 'suscriptores' : 'medidores'}. ¿Confirmar?`,
    )) return;

    this.committing.set(true);
    const obs: Observable<ImportCommitResponse> = this.tab() === 'subscribers'
      ? this.water.commitSubscribersImport(rows)
      : this.water.commitMetersImport(rows);
    obs.subscribe({
      next: (resp) => {
        this.committing.set(false);
        if (resp.failed > 0) {
          this.notify.show({
            type: 'error', title: 'Importación falló',
            message: `${resp.failed} filas fallaron al guardar. Se hizo rollback completo.`,
          });
          return;
        }
        this.notify.show({
          type: 'success', title: 'Importación completada',
          message: `${resp.created} creados, ${resp.updated} actualizados.`,
        });
        this.reset();
      },
      error: (err) => {
        this.committing.set(false);
        this.notify.show({
          type: 'error', title: 'Error al guardar',
          message: err?.error?.detail || 'No se pudo guardar la importación.',
        });
      },
    });
  }

  downloadTemplate(): void {
    const obs = this.tab() === 'subscribers'
      ? this.water.downloadSubscribersTemplate()
      : this.water.downloadMetersTemplate();
    obs.subscribe({
      next: ({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || (this.tab() === 'subscribers'
          ? 'suscriptores-plantilla.csv' : 'medidores-plantilla.csv');
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      },
      error: () => this.notify.show({
        type: 'error', title: 'Error', message: 'No se pudo descargar la plantilla.',
      }),
    });
  }

  // Pretty-print a few key columns from each row for the preview table
  displayKey(row: ImportRowPreview): string {
    const d = row.data;
    if (this.tab() === 'subscribers') {
      return (d['code'] as string) || '—';
    }
    return (d['serial_number'] as string) || '—';
  }

  displaySecondary(row: ImportRowPreview): string {
    const d = row.data;
    if (this.tab() === 'subscribers') {
      const parts = [
        d['first_name'] as string | undefined,
        d['last_name'] as string | undefined,
      ].filter(Boolean);
      const name = parts.join(' ').trim();
      return (d['business_name'] as string) || name || '—';
    }
    return (d['brand'] as string) || '—';
  }

  actionBadgeClass(action: string): string {
    switch (action) {
      case 'create': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'update': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      case 'error': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  actionLabel(action: string): string {
    switch (action) {
      case 'create': return 'Crear';
      case 'update': return 'Actualizar';
      case 'error': return 'Error';
      default: return action;
    }
  }
}
