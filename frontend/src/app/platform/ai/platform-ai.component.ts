import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import {
  HeroMetricCardComponent,
  KpiCardComponent,
  ChartCardComponent,
  BarChartComponent,
  BarRow,
  SparklineComponent,
} from '../../shared/components/bento';

interface ProviderConfig {
  id: string;
  provider: string;
  is_enabled: boolean;
  has_api_key: boolean;
  api_key_hint: string | null;
  model_haiku: string;
  model_sonnet: string;
  model_opus: string;
  default_tier: 'haiku' | 'sonnet' | 'opus';
  pricing: Record<string, unknown>;
  whatsapp_enabled: boolean;
  has_whatsapp_token: boolean;
  whatsapp_token_hint: string | null;
  whatsapp_phone_id: string | null;
  updated_at: string;
}

interface UsageRow { key: string; label: string; calls: number; tokens: number; cost_usd: string; }
interface OrgUsageRow { organization_id: string; organization_name: string; calls: number; tokens: number; cost_usd: string; }
interface PlatformUsage {
  total_cost_usd: string; total_tokens: number; total_calls: number; active_orgs: number;
  by_organization: OrgUsageRow[]; by_model: UsageRow[]; by_app: UsageRow[];
}

@Component({
  selector: 'app-platform-ai',
  imports: [
    CommonModule, FormsModule, DecimalPipe,
    HeroMetricCardComponent, KpiCardComponent, ChartCardComponent, BarChartComponent,
    SparklineComponent,
  ],
  template: `
    <div class="space-y-7">
      <header>
        <p class="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-medium">Plataforma · SavvyAI</p>
        <h1 class="text-3xl font-bold text-slate-900 dark:text-white mt-1">Inteligencia Artificial</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Configura el proveedor de IA y monitorea el consumo de todas las organizaciones.
        </p>
      </header>

      <!-- ====== Configuración del proveedor ====== -->
      <section class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6">
        <div class="flex items-start justify-between gap-3 mb-4">
          <div>
            <h2 class="text-base font-semibold text-slate-900 dark:text-white">Proveedor de IA</h2>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              La API key se guarda <strong>cifrada</strong>. Solo el super admin la administra.
            </p>
          </div>
          @if (cfg(); as c) {
            <span class="text-xs px-2.5 py-1 rounded-full font-medium"
              [class]="c.is_enabled
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
              {{ c.is_enabled ? '● Activo' : '○ Inactivo' }}
            </span>
          }
        </div>

        @if (cfg(); as c) {
          <div class="grid gap-4 md:grid-cols-2">
            <label class="block md:col-span-2">
              <span class="text-xs text-slate-600 dark:text-slate-400">API Key de Anthropic (Claude)</span>
              <div class="flex gap-2 mt-1">
                <input [(ngModel)]="apiKeyInput" type="password" autocomplete="off"
                  [placeholder]="c.has_api_key ? 'Configurada (' + (c.api_key_hint || '****') + ') — escribe una nueva para reemplazar' : 'sk-ant-...'"
                  class="flex-1 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
              </div>
              <p class="text-[11px] text-slate-400 mt-1">
                Aún no la tienes — puedes dejar todo configurado y pegarla aquí cuando la obtengas.
              </p>
            </label>

            <label class="flex items-center gap-2">
              <input type="checkbox" [(ngModel)]="c.is_enabled" class="h-4 w-4" />
              <span class="text-sm text-slate-700 dark:text-slate-300">IA habilitada en la plataforma</span>
            </label>

            <label class="block">
              <span class="text-xs text-slate-600 dark:text-slate-400">Tier por defecto</span>
              <select [(ngModel)]="c.default_tier"
                class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm">
                <option value="haiku">Haiku (barato)</option>
                <option value="sonnet">Sonnet (balance)</option>
                <option value="opus">Opus (potente)</option>
              </select>
            </label>

            <label class="block">
              <span class="text-xs text-slate-600 dark:text-slate-400">Modelo Haiku</span>
              <input [(ngModel)]="c.model_haiku" class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
            </label>
            <label class="block">
              <span class="text-xs text-slate-600 dark:text-slate-400">Modelo Sonnet</span>
              <input [(ngModel)]="c.model_sonnet" class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
            </label>
            <label class="block">
              <span class="text-xs text-slate-600 dark:text-slate-400">Modelo Opus</span>
              <input [(ngModel)]="c.model_opus" class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
            </label>
          </div>

          @if (msg()) { <p class="text-sm mt-3" [class]="msgErr() ? 'text-rose-600' : 'text-emerald-600'">{{ msg() }}</p> }

          <div class="flex flex-wrap justify-end gap-2 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <button (click)="testConnection()" [disabled]="testing() || !c.has_api_key && !apiKeyInput"
              class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm disabled:opacity-50">
              {{ testing() ? 'Probando…' : 'Probar conexión' }}
            </button>
            <button (click)="save()" [disabled]="saving()"
              class="rounded-md bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-5 py-2 text-sm font-medium">
              {{ saving() ? 'Guardando…' : 'Guardar configuración' }}
            </button>
          </div>
        }
      </section>

      <!-- ====== WhatsApp ====== -->
      @if (cfg(); as c) {
        <section class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6">
          <div class="flex items-start justify-between gap-3 mb-4">
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">💬 WhatsApp (Cloud API)</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Para que las automatizaciones de SavvyFlow envíen mensajes. Token cifrado.
              </p>
            </div>
            <span class="text-xs px-2.5 py-1 rounded-full font-medium"
              [class]="c.whatsapp_enabled ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'">
              {{ c.whatsapp_enabled ? '● Activo' : '○ Inactivo' }}
            </span>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <label class="block md:col-span-2">
              <span class="text-xs text-slate-600 dark:text-slate-400">Token de acceso (WhatsApp Cloud API)</span>
              <input [(ngModel)]="waToken" type="password" autocomplete="off"
                [placeholder]="c.has_whatsapp_token ? 'Configurado (' + (c.whatsapp_token_hint || '****') + ')' : 'EAAG...'"
                class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
            </label>
            <label class="block">
              <span class="text-xs text-slate-600 dark:text-slate-400">Phone Number ID</span>
              <input [(ngModel)]="c.whatsapp_phone_id" placeholder="123456789012345"
                class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm font-mono" />
            </label>
            <label class="flex items-center gap-2 mt-6">
              <input type="checkbox" [(ngModel)]="c.whatsapp_enabled" class="h-4 w-4" />
              <span class="text-sm text-slate-700 dark:text-slate-300">WhatsApp habilitado</span>
            </label>
          </div>
          <div class="flex flex-wrap items-end gap-2 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <label class="block flex-1 min-w-[180px]">
              <span class="text-xs text-slate-600 dark:text-slate-400">Probar envío a (número con código país)</span>
              <input [(ngModel)]="waTestTo" placeholder="573001234567"
                class="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm" />
            </label>
            <button (click)="testWhatsapp()" [disabled]="waTesting()"
              class="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm disabled:opacity-50">
              {{ waTesting() ? 'Enviando…' : 'Probar' }}
            </button>
            <button (click)="save()" [disabled]="saving()"
              class="rounded-md bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-5 py-2 text-sm font-medium">Guardar</button>
          </div>
          @if (waMsg()) { <p class="text-sm mt-2" [class]="waErr() ? 'text-rose-600' : 'text-emerald-600'">{{ waMsg() }}</p> }
        </section>
      }

      <!-- ====== Gasto diario + kill-switch ====== -->
      @if (daily(); as d) {
        <section class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6">
          <div class="flex items-start justify-between gap-3 mb-4">
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">Gasto de IA — hoy</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Kill-switch: bloquea cuando se alcanza el límite diario.</p>
            </div>
            <span class="text-xs px-2.5 py-1 rounded-full font-medium"
              [class]="d.budget.blocked
                ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300'
                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'">
              {{ d.budget.blocked ? '● Bloqueado' : '● Activo' }}
            </span>
          </div>

          <div class="flex items-end gap-3 mb-2">
            <span class="text-3xl font-bold tabular-nums text-slate-900 dark:text-white">$ {{ d.budget.spent_today_usd | number:'1.2-4' }}</span>
            <span class="text-sm text-slate-400 mb-1">/ $ {{ d.budget.daily_limit_usd | number:'1.2-2' }} límite global</span>
          </div>
          <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
            <div class="h-full rounded-full transition-all"
              [style.width.%]="min(d.budget.pct_used, 100)"
              [class]="d.budget.pct_used >= 90 ? 'bg-rose-500' : d.budget.pct_used >= 70 ? 'bg-amber-500' : 'bg-emerald-500'"></div>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">{{ d.budget.pct_used }}% usado hoy</p>

          @if (d.series.length >= 2) {
            <div class="mt-4">
              <div class="text-[11px] uppercase tracking-wider text-slate-400 mb-1">Costo por día (últimos {{ d.series.length }})</div>
              <div class="h-12"><app-sparkline [data]="costSeries(d.series)" color="violet" /></div>
            </div>
          }
        </section>
      }

      <!-- ====== Consumo global ====== -->
      <section>
        <div class="flex items-baseline justify-between mb-3">
          <h2 class="text-base font-semibold text-slate-900 dark:text-white">Consumo de IA (toda la plataforma)</h2>
          <span class="text-[11px] text-slate-400">acumulado histórico</span>
        </div>

        @if (usage(); as u) {
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
            <div class="lg:col-span-6 lg:row-span-2">
              <app-hero-metric-card
                label="Costo total acumulado"
                [value]="'$ ' + fmtUsd(u.total_cost_usd)"
                tone="violet" icon="🤖"
                subtitle="USD · todas las organizaciones"
                [hint]="u.active_orgs + ' org(s) usando IA'" />
            </div>
            <div class="lg:col-span-6 grid grid-cols-2 gap-4">
              <app-kpi-card label="Tokens totales" [value]="fmtNum(u.total_tokens)" hint="input + output" tone="info" />
              <app-kpi-card label="Llamadas" [value]="fmtNum(u.total_calls)" hint="al modelo" tone="default" />
              <app-kpi-card label="Organizaciones" [value]="u.active_orgs" hint="con consumo" tone="success" />
              <app-kpi-card label="Costo / llamada" [value]="'$ ' + avgCost(u)" hint="promedio" tone="warn" />
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            <app-chart-card title="Costo por organización" subtitle="quién consume más">
              <app-bar-chart [data]="orgBars(u)" tone="violet" />
            </app-chart-card>
            <app-chart-card title="Costo por módulo (app)" subtitle="qué apps consumen más">
              <app-bar-chart [data]="appBars(u)" tone="brand" />
            </app-chart-card>
          </div>

          <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 mt-4">
            <h3 class="text-sm font-semibold text-slate-900 dark:text-white mb-3">Por modelo</h3>
            <table class="w-full text-sm">
              <thead class="text-xs text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                <tr><th class="text-left py-2">Modelo</th><th class="text-right">Llamadas</th><th class="text-right">Tokens</th><th class="text-right">Costo</th></tr>
              </thead>
              <tbody>
                @for (m of u.by_model; track m.key) {
                  <tr class="border-b border-slate-100 dark:border-slate-800">
                    <td class="py-2 font-mono text-xs">{{ m.key }}</td>
                    <td class="text-right tabular-nums">{{ m.calls | number }}</td>
                    <td class="text-right tabular-nums">{{ m.tokens | number }}</td>
                    <td class="text-right tabular-nums font-semibold">$ {{ fmtUsd(m.cost_usd) }}</td>
                  </tr>
                } @empty {
                  <tr><td colspan="4" class="py-6 text-center text-xs text-slate-400">Sin consumo todavía. Configura la API key y empieza a usar SavvyScan.</td></tr>
                }
              </tbody>
            </table>
          </div>
        } @else {
          <p class="text-sm text-slate-500 dark:text-slate-400">Cargando consumo…</p>
        }
      </section>
    </div>
  `,
})
export class PlatformAiComponent implements OnInit {
  private readonly api = inject(ApiService);

  cfg = signal<ProviderConfig | null>(null);
  usage = signal<PlatformUsage | null>(null);
  daily = signal<{ series: { day: string; cost_usd: number }[]; budget: { spent_today_usd: number; daily_limit_usd: number; pct_used: number; blocked: boolean } } | null>(null);
  apiKeyInput = '';
  saving = signal(false);
  testing = signal(false);
  msg = signal('');
  msgErr = signal(false);

  // WhatsApp
  waToken = '';
  waTestTo = '';
  waTesting = signal(false);
  waMsg = signal('');
  waErr = signal(false);

  ngOnInit(): void {
    this.api.get<ProviderConfig>('/platform/ai/provider').subscribe({ next: (c) => this.cfg.set(c) });
    this.api.get<PlatformUsage>('/platform/ai/usage').subscribe({ next: (u) => this.usage.set(u) });
    this.api.get<{ series: { day: string; cost_usd: number }[]; budget: { spent_today_usd: number; daily_limit_usd: number; pct_used: number; blocked: boolean } }>('/platform/ai/usage/daily').subscribe({ next: (d) => this.daily.set(d) });
  }

  save(): void {
    const c = this.cfg();
    if (!c) return;
    this.saving.set(true);
    this.msg.set('');
    const body: Record<string, unknown> = {
      is_enabled: c.is_enabled,
      default_tier: c.default_tier,
      model_haiku: c.model_haiku,
      model_sonnet: c.model_sonnet,
      model_opus: c.model_opus,
      whatsapp_enabled: c.whatsapp_enabled,
      whatsapp_phone_id: c.whatsapp_phone_id,
    };
    if (this.apiKeyInput.trim()) body['api_key'] = this.apiKeyInput.trim();
    if (this.waToken.trim()) body['whatsapp_token'] = this.waToken.trim();
    this.api.patch<ProviderConfig>('/platform/ai/provider', body).subscribe({
      next: (c2) => {
        this.cfg.set(c2);
        this.apiKeyInput = '';
        this.waToken = '';
        this.saving.set(false);
        this.msgErr.set(false);
        this.msg.set('Configuración guardada.');
      },
      error: (err) => {
        this.saving.set(false);
        this.msgErr.set(true);
        this.msg.set(err?.error?.detail || 'No se pudo guardar.');
      },
    });
  }

  testConnection(): void {
    this.testing.set(true);
    this.msg.set('');
    // Si el usuario escribió una key nueva, guárdala antes de probar.
    const c = this.cfg();
    const doTest = () => {
      this.api.post<{ ok: boolean; message: string; model?: string; latency_ms?: number }>(
        '/platform/ai/provider/test', {},
      ).subscribe({
        next: (r) => {
          this.testing.set(false);
          this.msgErr.set(!r.ok);
          this.msg.set(r.ok ? `✓ ${r.message} (${r.model}, ${r.latency_ms}ms)` : r.message);
        },
        error: () => { this.testing.set(false); this.msgErr.set(true); this.msg.set('Error al probar.'); },
      });
    };
    if (this.apiKeyInput.trim() && c) {
      this.api.patch<ProviderConfig>('/platform/ai/provider', { api_key: this.apiKeyInput.trim(), is_enabled: c.is_enabled }).subscribe({
        next: (c2) => { this.cfg.set(c2); this.apiKeyInput = ''; doTest(); },
        error: () => { this.testing.set(false); this.msgErr.set(true); this.msg.set('No se pudo guardar la key.'); },
      });
    } else {
      doTest();
    }
  }

  testWhatsapp(): void {
    if (!this.waTestTo.trim()) { this.waErr.set(true); this.waMsg.set('Ingresa un número de prueba.'); return; }
    this.waTesting.set(true); this.waMsg.set('');
    const send = () => this.api.post<{ ok: boolean; reason?: string; error?: string; message_id?: string }>(
      '/platform/ai/whatsapp/test', { to: this.waTestTo.trim(), message: 'Prueba de SavvyFlow ✅' },
    ).subscribe({
      next: (r) => {
        this.waTesting.set(false); this.waErr.set(!r.ok);
        this.waMsg.set(r.ok ? `✓ Enviado (id ${r.message_id || '—'})` : (r.reason || r.error || 'No se pudo enviar.'));
      },
      error: () => { this.waTesting.set(false); this.waErr.set(true); this.waMsg.set('Error al enviar.'); },
    });
    // Si hay token/phone nuevos sin guardar, guarda primero.
    const c = this.cfg();
    if ((this.waToken.trim() || (c && c.whatsapp_phone_id)) && c) {
      const body: Record<string, unknown> = { whatsapp_enabled: c.whatsapp_enabled, whatsapp_phone_id: c.whatsapp_phone_id };
      if (this.waToken.trim()) body['whatsapp_token'] = this.waToken.trim();
      this.api.patch<ProviderConfig>('/platform/ai/provider', body).subscribe({ next: (c2) => { this.cfg.set(c2); this.waToken = ''; send(); }, error: () => send() });
    } else { send(); }
  }

  min(a: number, b: number): number { return Math.min(a, b); }
  costSeries(series: { cost_usd: number }[]): number[] { return series.map((s) => s.cost_usd); }

  fmtUsd(v: string | number): string {
    return Number(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  }
  fmtNum(v: number): string { return Number(v || 0).toLocaleString('es-CO'); }
  avgCost(u: PlatformUsage): string {
    if (!u.total_calls) return '0.0000';
    return (Number(u.total_cost_usd) / u.total_calls).toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  }
  orgBars(u: PlatformUsage): BarRow[] {
    return u.by_organization.slice(0, 8).map((o) => ({ label: o.organization_name, value: Math.round(Number(o.cost_usd) * 1_000_000) }));
  }
  appBars(u: PlatformUsage): BarRow[] {
    return u.by_app.slice(0, 8).map((a) => ({ label: a.label, value: Math.round(Number(a.cost_usd) * 1_000_000) }));
  }
}
