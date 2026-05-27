export type MemorialServiceStatus =
  | 'iniciado' | 'en_proceso' | 'pendiente' | 'finalizado' | 'cancelado';

export type MemorialServiceType =
  | 'velacion' | 'cremacion' | 'entierro'
  | 'velacion_cremacion' | 'velacion_entierro'
  | 'velacion_cremacion_entierro';

export interface MemorialFamilyMember {
  id: string;
  service_id: string;
  first_name: string;
  last_name: string | null;
  document_type: string | null;
  document_number: string | null;
  relationship: string | null;
  phone: string | null;
  mobile: string | null;
  email: string | null;
  address: string | null;
  is_primary: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface MemorialFamilyMemberCreate {
  first_name: string;
  last_name?: string | null;
  document_type?: string | null;
  document_number?: string | null;
  relationship?: string | null;
  phone?: string | null;
  mobile?: string | null;
  email?: string | null;
  address?: string | null;
  is_primary?: boolean;
  notes?: string | null;
}

export interface MemorialServiceListItem {
  id: string;
  code: string;
  consecutive: number;
  deceased_name: string;
  deceased_death_date: string;
  service_type: MemorialServiceType;
  status: MemorialServiceStatus;
  estimated_total: string;
  final_total: string;
  primary_family_name: string | null;
  primary_family_phone: string | null;
  family_count: number;
  created_at: string;
}

export interface MemorialService {
  id: string;
  organization_id: string;
  code: string;
  consecutive: number;

  deceased_first_name: string;
  deceased_last_name: string | null;
  deceased_document_type: string | null;
  deceased_document_number: string | null;
  deceased_birth_date: string | null;
  deceased_death_date: string;
  deceased_death_time: string | null;
  deceased_death_cause: string | null;
  deceased_death_place: string | null;

  service_type: MemorialServiceType;
  status: MemorialServiceStatus;

  velation_start_at: string | null;
  velation_end_at: string | null;
  velation_location: string | null;

  cremation_at: string | null;
  cremation_location: string | null;

  burial_at: string | null;
  burial_cemetery: string | null;
  burial_section: string | null;

  mass_at: string | null;
  mass_church: string | null;

  estimated_total: string;
  final_total: string;

  exequial_contract_id: string | null;
  notes: string | null;
  closed_at: string | null;
  closed_by: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;

  family_members: MemorialFamilyMember[];
}

export interface MemorialServiceCreate {
  deceased_first_name: string;
  deceased_last_name?: string | null;
  deceased_document_type?: string | null;
  deceased_document_number?: string | null;
  deceased_birth_date?: string | null;
  deceased_death_date: string;
  deceased_death_time?: string | null;
  deceased_death_cause?: string | null;
  deceased_death_place?: string | null;

  service_type: MemorialServiceType;
  status?: MemorialServiceStatus;

  velation_start_at?: string | null;
  velation_end_at?: string | null;
  velation_location?: string | null;

  cremation_at?: string | null;
  cremation_location?: string | null;

  burial_at?: string | null;
  burial_cemetery?: string | null;
  burial_section?: string | null;

  mass_at?: string | null;
  mass_church?: string | null;

  estimated_total?: string | number;
  final_total?: string | number;

  notes?: string | null;
  family_members?: MemorialFamilyMemberCreate[];
}

export interface MemorialServiceEvent {
  id: string;
  service_id: string;
  event_type: string;
  body: string | null;
  event_data: Record<string, unknown> | null;
  actor_user_id: string | null;
  created_at: string;
}

export interface MemorialDashboardKpis {
  services_total: number;
  services_active: number;
  services_closed: number;
  services_today: number;
  services_by_status: Record<string, number>;

  // Phase 2
  active_contracts: number;
  total_affiliates: number;
  plans_active: number;

  // Phase 3 — financiero
  billed_this_month: string;
  paid_this_month: string;
  pending_balance: string;
  overdue_balance: string;
  overdue_invoices: number;
  overdue_contracts: number;
}

// ===================== Phase 2: Plans + Contracts =====================

export type PlanType = 'individual' | 'familiar' | 'empresarial';
export type PaymentFrequency = 'monthly' | 'quarterly' | 'semiannual' | 'annual';
export type ContractStatus = 'active' | 'suspended' | 'cancelled' | 'expired';

export interface ExequialPlan {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  description: string | null;
  plan_type: PlanType;
  max_beneficiaries: number | null;
  max_age_at_affiliation: number | null;
  max_age_for_coverage: number | null;
  waiting_period_days: number;
  monthly_fee: string;
  quarterly_fee: string;
  semiannual_fee: string;
  annual_fee: string;
  coverage_amount: string;
  coverage_items: string[];
  is_active: boolean;
  valid_from: string;
  valid_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExequialPlanCreate {
  code: string;
  name: string;
  description?: string | null;
  plan_type: PlanType;
  max_beneficiaries?: number | null;
  max_age_at_affiliation?: number | null;
  max_age_for_coverage?: number | null;
  waiting_period_days?: number;
  monthly_fee?: string | number;
  quarterly_fee?: string | number;
  semiannual_fee?: string | number;
  annual_fee?: string | number;
  coverage_amount?: string | number;
  coverage_items?: string[];
  is_active?: boolean;
  valid_from: string;
  valid_to?: string | null;
}

export interface ExequialPlanListItem {
  id: string;
  code: string;
  name: string;
  plan_type: PlanType;
  monthly_fee: string;
  coverage_amount: string;
  is_active: boolean;
  contracts_count: number;
}

export interface ExequialBeneficiary {
  id: string;
  contract_id: string;
  first_name: string;
  last_name: string | null;
  document_type: string | null;
  document_number: string | null;
  birth_date: string | null;
  gender: string | null;
  relationship: string | null;
  is_titular: boolean;
  joined_at: string;
  removed_at: string | null;
  removed_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExequialBeneficiaryCreate {
  first_name: string;
  last_name?: string | null;
  document_type?: string | null;
  document_number?: string | null;
  birth_date?: string | null;
  gender?: string | null;
  relationship?: string | null;
  is_titular?: boolean;
  joined_at?: string | null;
}

export interface ExequialContract {
  id: string;
  organization_id: string;
  code: string;
  consecutive: number;
  plan_id: string;
  plan_name: string | null;
  plan_type: string | null;
  affiliate_type: PlanType;
  titular_first_name: string | null;
  titular_last_name: string | null;
  titular_business_name: string | null;
  titular_document_type: string | null;
  titular_document_number: string | null;
  titular_email: string | null;
  titular_phone: string | null;
  titular_mobile: string | null;
  titular_address: string | null;
  payment_frequency: PaymentFrequency;
  fee_amount: string;
  start_date: string;
  next_payment_date: string | null;
  status: ContractStatus;
  suspended_at: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  user_id: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  beneficiaries: ExequialBeneficiary[];
}

export interface ExequialContractCreate {
  plan_id: string;
  affiliate_type: PlanType;
  titular_first_name?: string | null;
  titular_last_name?: string | null;
  titular_business_name?: string | null;
  titular_document_type?: string | null;
  titular_document_number?: string | null;
  titular_email?: string | null;
  titular_phone?: string | null;
  titular_mobile?: string | null;
  titular_address?: string | null;
  payment_frequency: PaymentFrequency;
  start_date: string;
  notes?: string | null;
  beneficiaries?: ExequialBeneficiaryCreate[];
}

export interface ExequialContractListItem {
  id: string;
  code: string;
  consecutive: number;
  plan_id: string;
  plan_name: string;
  affiliate_type: PlanType;
  titular_display: string;
  titular_document_number: string | null;
  payment_frequency: PaymentFrequency;
  fee_amount: string;
  start_date: string;
  next_payment_date: string | null;
  status: ContractStatus;
  beneficiaries_count: number;
}

export interface CoverageLookupResult {
  contract_id: string;
  contract_code: string;
  plan_name: string;
  plan_type: string;
  titular_display: string;
  beneficiary_id: string;
  beneficiary_name: string;
  beneficiary_relationship: string | null;
  is_titular: boolean;
  coverage_amount: string;
  status: string;
}

// ===================== Phase 3: Invoices + Payments + Cartera =====================

export type MemorialInvoiceSource = 'exequial_dues' | 'service';
export type MemorialInvoiceStatus =
  | 'pending' | 'partial' | 'paid' | 'overdue' | 'annulled';
export type MemorialPaymentMethod = 'cash' | 'transfer' | 'card' | 'check' | 'online';

export interface MemorialInvoiceListItem {
  id: string;
  code: string;
  consecutive: number;
  source_type: MemorialInvoiceSource;
  contract_id: string | null;
  service_id: string | null;
  responsible_name: string;
  issue_date: string;
  due_date: string;
  total: string;
  paid_amount: string;
  balance: string;
  status: MemorialInvoiceStatus;
  description: string | null;
}

export interface MemorialInvoice {
  id: string;
  organization_id: string;
  code: string;
  consecutive: number;
  source_type: MemorialInvoiceSource;
  contract_id: string | null;
  service_id: string | null;
  responsible_name: string;
  responsible_document: string | null;
  responsible_email: string | null;
  responsible_phone: string | null;
  responsible_address: string | null;
  period_start: string | null;
  period_end: string | null;
  issue_date: string;
  due_date: string;
  subtotal: string;
  late_interest: string;
  surcharges: string;
  discounts: string;
  total: string;
  paid_amount: string;
  balance: string;
  status: MemorialInvoiceStatus;
  description: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface BatchGenerateDuesResult {
  generated: number;
  skipped_no_fee: number;
  invoice_ids: string[];
}

export interface GenerateServiceInvoiceRequest {
  service_id: string;
  due_days?: number;
  surcharges?: string | number;
  discounts?: string | number;
  description?: string | null;
  notes?: string | null;
}

export interface MemorialPaymentAllocation {
  invoice_id: string;
  invoice_code: string;
  amount: string;
}

export interface MemorialPaymentListItem {
  id: string;
  code: string;
  consecutive: number;
  payment_date: string;
  amount: string;
  method: MemorialPaymentMethod;
  receipt_number: string | null;
  payer_name: string;
  contract_id: string | null;
  service_id: string | null;
  invoices_count: number;
}

export interface MemorialPayment {
  id: string;
  organization_id: string;
  code: string;
  consecutive: number;
  contract_id: string | null;
  service_id: string | null;
  payer_name: string;
  payer_document: string | null;
  payer_email: string | null;
  payer_phone: string | null;
  payment_date: string;
  amount: string;
  method: MemorialPaymentMethod;
  receipt_number: string | null;
  reference: string | null;
  notes: string | null;
  recorded_by: string | null;
  created_at: string;
  updated_at: string;
  allocations: MemorialPaymentAllocation[];
}

export interface MemorialPaymentCreate {
  contract_id?: string | null;
  service_id?: string | null;
  payer_name: string;
  payer_document?: string | null;
  payer_email?: string | null;
  payer_phone?: string | null;
  payment_date: string;
  amount: string | number;
  method?: MemorialPaymentMethod;
  receipt_number?: string | null;
  reference?: string | null;
  notes?: string | null;
  allocations?: { invoice_id: string; amount: string | number }[];
}

export interface MemorialCarteraRecalcResult {
  invoices_marked_overdue: number;
  invoices_with_interest_applied: number;
  contracts_suspended: number;
  total_interest_applied: string;
}

export interface MemorialAgingBucket {
  bucket: 'current' | '0_30' | '31_60' | '61_90' | '90_plus';
  invoices: number;
  balance: string;
}

export interface MemorialAgingReport {
  total_balance: string;
  buckets: MemorialAgingBucket[];
}

export interface MemorialOverdueDebtor {
  contract_id: string | null;
  service_id: string | null;
  code: string;
  name: string;
  phone: string | null;
  email: string | null;
  overdue_invoices: number;
  oldest_due_date: string | null;
  days_overdue: number;
  total_balance: string;
}


// ===================== Phase 4: Logística =====================

export type VehicleType = 'hearse' | 'family' | 'utility' | 'other';
export type VehicleStatus = 'active' | 'maintenance' | 'inactive';
export type LocationKind = 'cemetery' | 'church' | 'other';
export type TransferType =
  | 'pickup' | 'to_velation' | 'to_cremation' | 'to_burial' | 'to_mass' | 'family' | 'other';
export type TransferStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled';

export interface MemorialVehicle {
  id: string; organization_id: string;
  code: string; plate: string;
  brand: string | null; model: string | null; year: number | null;
  type: VehicleType; capacity: number | null; color: string | null;
  status: VehicleStatus; default_driver_id: string | null;
  notes: string | null;
  created_at: string; updated_at: string;
}
export interface MemorialVehicleCreate {
  code: string; plate: string;
  brand?: string | null; model?: string | null; year?: number | null;
  type?: VehicleType; capacity?: number | null; color?: string | null;
  status?: VehicleStatus; default_driver_id?: string | null;
  notes?: string | null;
}

export interface MemorialDriver {
  id: string; organization_id: string;
  code: string;
  first_name: string; last_name: string | null;
  document_type: string | null; document_number: string | null;
  license_number: string | null; license_category: string | null;
  phone: string | null; mobile: string | null; email: string | null;
  is_active: boolean; notes: string | null;
  created_at: string; updated_at: string;
}
export interface MemorialDriverCreate {
  code: string;
  first_name: string; last_name?: string | null;
  document_type?: string | null; document_number?: string | null;
  license_number?: string | null; license_category?: string | null;
  phone?: string | null; mobile?: string | null; email?: string | null;
  is_active?: boolean; notes?: string | null;
}

export interface MemorialRoom {
  id: string; organization_id: string;
  code: string; name: string; capacity: number | null;
  location: string | null; is_active: boolean; notes: string | null;
  created_at: string; updated_at: string;
}
export interface MemorialRoomCreate {
  code: string; name: string; capacity?: number | null;
  location?: string | null; is_active?: boolean; notes?: string | null;
}

export interface MemorialOven {
  id: string; organization_id: string;
  code: string; name: string; brand: string | null; model: string | null;
  daily_capacity: number | null; is_active: boolean; notes: string | null;
  created_at: string; updated_at: string;
}
export interface MemorialOvenCreate {
  code: string; name: string; brand?: string | null; model?: string | null;
  daily_capacity?: number | null; is_active?: boolean; notes?: string | null;
}

export interface MemorialLocation {
  id: string; organization_id: string;
  code: string; name: string; kind: LocationKind;
  address: string | null; city: string | null;
  contact_name: string | null; contact_phone: string | null; contact_email: string | null;
  notes: string | null; is_active: boolean;
  created_at: string; updated_at: string;
}
export interface MemorialLocationCreate {
  code: string; name: string; kind: LocationKind;
  address?: string | null; city?: string | null;
  contact_name?: string | null; contact_phone?: string | null; contact_email?: string | null;
  notes?: string | null; is_active?: boolean;
}

export interface MemorialTransferListItem {
  id: string; code: string; consecutive: number;
  service_id: string | null; service_code: string | null;
  deceased_name: string | null;
  transfer_type: TransferType;
  vehicle_id: string | null; vehicle_label: string | null;
  driver_id: string | null; driver_name: string | null;
  scheduled_at: string; completed_at: string | null;
  origin: string | null; destination: string | null;
  status: TransferStatus;
}

export interface MemorialTransfer {
  id: string; organization_id: string;
  code: string; consecutive: number;
  service_id: string | null;
  transfer_type: TransferType;
  vehicle_id: string | null; driver_id: string | null;
  scheduled_at: string; started_at: string | null; completed_at: string | null;
  origin: string | null; destination: string | null;
  status: TransferStatus; notes: string | null;
  created_by: string | null; created_at: string; updated_at: string;
}

export interface MemorialTransferCreate {
  service_id?: string | null;
  transfer_type: TransferType;
  vehicle_id?: string | null;
  driver_id?: string | null;
  scheduled_at: string;
  origin?: string | null;
  destination?: string | null;
  notes?: string | null;
}


// ===================== Phase 5: Inventario + RRHH =====================

export type ItemCategory = 'casket' | 'urn' | 'flowers' | 'supplies' | 'vehicle_supplies' | 'other';
export type MovementType = 'entry' | 'exit' | 'adjustment' | 'transfer_out' | 'transfer_in';
export type ContractType = 'indefinido' | 'fijo' | 'obra_labor' | 'prestacion' | 'aprendiz' | 'otro';
export type EmployeeStatus = 'active' | 'on_leave' | 'suspended' | 'terminated';
export type ShiftKind = 'morning' | 'afternoon' | 'night' | 'rotating' | 'administrative';
export type AttendanceStatus = 'present' | 'absent' | 'late' | 'justified' | 'vacation' | 'sick_leave';

export interface InventoryItem {
  id: string; organization_id: string;
  code: string; name: string; category: ItemCategory;
  description: string | null; unit: string;
  current_stock: string; min_stock: string; max_stock: string | null;
  unit_cost: string; sale_price: string;
  is_active: boolean; notes: string | null;
  created_at: string; updated_at: string;
}

export interface InventoryItemCreate {
  code: string; name: string; category: ItemCategory;
  description?: string | null; unit?: string;
  initial_stock?: string | number;
  min_stock?: string | number; max_stock?: string | number | null;
  unit_cost?: string | number; sale_price?: string | number;
  is_active?: boolean; notes?: string | null;
}

export interface InventoryItemListItem {
  id: string; code: string; name: string; category: string; unit: string;
  current_stock: string; min_stock: string; max_stock: string | null;
  unit_cost: string; sale_price: string;
  is_active: boolean; is_low_stock: boolean;
}

export interface InventoryMovement {
  id: string; code: string; consecutive: number;
  organization_id: string;
  item_id: string;
  movement_type: MovementType;
  quantity: string; unit_cost: string | null;
  reason: string | null; reference_doc: string | null;
  supplier: string | null;
  service_id: string | null;
  movement_date: string;
  notes: string | null;
  recorded_by: string | null;
  created_at: string;
}

export interface InventoryMovementCreate {
  item_id: string;
  movement_type: MovementType;
  quantity: string | number;
  unit_cost?: string | number | null;
  reason?: string | null;
  reference_doc?: string | null;
  supplier?: string | null;
  service_id?: string | null;
  movement_date?: string | null;
  notes?: string | null;
}

export interface InventoryMovementListItem {
  id: string; code: string; consecutive: number;
  item_id: string; item_code: string; item_name: string;
  movement_type: MovementType;
  quantity: string; unit_cost: string | null;
  reason: string | null;
  movement_date: string; created_at: string;
}

export interface HrPosition {
  id: string; organization_id: string;
  code: string; name: string; description: string | null;
  is_active: boolean;
  created_at: string; updated_at: string;
}

export interface HrPositionCreate {
  code: string; name: string; description?: string | null; is_active?: boolean;
}

export interface HrEmployee {
  id: string; organization_id: string;
  code: string;
  first_name: string; last_name: string | null;
  document_type: string | null; document_number: string | null;
  birth_date: string | null; gender: string | null;
  email: string | null; phone: string | null; mobile: string | null;
  address: string | null;
  position_id: string | null;
  contract_type: ContractType;
  hire_date: string; end_date: string | null;
  base_salary: string;
  default_shift: ShiftKind | null;
  status: EmployeeStatus;
  user_id: string | null;
  driver_id: string | null;
  notes: string | null;
  created_at: string; updated_at: string;
}

export interface HrEmployeeCreate {
  code: string;
  first_name: string; last_name?: string | null;
  document_type?: string | null; document_number?: string | null;
  birth_date?: string | null; gender?: string | null;
  email?: string | null; phone?: string | null; mobile?: string | null;
  address?: string | null;
  position_id?: string | null;
  contract_type?: ContractType;
  hire_date: string; end_date?: string | null;
  base_salary?: string | number;
  default_shift?: ShiftKind | null;
  status?: EmployeeStatus;
  user_id?: string | null;
  driver_id?: string | null;
  notes?: string | null;
}

export interface HrEmployeeListItem {
  id: string; code: string;
  first_name: string; last_name: string | null;
  document_number: string | null;
  position_id: string | null; position_name: string | null;
  contract_type: string; hire_date: string;
  status: string; base_salary: string;
  default_shift: string | null;
}

export interface HrAttendance {
  id: string; organization_id: string;
  employee_id: string; work_date: string;
  check_in_at: string | null; check_out_at: string | null;
  hours_worked: string | null;
  status: AttendanceStatus; notes: string | null;
  created_at: string; updated_at: string;
}

export interface HrAttendanceCreate {
  employee_id: string; work_date: string;
  check_in_at?: string | null; check_out_at?: string | null;
  status?: AttendanceStatus; notes?: string | null;
}

export interface HrAttendanceListItem {
  id: string;
  employee_id: string; employee_code: string; employee_name: string;
  work_date: string;
  check_in_at: string | null; check_out_at: string | null;
  hours_worked: string | null;
  status: string;
}

