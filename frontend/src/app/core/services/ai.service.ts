import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface AiExtractionField {
  key: string;
  label: string;
  value: unknown;
  confidence: number | null;
  editable: boolean;
}

export interface ConfirmableAction {
  extraction_id: string;
  title: string;
  target_app: string | null;
  document_type: string;
  summary: string;
  confidence: number | null;
  fields: AiExtractionField[];
  line_items: Record<string, unknown>[];
  status: 'pending_review' | 'confirmed' | 'discarded';
  actions: string[];
  result_summary?: string | null;
  result?: Record<string, unknown> | null;
}

export interface AiUsageRow { key: string; label: string; calls: number; tokens: number; cost_usd: string; }
export interface OrgUsageReport {
  organization_id: string;
  summary: { total_cost_usd: string; total_tokens: number; total_calls: number; quota: number; tokens_used_this_period: number; };
  by_app: AiUsageRow[];
  by_action: AiUsageRow[];
  by_user: AiUsageRow[];
  by_prompt: AiUsageRow[];
}

@Injectable({ providedIn: 'root' })
export class AiService {
  private readonly api = inject(ApiService);

  /** Sube un documento (factura, cédula…) y obtiene la acción confirmable. */
  scan(file: File, opts: { prompt_key?: string; target_app?: string; document_type?: string } = {}): Observable<ConfirmableAction> {
    const fd = new FormData();
    fd.append('file', file);
    if (opts.prompt_key) fd.append('prompt_key', opts.prompt_key);
    if (opts.target_app) fd.append('target_app', opts.target_app);
    if (opts.document_type) fd.append('document_type', opts.document_type);
    return this.api.post<ConfirmableAction>('/ai/scan', fd);
  }

  getExtraction(id: string): Observable<ConfirmableAction> {
    return this.api.get<ConfirmableAction>(`/ai/extractions/${id}`);
  }
  confirm(id: string, editedData?: Record<string, unknown>): Observable<ConfirmableAction> {
    return this.api.post<ConfirmableAction>(`/ai/extractions/${id}/confirm`, { edited_data: editedData ?? null });
  }
  discard(id: string): Observable<{ status: string }> {
    return this.api.post<{ status: string }>(`/ai/extractions/${id}/discard`, {});
  }
  usage(): Observable<OrgUsageReport> {
    return this.api.get<OrgUsageReport>('/ai/usage');
  }
}
