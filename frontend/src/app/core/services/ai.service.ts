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

  // ===== Fase 2: búsqueda universal + copilot + briefing =====
  search(q: string): Observable<UniversalSearchResponse> {
    return this.api.get<UniversalSearchResponse>('/ai/search', { q });
  }
  copilot(message: string): Observable<CopilotResponse> {
    return this.api.post<CopilotResponse>('/ai/copilot', { message });
  }
  briefing(): Observable<BriefingResponse> {
    return this.api.get<BriefingResponse>('/ai/briefing');
  }

  // ===== Fase 3: insights =====
  insightsSummary(): Observable<{ cards: InsightCard[] }> {
    return this.api.get<{ cards: InsightCard[] }>('/ai/insights/summary');
  }
  insightsPos(): Observable<PosInsights> {
    return this.api.get<PosInsights>('/ai/insights/pos');
  }
  insightsMemorial(): Observable<MemorialRisk> {
    return this.api.get<MemorialRisk>('/ai/insights/memorial');
  }
}

export interface InsightCard { icon: string; tone: string; title: string; detail: string; link: string; }
export interface ReorderItem { product: string; sku: string; current_stock: number; per_day: number; days_left: number; suggested_qty: number; est_cost: number; urgency: string; }
export interface StaleItem { product: string; sku: string; current_stock: number; tied_capital: number; }
export interface PromoItem { anchor: string; anchor_sold: number; promote: string; promote_stock: number; idea: string; }
export interface PosInsights {
  reorder: ReorderItem[]; stale: StaleItem[]; promos: PromoItem[];
  reorder_count: number; stale_count: number; count: number;
}
export interface RiskItem {
  contract_id: string; code: string; name: string; phone: string | null;
  contract_status: string; overdue_count: number; overdue_amount: number;
  pending_amount: number; days_late: number; risk_tier: 'alto' | 'medio' | 'bajo'; action: string;
}
export interface MemorialRisk {
  at_risk: RiskItem[]; total_at_risk: number; total_overdue_amount: number;
  by_tier: { alto: number; medio: number; bajo: number };
}

export interface GraphHit {
  module: string;
  entity_type: string;
  entity_id: string;
  display_name: string;
  document_number: string | null;
  subtitle: string | null;
  route: string | null;
}
export interface PersonNode {
  display_name: string;
  document_number: string | null;
  hits: GraphHit[];
}
export interface UniversalSearchResponse {
  query: string;
  hits: GraphHit[];
  people: PersonNode[];
}
export interface CopilotResponse {
  answer: string;
  tools_used: string[];
}
export interface BriefingResponse {
  narrative: string[];
  metrics: Record<string, number>;
  generated_by: 'ai' | 'template';
}
