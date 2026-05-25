// Portal del suscriptor — SavvyWater

export interface PortalMe {
  subscriber_id: string;
  code: string;
  name: string;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  address: string | null;
  neighborhood: string | null;
  stratum: number | null;
  subscriber_type: string;
  status: string;
  organization_id: string;
  organization_name: string;
}

export interface PortalDashboard {
  open_balance: string;
  overdue_count: number;
  pending_count: number;
  last_invoice_date: string | null;
  last_payment_date: string | null;
  last_consumption_cubic: string | null;
  last_consumption_period: string | null;
}

export interface PortalInvoiceItem {
  id: string;
  consecutive: number;
  period_year: number;
  period_month: number;
  issue_date: string;
  due_date: string;
  total: string;
  paid_amount: string;
  balance: string;
  status: 'pending' | 'partial' | 'paid' | 'overdue' | 'annulled';
  consumption_cubic: string;
}

export interface PortalPaymentItem {
  id: string;
  payment_date: string;
  amount: string;
  method: string;
  receipt_number: string | null;
  invoices_count: number;
}

export interface PortalConsumptionItem {
  period_year: number;
  period_month: number;
  reading_date: string;
  previous_reading: string;
  current_reading: string;
  consumption_cubic: string;
}

// PQRS
export type PqrsType = 'peticion' | 'queja' | 'reclamo' | 'sugerencia';
export type PqrsStatus = 'open' | 'in_progress' | 'resolved' | 'closed';

export interface PortalPqrsListItem {
  id: string;
  code: string;
  type: PqrsType;
  subject: string;
  status: PqrsStatus;
  created_at: string;
  responded_at: string | null;
}

export interface PortalPqrsDetail {
  id: string;
  code: string;
  type: PqrsType;
  subject: string;
  description: string;
  status: PqrsStatus;
  response: string | null;
  created_at: string;
  responded_at: string | null;
}

export interface PqrsCreate {
  type: PqrsType;
  subject: string;
  description: string;
}

// Admin PQRS
export interface AdminPqrsListItem {
  id: string;
  code: string;
  type: PqrsType;
  subject: string;
  status: PqrsStatus;
  subscriber_id: string;
  subscriber_code: string;
  subscriber_name: string;
  created_at: string;
  responded_at: string | null;
}

// Invite portal
export interface InvitePortalRequest {
  email: string;
  password: string;
  name?: string | null;
}

export interface InvitePortalResponse {
  user_id: string;
  email: string;
  name: string;
  created_new_user: boolean;
}
