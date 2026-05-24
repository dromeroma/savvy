export type SubscriberStatus = 'active' | 'suspended' | 'overdue' | 'retired';
export type SubscriberType = 'residential' | 'commercial' | 'industrial' | 'official';
export type MeterStatus = 'active' | 'replaced' | 'damaged' | 'inactive';

export interface WaterSubscriberListItem {
  id: string;
  code: string;
  first_name: string;
  last_name: string | null;
  business_name: string | null;
  document_number: string | null;
  address: string | null;
  neighborhood: string | null;
  subscriber_type: SubscriberType;
  status: SubscriberStatus;
  stratum: number | null;
  meter_count: number;
}

export interface WaterSubscriber {
  id: string;
  organization_id: string;
  code: string;
  document_type: string | null;
  document_number: string | null;
  first_name: string;
  last_name: string | null;
  business_name: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  address: string | null;
  neighborhood: string | null;
  city_id: number | null;
  stratum: number | null;
  subscriber_type: SubscriberType;
  status: SubscriberStatus;
  latitude: string | null;
  longitude: string | null;
  notes: string | null;
  registered_at: string | null;
  retired_at: string | null;
  user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaterSubscriberCreate {
  code: string;
  document_type?: string | null;
  document_number?: string | null;
  first_name: string;
  last_name?: string | null;
  business_name?: string | null;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  address?: string | null;
  neighborhood?: string | null;
  city_id?: number | null;
  stratum?: number | null;
  subscriber_type?: SubscriberType;
  status?: SubscriberStatus;
  notes?: string | null;
  registered_at?: string | null;
}

export interface WaterMeterListItem {
  id: string;
  serial_number: string;
  brand: string | null;
  model: string | null;
  diameter: string | null;
  status: MeterStatus;
  last_reading: string;
  last_reading_date: string | null;
  subscriber_id: string | null;
  subscriber_code: string | null;
  subscriber_name: string | null;
}

export interface WaterMeter {
  id: string;
  organization_id: string;
  subscriber_id: string | null;
  serial_number: string;
  brand: string | null;
  model: string | null;
  diameter: string | null;
  install_date: string | null;
  initial_reading: string;
  last_reading: string;
  last_reading_date: string | null;
  status: MeterStatus;
  location_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaterMeterCreate {
  subscriber_id?: string | null;
  serial_number: string;
  brand?: string | null;
  model?: string | null;
  diameter?: string | null;
  install_date?: string | null;
  initial_reading?: string;
  last_reading?: string;
  last_reading_date?: string | null;
  status?: MeterStatus;
  location_notes?: string | null;
}

export interface WaterDashboardKpis {
  total_subscribers: number;
  by_status: {
    active: number;
    suspended: number;
    overdue: number;
    retired: number;
  };
  total_meters: number;
  assigned_meters: number;
  unassigned_meters: number;
  invoices_this_month: number;
  billed_this_month: number;
  pending_balance: number;
  paid_this_month: number;
  paid_today: number;
  overdue_invoices: number;
  overdue_balance: number;
  overdue_subscribers: number;
  cash_on_hand: number;
  cash_accounts_count: number;
}

// ---------- Tariffs ----------
export interface WaterTariff {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  subscriber_type: SubscriberType;
  stratum: number | null;
  fixed_charge: string;
  price_per_cubic: string;
  basic_limit_cubic: string | null;
  surplus_price_per_cubic: string | null;
  reconnection_fee: string;
  suspension_fee: string;
  late_interest_rate: string;
  is_active: boolean;
  valid_from: string;
  valid_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaterTariffCreate {
  code: string;
  name: string;
  subscriber_type: SubscriberType;
  stratum?: number | null;
  fixed_charge?: string | number;
  price_per_cubic?: string | number;
  basic_limit_cubic?: string | number | null;
  surplus_price_per_cubic?: string | number | null;
  reconnection_fee?: string | number;
  suspension_fee?: string | number;
  late_interest_rate?: string | number;
  is_active?: boolean;
  valid_from: string;
  valid_to?: string | null;
}

// ---------- Consumptions ----------
export interface WaterConsumptionListItem {
  id: string;
  period_year: number;
  period_month: number;
  reading_date: string;
  previous_reading: string;
  current_reading: string;
  consumption_cubic: string;
  is_estimated: boolean;
  meter_id: string;
  meter_serial: string;
  subscriber_id: string;
  subscriber_code: string;
  subscriber_name: string;
  has_invoice: boolean;
}

export interface WaterConsumptionCreate {
  meter_id: string;
  period_year: number;
  period_month: number;
  reading_date: string;
  current_reading: string | number;
  is_estimated?: boolean;
  notes?: string | null;
}

// ---------- Invoices ----------
export type InvoiceStatus = 'pending' | 'paid' | 'partial' | 'overdue' | 'annulled';

export interface WaterInvoiceListItem {
  id: string;
  consecutive: number;
  period_year: number;
  period_month: number;
  issue_date: string;
  due_date: string;
  total: string;
  paid_amount: string;
  balance: string;
  status: InvoiceStatus;
  subscriber_id: string;
  subscriber_code: string;
  subscriber_name: string;
}

export interface WaterInvoice {
  id: string;
  organization_id: string;
  subscriber_id: string;
  consumption_id: string | null;
  consecutive: number;
  period_year: number;
  period_month: number;
  issue_date: string;
  due_date: string;
  fixed_charge: string;
  consumption_cubic: string;
  consumption_charge: string;
  late_interest: string;
  surcharges: string;
  discounts: string;
  reconnection_fee: string;
  suspension_fee: string;
  total: string;
  paid_amount: string;
  balance: string;
  status: InvoiceStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BatchGenerateRequest {
  period_year: number;
  period_month: number;
  issue_date?: string | null;
  due_date?: string | null;
}

export interface BatchGenerateResult {
  generated: number;
  skipped_existing: number;
  skipped_no_tariff: number;
  errors: string[];
  invoice_ids: string[];
}

// ---------- Payments ----------
export type PaymentMethod = 'cash' | 'transfer' | 'card' | 'check' | 'online';

export interface WaterPaymentListItem {
  id: string;
  payment_date: string;
  amount: string;
  method: PaymentMethod;
  receipt_number: string | null;
  reference: string | null;
  subscriber_id: string;
  subscriber_code: string;
  subscriber_name: string;
  invoices_count: number;
  cash_account_name: string | null;
}

export interface WaterPaymentAllocation {
  invoice_id: string;
  invoice_consecutive: number;
  amount: string;
}

export interface WaterPayment {
  id: string;
  organization_id: string;
  subscriber_id: string;
  receipt_number: string | null;
  payment_date: string;
  amount: string;
  method: PaymentMethod;
  reference: string | null;
  notes: string | null;
  collector_user_id: string | null;
  created_at: string;
  updated_at: string;
  allocations: WaterPaymentAllocation[];
}

export interface WaterPaymentCreate {
  subscriber_id: string;
  amount: string | number;
  payment_date: string;
  method?: PaymentMethod;
  receipt_number?: string | null;
  reference?: string | null;
  notes?: string | null;
  cash_account_id?: string | null;
  allocations?: { invoice_id: string; amount: string | number }[];
}

// ---------- Cartera ----------
export interface CarteraRecalcResult {
  invoices_marked_overdue: number;
  invoices_with_interest_applied: number;
  subscribers_marked_overdue: number;
  subscribers_recovered: number;
  total_interest_applied: string;
}

export interface CarteraAgingBucket {
  bucket: 'current' | '0_30' | '31_60' | '61_90' | '90_plus';
  invoices: number;
  balance: string;
}

export interface CarteraAgingReport {
  total_balance: string;
  buckets: CarteraAgingBucket[];
}

export interface CarteraOverdueSubscriber {
  subscriber_id: string;
  code: string;
  name: string;
  phone: string | null;
  mobile: string | null;
  status: string;
  overdue_invoices: number;
  oldest_due_date: string | null;
  days_overdue: number;
  total_balance: string;
}

// ---------- Routes ----------
export interface WaterRouteListItem {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
  collector_user_id: string | null;
  collector_name: string | null;
  subscribers_count: number;
  open_balance: string;
}

export interface WaterRoute {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  description: string | null;
  collector_user_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WaterRouteCreate {
  code: string;
  name: string;
  description?: string | null;
  collector_user_id?: string | null;
  is_active?: boolean;
}

export interface RouteAssignment {
  id: string;
  route_id: string;
  subscriber_id: string;
  subscriber_code: string;
  subscriber_name: string;
  sort_order: number;
}

export interface CollectorRouteSummary {
  route_id: string;
  route_code: string;
  route_name: string;
  subscribers_count: number;
  overdue_count: number;
  open_balance: string;
}

export interface CollectorSubscriberItem {
  subscriber_id: string;
  code: string;
  name: string;
  address: string | null;
  mobile: string | null;
  status: string;
  sort_order: number;
  open_balance: string;
  overdue_invoices: number;
  oldest_due_date: string | null;
}

// ---------- Treasury — Cash accounts ----------
export type CashAccountType = 'cash' | 'bank' | 'other';

export interface WaterCashAccountListItem {
  id: string;
  code: string;
  name: string;
  type: CashAccountType;
  is_default: boolean;
  is_active: boolean;
  initial_balance: string;
  current_balance: string;
  movement_count: number;
}

export interface WaterCashAccount {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  type: CashAccountType;
  initial_balance: string;
  is_default: boolean;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaterCashAccountCreate {
  code: string;
  name: string;
  type?: CashAccountType;
  initial_balance?: string | number;
  is_default?: boolean;
  is_active?: boolean;
  notes?: string | null;
}

// ---------- Treasury — Movements ----------
export type MovementType = 'income' | 'expense';

export interface WaterTreasuryMovementListItem {
  id: string;
  movement_date: string;
  type: MovementType;
  category: string | null;
  amount: string;
  description: string;
  reference: string | null;
  cash_account_id: string;
  cash_account_name: string;
  payment_id: string | null;
}

export interface WaterTreasuryMovementCreate {
  cash_account_id: string;
  movement_date: string;
  type: MovementType;
  category?: string | null;
  amount: string | number;
  description: string;
  reference?: string | null;
}

// ---------- Treasury — Closings (arqueos) ----------
export interface ClosingPreview {
  cash_account_id: string;
  closing_date: string;
  initial_balance: string;
  movements_income: string;
  movements_expense: string;
  expected_balance: string;
}

export interface ClosingCreate {
  cash_account_id: string;
  closing_date: string;
  counted_balance: string | number;
  notes?: string | null;
}

export interface ClosingResponse {
  id: string;
  organization_id: string;
  cash_account_id: string;
  cash_account_name: string;
  closing_date: string;
  expected_balance: string;
  counted_balance: string;
  difference: string;
  notes: string | null;
  closed_by: string | null;
  closed_at: string;
}

// ---------- Treasury — Dashboard ----------
export interface CashAccountBalance {
  cash_account_id: string;
  code: string;
  name: string;
  type: string;
  current_balance: string;
}

export interface TreasuryDashboard {
  total_balance: string;
  income_today: string;
  expense_today: string;
  income_this_month: string;
  expense_this_month: string;
  net_this_month: string;
  balances: CashAccountBalance[];
}
