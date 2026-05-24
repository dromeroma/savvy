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
  allocations?: { invoice_id: string; amount: string | number }[];
}
