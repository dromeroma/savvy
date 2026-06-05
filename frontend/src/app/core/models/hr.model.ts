// SavvyHR — Fase 1 models

export type HrEmployeeStatus = 'active' | 'on_leave' | 'suspended' | 'terminated';
export type HrEmploymentType = 'full_time' | 'part_time' | 'intern' | 'contractor' | 'temporary';
export type HrWorkLocation = 'onsite' | 'remote' | 'hybrid';

export type HrContractType =
  | 'indefinido' | 'fijo' | 'obra_labor' | 'prestacion' | 'aprendiz' | 'practicante' | 'otro';
export type HrPaymentFrequency = 'monthly' | 'biweekly' | 'weekly';
export type HrContractStatus = 'draft' | 'active' | 'suspended' | 'terminated' | 'expired';

export type HrDocumentType =
  | 'resume' | 'contract' | 'id_copy' | 'tax_id'
  | 'eps_affiliation' | 'pension_affiliation' | 'severance_affiliation'
  | 'arl_affiliation' | 'compensation_fund_affiliation'
  | 'medical_exam' | 'background_check' | 'study_certificate' | 'work_certificate'
  | 'training_certificate' | 'disciplinary_record' | 'other';
export type HrDocumentStatus = 'valid' | 'expired' | 'revoked' | 'pending_review';

// =================================================== Department

export interface HrDepartment {
  id: string;
  organization_id: string;
  parent_id: string | null;
  code: string;
  name: string;
  description: string | null;
  cost_center: string | null;
  manager_employee_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface HrDepartmentCreate {
  code: string;
  name: string;
  description?: string | null;
  cost_center?: string | null;
  parent_id?: string | null;
  manager_employee_id?: string | null;
  is_active?: boolean;
}

// =================================================== Position

export interface HrPosition {
  id: string;
  organization_id: string;
  department_id: string | null;
  code: string;
  name: string;
  description: string | null;
  level: number | null;
  min_salary: string | null;
  max_salary: string | null;
  reference_salary: string | null;
  currency: string;
  headcount_budget: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface HrPositionCreate {
  code: string;
  name: string;
  description?: string | null;
  department_id?: string | null;
  level?: number | null;
  min_salary?: string | null;
  max_salary?: string | null;
  reference_salary?: string | null;
  currency?: string;
  headcount_budget?: number | null;
  is_active?: boolean;
}

// =================================================== Employee

export interface HrEmployee {
  id: string;
  organization_id: string;
  person_id: string | null;
  employee_code: string;
  first_name: string;
  last_name: string | null;
  document_type: string | null;
  document_number: string | null;
  birth_date: string | null;
  gender: string | null;
  marital_status: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  address: string | null;
  city: string | null;
  country_code: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  emergency_contact_relationship: string | null;
  department_id: string | null;
  position_id: string | null;
  supervisor_id: string | null;
  hire_date: string;
  termination_date: string | null;
  termination_reason: string | null;
  status: HrEmployeeStatus;
  employment_type: HrEmploymentType;
  work_location: HrWorkLocation;
  user_id: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrEmployeeCreate {
  employee_code: string;
  first_name: string;
  last_name?: string | null;
  document_type?: string | null;
  document_number?: string | null;
  birth_date?: string | null;
  gender?: string | null;
  marital_status?: string | null;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  address?: string | null;
  city?: string | null;
  country_code?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact_relationship?: string | null;
  department_id?: string | null;
  position_id?: string | null;
  supervisor_id?: string | null;
  hire_date: string;
  employment_type?: HrEmploymentType;
  work_location?: HrWorkLocation;
  user_id?: string | null;
  person_id?: string | null;
  notes?: string | null;
}

export interface HrEmployeeUpdate extends Partial<Omit<HrEmployeeCreate, 'employee_code' | 'hire_date'>> {
  status?: HrEmployeeStatus;
  termination_date?: string | null;
  termination_reason?: string | null;
}

export interface HrEmployeeListItem {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string | null;
  document_number: string | null;
  email: string | null;
  mobile: string | null;
  department_id: string | null;
  department_name: string | null;
  position_id: string | null;
  position_name: string | null;
  hire_date: string;
  status: HrEmployeeStatus;
  employment_type: HrEmploymentType;
}

// =================================================== Contract

export interface HrContract {
  id: string;
  organization_id: string;
  employee_id: string;
  contract_number: string;
  contract_type: HrContractType;
  start_date: string;
  end_date: string | null;
  trial_period_end: string | null;
  renewal_count: number;
  base_salary: string;
  currency: string;
  payment_frequency: HrPaymentFrequency;
  weekly_hours: string;
  transport_allowance: string;
  food_allowance: string;
  connectivity_allowance: string;
  other_allowance: string;
  risk_class: string | null;
  eps_provider: string | null;
  pension_provider: string | null;
  severance_provider: string | null;
  compensation_fund: string | null;
  bank_name: string | null;
  bank_account_type: string | null;
  bank_account_number: string | null;
  status: HrContractStatus;
  terminated_at: string | null;
  termination_reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrContractCreate {
  employee_id: string;
  contract_number: string;
  contract_type: HrContractType;
  start_date: string;
  end_date?: string | null;
  trial_period_end?: string | null;
  base_salary?: string;
  currency?: string;
  payment_frequency?: HrPaymentFrequency;
  weekly_hours?: string;
  transport_allowance?: string;
  food_allowance?: string;
  connectivity_allowance?: string;
  other_allowance?: string;
  risk_class?: string | null;
  eps_provider?: string | null;
  pension_provider?: string | null;
  severance_provider?: string | null;
  compensation_fund?: string | null;
  bank_name?: string | null;
  bank_account_type?: string | null;
  bank_account_number?: string | null;
  notes?: string | null;
}

// =================================================== Document

export interface HrEmployeeDocument {
  id: string;
  organization_id: string;
  employee_id: string;
  document_type: HrDocumentType;
  title: string;
  description: string | null;
  file_url: string | null;
  file_size_bytes: number | null;
  issue_date: string | null;
  expiration_date: string | null;
  issuer: string | null;
  reference_code: string | null;
  status: HrDocumentStatus;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrEmployeeDocumentCreate {
  employee_id: string;
  document_type: HrDocumentType;
  title: string;
  description?: string | null;
  file_url?: string | null;
  file_size_bytes?: number | null;
  issue_date?: string | null;
  expiration_date?: string | null;
  issuer?: string | null;
  reference_code?: string | null;
}

// =================================================== Fase 2 — Shifts

export type HrShiftType =
  | 'morning' | 'afternoon' | 'night' | 'rotating' | 'flexible' | 'administrative';

export interface HrShift {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  description: string | null;
  shift_type: HrShiftType;
  start_time: string | null;
  end_time: string | null;
  break_minutes: number;
  days_of_week: number[];
  weekly_hours: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface HrShiftCreate {
  code: string;
  name: string;
  description?: string | null;
  shift_type?: HrShiftType;
  start_time?: string | null;
  end_time?: string | null;
  break_minutes?: number;
  days_of_week?: number[];
  weekly_hours?: string | null;
  is_active?: boolean;
}

// =================================================== Fase 2 — Attendance

export type HrAttendanceStatus =
  | 'present' | 'absent' | 'late' | 'early_leave' | 'justified'
  | 'vacation' | 'sick_leave' | 'permit' | 'holiday';

export interface HrAttendance {
  id: string;
  organization_id: string;
  employee_id: string;
  shift_id: string | null;
  work_date: string;
  check_in_at: string | null;
  check_out_at: string | null;
  planned_hours: string | null;
  worked_hours: string | null;
  overtime_day_hours: string;
  overtime_night_hours: string;
  overtime_holiday_hours: string;
  status: HrAttendanceStatus;
  notes: string | null;
  recorded_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrAttendanceCreate {
  employee_id: string;
  work_date: string;
  shift_id?: string | null;
  check_in_at?: string | null;
  check_out_at?: string | null;
  planned_hours?: string | null;
  worked_hours?: string | null;
  overtime_day_hours?: string;
  overtime_night_hours?: string;
  overtime_holiday_hours?: string;
  status?: HrAttendanceStatus;
  notes?: string | null;
}

export interface HrAttendanceListItem {
  id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  work_date: string;
  check_in_at: string | null;
  check_out_at: string | null;
  worked_hours: string | null;
  overtime_total: string;
  status: HrAttendanceStatus;
}

// =================================================== Fase 2 — Vacations

export type HrVacationRequestType = 'paid' | 'compensation' | 'unpaid';
export type HrVacationStatus = 'pending' | 'approved' | 'rejected' | 'cancelled' | 'completed';

export interface HrVacationBalance {
  id: string;
  organization_id: string;
  employee_id: string;
  period_year: number;
  days_accrued: string;
  days_taken: string;
  days_pending: string;
  days_compensated: string;
  last_accrual_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrVacationBalanceAdjust {
  period_year: number;
  days_accrued?: string;
  days_taken?: string;
  days_compensated?: string;
  notes?: string | null;
}

export interface HrVacationRequest {
  id: string;
  organization_id: string;
  employee_id: string;
  request_number: string;
  request_type: HrVacationRequestType;
  start_date: string;
  end_date: string;
  days_count: string;
  status: HrVacationStatus;
  request_reason: string | null;
  rejection_reason: string | null;
  compensation_amount: string | null;
  requested_at: string;
  approved_at: string | null;
  approved_by: string | null;
  rejected_at: string | null;
  rejected_by: string | null;
  cancelled_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrVacationRequestCreate {
  employee_id: string;
  request_type?: HrVacationRequestType;
  start_date: string;
  end_date: string;
  days_count: string;
  request_reason?: string | null;
  compensation_amount?: string | null;
  notes?: string | null;
}

// =================================================== Fase 2 — Leaves

export type HrLeaveType =
  | 'medical' | 'maternity' | 'paternity' | 'bereavement'
  | 'unpaid' | 'paid_other' | 'study' | 'remunerated_permit';
export type HrLeaveStatus = 'active' | 'completed' | 'cancelled';

export interface HrLeave {
  id: string;
  organization_id: string;
  employee_id: string;
  leave_number: string;
  leave_type: HrLeaveType;
  subtype: string | null;
  start_date: string;
  end_date: string;
  days_count: string;
  is_paid: boolean;
  paid_percentage: string | null;
  amount_paid: string | null;
  supporting_doc_url: string | null;
  supporting_doc_number: string | null;
  supporting_doc_issuer: string | null;
  diagnosis_code: string | null;
  status: HrLeaveStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrLeaveCreate {
  employee_id: string;
  leave_type: HrLeaveType;
  subtype?: string | null;
  start_date: string;
  end_date: string;
  days_count: string;
  is_paid?: boolean;
  paid_percentage?: string | null;
  amount_paid?: string | null;
  supporting_doc_url?: string | null;
  supporting_doc_number?: string | null;
  supporting_doc_issuer?: string | null;
  diagnosis_code?: string | null;
  notes?: string | null;
}
