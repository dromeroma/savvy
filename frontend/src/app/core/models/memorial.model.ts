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
