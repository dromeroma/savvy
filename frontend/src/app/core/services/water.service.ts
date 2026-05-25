import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  BatchGenerateRequest,
  BatchGenerateResult,
  CarteraAgingReport,
  CarteraOverdueSubscriber,
  CarteraRecalcResult,
  ClosingCreate,
  ClosingPreview,
  ClosingResponse,
  CollectorRouteSummary,
  CollectorSubscriberItem,
  RouteAssignment,
  TreasuryDashboard,
  WaterCashAccount,
  WaterCashAccountCreate,
  WaterCashAccountListItem,
  WaterConsumptionCreate,
  WaterConsumptionListItem,
  WaterDashboardKpis,
  WaterInvoice,
  WaterInvoiceListItem,
  WaterMeter,
  WaterMeterCreate,
  WaterMeterListItem,
  WaterPayment,
  WaterPaymentCreate,
  WaterPaymentListItem,
  WaterRoute,
  WaterRouteCreate,
  WaterRouteListItem,
  WaterSubscriber,
  WaterSubscriberCreate,
  WaterSubscriberListItem,
  WaterTariff,
  WaterTariffCreate,
  WaterTreasuryMovementCreate,
  WaterTreasuryMovementListItem,
} from '../models/water.model';

@Injectable({ providedIn: 'root' })
export class WaterService {
  private readonly api = inject(ApiService);

  // ---- Dashboard ----
  getKpis(): Observable<WaterDashboardKpis> {
    return this.api.get<WaterDashboardKpis>('/water/dashboard/kpis');
  }

  // ---- Subscribers ----
  listSubscribers(params?: {
    search?: string;
    status?: string;
    subscriber_type?: string;
    limit?: number;
    offset?: number;
  }): Observable<WaterSubscriberListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.search) clean['search'] = params.search;
    if (params?.status) clean['status'] = params.status;
    if (params?.subscriber_type) clean['subscriber_type'] = params.subscriber_type;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterSubscriberListItem[]>('/water/subscribers', clean);
  }

  getSubscriber(id: string): Observable<WaterSubscriber> {
    return this.api.get<WaterSubscriber>(`/water/subscribers/${id}`);
  }

  createSubscriber(data: WaterSubscriberCreate): Observable<WaterSubscriber> {
    return this.api.post<WaterSubscriber>('/water/subscribers', data);
  }

  updateSubscriber(id: string, data: Partial<WaterSubscriberCreate>): Observable<WaterSubscriber> {
    return this.api.patch<WaterSubscriber>(`/water/subscribers/${id}`, data);
  }

  deleteSubscriber(id: string): Observable<void> {
    return this.api.delete(`/water/subscribers/${id}`);
  }

  // ---- Meters ----
  listMeters(params?: {
    search?: string;
    status?: string;
    subscriber_id?: string;
    unassigned_only?: boolean;
    limit?: number;
    offset?: number;
  }): Observable<WaterMeterListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.search) clean['search'] = params.search;
    if (params?.status) clean['status'] = params.status;
    if (params?.subscriber_id) clean['subscriber_id'] = params.subscriber_id;
    if (params?.unassigned_only) clean['unassigned_only'] = true;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterMeterListItem[]>('/water/meters', clean);
  }

  getMeter(id: string): Observable<WaterMeter> {
    return this.api.get<WaterMeter>(`/water/meters/${id}`);
  }

  createMeter(data: WaterMeterCreate): Observable<WaterMeter> {
    return this.api.post<WaterMeter>('/water/meters', data);
  }

  updateMeter(id: string, data: Partial<WaterMeterCreate>): Observable<WaterMeter> {
    return this.api.patch<WaterMeter>(`/water/meters/${id}`, data);
  }

  deleteMeter(id: string): Observable<void> {
    return this.api.delete(`/water/meters/${id}`);
  }

  // ---- Tariffs ----
  listTariffs(activeOnly = false): Observable<WaterTariff[]> {
    return this.api.get<WaterTariff[]>('/water/tariffs', activeOnly ? { active_only: true } : undefined);
  }
  getTariff(id: string): Observable<WaterTariff> {
    return this.api.get<WaterTariff>(`/water/tariffs/${id}`);
  }
  createTariff(data: WaterTariffCreate): Observable<WaterTariff> {
    return this.api.post<WaterTariff>('/water/tariffs', data);
  }
  updateTariff(id: string, data: Partial<WaterTariffCreate>): Observable<WaterTariff> {
    return this.api.patch<WaterTariff>(`/water/tariffs/${id}`, data);
  }
  deleteTariff(id: string): Observable<void> {
    return this.api.delete(`/water/tariffs/${id}`);
  }

  // ---- Consumptions ----
  listConsumptions(params?: {
    period_year?: number;
    period_month?: number;
    meter_id?: string;
    subscriber_id?: string;
    limit?: number;
    offset?: number;
  }): Observable<WaterConsumptionListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.period_year !== undefined) clean['period_year'] = params.period_year;
    if (params?.period_month !== undefined) clean['period_month'] = params.period_month;
    if (params?.meter_id) clean['meter_id'] = params.meter_id;
    if (params?.subscriber_id) clean['subscriber_id'] = params.subscriber_id;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterConsumptionListItem[]>('/water/consumptions', clean);
  }
  createConsumption(data: WaterConsumptionCreate): Observable<any> {
    return this.api.post<any>('/water/consumptions', data);
  }
  deleteConsumption(id: string): Observable<void> {
    return this.api.delete(`/water/consumptions/${id}`);
  }

  // ---- Invoices ----
  listInvoices(params?: {
    status?: string;
    period_year?: number;
    period_month?: number;
    subscriber_id?: string;
    unpaid_only?: boolean;
    limit?: number;
    offset?: number;
  }): Observable<WaterInvoiceListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.status) clean['status'] = params.status;
    if (params?.period_year !== undefined) clean['period_year'] = params.period_year;
    if (params?.period_month !== undefined) clean['period_month'] = params.period_month;
    if (params?.subscriber_id) clean['subscriber_id'] = params.subscriber_id;
    if (params?.unpaid_only) clean['unpaid_only'] = true;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterInvoiceListItem[]>('/water/invoices', clean);
  }
  getInvoice(id: string): Observable<WaterInvoice> {
    return this.api.get<WaterInvoice>(`/water/invoices/${id}`);
  }
  batchGenerateInvoices(data: BatchGenerateRequest): Observable<BatchGenerateResult> {
    return this.api.post<BatchGenerateResult>('/water/invoices/batch-generate', data);
  }
  annulInvoice(id: string): Observable<WaterInvoice> {
    return this.api.post<WaterInvoice>(`/water/invoices/${id}/annul`, {});
  }
  downloadInvoicePdf(id: string): Observable<{ blob: Blob; filename: string | null }> {
    return this.api.getBlob(`/water/invoices/${id}/pdf`);
  }

  // ---- Payments ----
  listPayments(params?: {
    subscriber_id?: string;
    date_from?: string;
    date_to?: string;
    method?: string;
    limit?: number;
    offset?: number;
  }): Observable<WaterPaymentListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.subscriber_id) clean['subscriber_id'] = params.subscriber_id;
    if (params?.date_from) clean['date_from'] = params.date_from;
    if (params?.date_to) clean['date_to'] = params.date_to;
    if (params?.method) clean['method'] = params.method;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterPaymentListItem[]>('/water/payments', clean);
  }
  getPayment(id: string): Observable<WaterPayment> {
    return this.api.get<WaterPayment>(`/water/payments/${id}`);
  }
  registerPayment(data: WaterPaymentCreate): Observable<WaterPayment> {
    return this.api.post<WaterPayment>('/water/payments', data);
  }

  // ---- Subscribers — service actions ----
  suspendSubscriber(id: string, reason?: string): Observable<WaterSubscriber> {
    return this.api.post<WaterSubscriber>(
      `/water/subscribers/${id}/suspend`,
      { reason: reason ?? null, create_fee_invoice: true },
    );
  }
  reconnectSubscriber(id: string, reason?: string): Observable<WaterSubscriber> {
    return this.api.post<WaterSubscriber>(
      `/water/subscribers/${id}/reconnect`,
      { reason: reason ?? null, create_fee_invoice: true },
    );
  }

  // ---- Cartera ----
  recalcCartera(): Observable<CarteraRecalcResult> {
    return this.api.post<CarteraRecalcResult>('/water/cartera/recalculate', {});
  }
  carteraAging(): Observable<CarteraAgingReport> {
    return this.api.get<CarteraAgingReport>('/water/cartera/aging');
  }
  carteraOverdue(limit = 100): Observable<CarteraOverdueSubscriber[]> {
    return this.api.get<CarteraOverdueSubscriber[]>(
      '/water/cartera/overdue-subscribers', { limit },
    );
  }

  // ---- Routes (admin) ----
  listRoutes(activeOnly = false): Observable<WaterRouteListItem[]> {
    return this.api.get<WaterRouteListItem[]>(
      '/water/routes', activeOnly ? { active_only: true } : undefined,
    );
  }
  getRoute(id: string): Observable<WaterRoute> {
    return this.api.get<WaterRoute>(`/water/routes/${id}`);
  }
  createRoute(data: WaterRouteCreate): Observable<WaterRoute> {
    return this.api.post<WaterRoute>('/water/routes', data);
  }
  updateRoute(id: string, data: Partial<WaterRouteCreate>): Observable<WaterRoute> {
    return this.api.patch<WaterRoute>(`/water/routes/${id}`, data);
  }
  deleteRoute(id: string): Observable<void> {
    return this.api.delete(`/water/routes/${id}`);
  }
  listRouteAssignments(routeId: string): Observable<RouteAssignment[]> {
    return this.api.get<RouteAssignment[]>(`/water/routes/${routeId}/subscribers`);
  }
  assignToRoute(routeId: string, subscriberId: string, sortOrder = 0): Observable<RouteAssignment> {
    return this.api.post<RouteAssignment>(
      `/water/routes/${routeId}/subscribers`,
      { subscriber_id: subscriberId, sort_order: sortOrder },
    );
  }
  unassignFromRoute(routeId: string, subscriberId: string): Observable<void> {
    return this.api.delete(`/water/routes/${routeId}/subscribers/${subscriberId}`);
  }

  // ---- Routes — collector view ----
  myRoutes(): Observable<CollectorRouteSummary[]> {
    return this.api.get<CollectorRouteSummary[]>('/water/routes/me');
  }
  routeCollectionView(routeId: string, requireCollector = true): Observable<CollectorSubscriberItem[]> {
    return this.api.get<CollectorSubscriberItem[]>(
      `/water/routes/${routeId}/collection-view`,
      { require_collector: requireCollector },
    );
  }

  // ---- Cash accounts ----
  listCashAccounts(activeOnly = false): Observable<WaterCashAccountListItem[]> {
    return this.api.get<WaterCashAccountListItem[]>(
      '/water/cash-accounts', activeOnly ? { active_only: true } : undefined,
    );
  }
  getCashAccount(id: string): Observable<WaterCashAccount> {
    return this.api.get<WaterCashAccount>(`/water/cash-accounts/${id}`);
  }
  createCashAccount(data: WaterCashAccountCreate): Observable<WaterCashAccount> {
    return this.api.post<WaterCashAccount>('/water/cash-accounts', data);
  }
  updateCashAccount(id: string, data: Partial<WaterCashAccountCreate>): Observable<WaterCashAccount> {
    return this.api.patch<WaterCashAccount>(`/water/cash-accounts/${id}`, data);
  }
  deleteCashAccount(id: string): Observable<void> {
    return this.api.delete(`/water/cash-accounts/${id}`);
  }

  // ---- Treasury dashboard ----
  treasuryDashboard(): Observable<TreasuryDashboard> {
    return this.api.get<TreasuryDashboard>('/water/treasury/dashboard');
  }

  // ---- Treasury movements ----
  listTreasuryMovements(params?: {
    cash_account_id?: string;
    type?: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
    offset?: number;
  }): Observable<WaterTreasuryMovementListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.cash_account_id) clean['cash_account_id'] = params.cash_account_id;
    if (params?.type) clean['type'] = params.type;
    if (params?.date_from) clean['date_from'] = params.date_from;
    if (params?.date_to) clean['date_to'] = params.date_to;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<WaterTreasuryMovementListItem[]>('/water/treasury/movements', clean);
  }
  createTreasuryMovement(data: WaterTreasuryMovementCreate): Observable<any> {
    return this.api.post<any>('/water/treasury/movements', data);
  }
  deleteTreasuryMovement(id: string): Observable<void> {
    return this.api.delete(`/water/treasury/movements/${id}`);
  }

  // ---- Treasury closings (arqueos) ----
  closingPreview(cashAccountId: string, closingDate: string): Observable<ClosingPreview> {
    return this.api.get<ClosingPreview>('/water/treasury/closings/preview', {
      cash_account_id: cashAccountId, closing_date: closingDate,
    });
  }
  listClosings(cashAccountId?: string): Observable<ClosingResponse[]> {
    return this.api.get<ClosingResponse[]>(
      '/water/treasury/closings',
      cashAccountId ? { cash_account_id: cashAccountId } : undefined,
    );
  }
  createClosing(data: ClosingCreate): Observable<ClosingResponse> {
    return this.api.post<ClosingResponse>('/water/treasury/closings', data);
  }
}
