import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface FlowStep {
  id?: string;
  kind: 'condition' | 'action';
  type: string;
  config: Record<string, unknown>;
  sort_order: number;
}
export interface Workflow {
  id: string;
  name: string;
  description: string | null;
  trigger_type: string;
  is_active: boolean;
  run_count: number;
  last_run_at: string | null;
  last_status: string | null;
  created_at: string;
}
export interface WorkflowDetail extends Workflow {
  trigger_config: Record<string, unknown>;
  steps: FlowStep[];
}
export interface ConfigField {
  key: string; label: string; type: string;
  default?: unknown; options?: string[];
}
export interface TriggerDef { type: string; label: string; icon: string; desc: string; config_fields: ConfigField[]; }
export interface ActionDef { type: string; label: string; icon: string; desc: string; config_fields: ConfigField[]; }
export interface ConditionDef { type: string; label: string; desc: string; ops: string[]; }
export interface TemplateDef {
  key: string; name: string; description: string; icon: string;
  trigger_type: string; trigger_config: Record<string, unknown>;
  steps: { kind: string; type: string; config: Record<string, unknown> }[];
}
export interface Catalog {
  triggers: TriggerDef[]; actions: ActionDef[]; conditions: ConditionDef[]; templates: TemplateDef[];
}
export interface FlowRun {
  id: string; status: string; trigger_source: string | null;
  items_matched: number; log: Record<string, unknown>[]; error: string | null;
  started_at: string; finished_at: string | null;
}
export interface FlowNotification {
  id: string; level: string; title: string; body: string | null;
  link: string | null; read_at: string | null; created_at: string;
}

@Injectable({ providedIn: 'root' })
export class FlowService {
  private readonly api = inject(ApiService);

  catalog(): Observable<Catalog> { return this.api.get<Catalog>('/automations/catalog'); }
  list(): Observable<Workflow[]> { return this.api.get<Workflow[]>('/automations'); }
  get(id: string): Observable<WorkflowDetail> { return this.api.get<WorkflowDetail>(`/automations/${id}`); }
  create(body: Partial<WorkflowDetail>): Observable<WorkflowDetail> { return this.api.post<WorkflowDetail>('/automations', body); }
  update(id: string, body: Partial<WorkflowDetail>): Observable<WorkflowDetail> { return this.api.patch<WorkflowDetail>(`/automations/${id}`, body); }
  remove(id: string): Observable<unknown> { return this.api.delete(`/automations/${id}`); }
  toggle(id: string, active: boolean): Observable<Workflow> { return this.api.post<Workflow>(`/automations/${id}/toggle?active=${active}`, {}); }
  run(id: string): Observable<FlowRun> { return this.api.post<FlowRun>(`/automations/${id}/run`, {}); }
  runs(id: string): Observable<FlowRun[]> { return this.api.get<FlowRun[]>(`/automations/${id}/runs`); }
  installTemplate(key: string): Observable<WorkflowDetail> { return this.api.post<WorkflowDetail>('/automations/install-template', { template_key: key }); }
  evaluate(): Observable<{ evaluated: number; executed: number; skipped: number }> { return this.api.post('/automations/evaluate', {}); }
  notifications(): Observable<FlowNotification[]> { return this.api.get<FlowNotification[]>('/automations/notifications'); }
  readAll(): Observable<unknown> { return this.api.post('/automations/notifications/read-all', {}); }
}
