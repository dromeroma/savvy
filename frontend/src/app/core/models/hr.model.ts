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

// =================================================== Fase 3 — Payroll

export type HrPayrollConceptType =
  | 'earning' | 'deduction' | 'benefit' | 'employer_contribution' | 'informative';
export type HrPayrollCalcMethod = 'fixed' | 'percentage' | 'formula' | 'quantity_rate';

export interface HrPayrollConcept {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  description: string | null;
  concept_type: HrPayrollConceptType;
  category: string;
  calculation_method: HrPayrollCalcMethod;
  formula: string | null;
  percentage_value: string | null;
  fixed_value: string | null;
  base_concept_code: string | null;
  country_code: string | null;
  is_taxable: boolean;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface HrPayrollConceptCreate {
  code: string;
  name: string;
  description?: string | null;
  concept_type: HrPayrollConceptType;
  category: string;
  calculation_method?: HrPayrollCalcMethod;
  formula?: string | null;
  percentage_value?: string | null;
  fixed_value?: string | null;
  base_concept_code?: string | null;
  country_code?: string | null;
  is_taxable?: boolean;
  is_active?: boolean;
  sort_order?: number;
}

export type HrPayrollPeriodType = 'monthly' | 'biweekly' | 'weekly';
export type HrPayrollPeriodStatus =
  | 'draft' | 'calculating' | 'calculated' | 'approved' | 'paid' | 'closed' | 'cancelled';

export interface HrPayrollPeriod {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  period_type: HrPayrollPeriodType;
  start_date: string;
  end_date: string;
  payment_date: string | null;
  status: HrPayrollPeriodStatus;
  total_gross: string;
  total_deductions: string;
  total_net: string;
  employee_count: number;
  calculated_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
  paid_at: string | null;
  paid_by: string | null;
  closed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrPayrollPeriodCreate {
  code: string;
  name: string;
  period_type?: HrPayrollPeriodType;
  start_date: string;
  end_date: string;
  payment_date?: string | null;
  notes?: string | null;
}

export type HrPayrollStatus = 'pending' | 'calculated' | 'approved' | 'paid' | 'cancelled';

export interface HrPayrollItem {
  id: string;
  concept_code: string;
  concept_name: string;
  concept_type: HrPayrollConceptType;
  category: string | null;
  quantity: string | null;
  rate: string | null;
  base_amount: string | null;
  percentage: string | null;
  amount: string;
  sort_order: number;
}

export interface HrPayroll {
  id: string;
  organization_id: string;
  period_id: string;
  employee_id: string;
  contract_id: string | null;
  employee_code: string;
  employee_name: string;
  department_name: string | null;
  position_name: string | null;
  base_salary: string;
  worked_days: string;
  absence_days: string;
  total_earnings: string;
  total_deductions: string;
  total_benefits: string;
  total_employer_contrib: string;
  net_amount: string;
  status: HrPayrollStatus;
  paid_at: string | null;
  payment_reference: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrPayrollWithItems extends HrPayroll {
  items: HrPayrollItem[];
}

export interface HrPayrollCalculationResult {
  period_id: string;
  employees_processed: number;
  total_gross: string;
  total_deductions: string;
  total_net: string;
}

// =================================================== Fase 4 — Evaluations

export type HrEvaluationCycleStatus = 'draft' | 'open' | 'closed' | 'cancelled';
export type HrEvaluationStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type HrEvaluatorType = 'self' | 'supervisor' | 'peer' | 'subordinate';

export interface HrCompetency {
  code: string;
  name: string;
  weight: string | number;
  description?: string | null;
}

export interface HrEvaluationCycle {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  description: string | null;
  period_label: string | null;
  start_date: string;
  end_date: string;
  enable_self: boolean;
  enable_supervisor: boolean;
  enable_360: boolean;
  scale_min: string;
  scale_max: string;
  competencies: HrCompetency[];
  status: HrEvaluationCycleStatus;
  opened_at: string | null;
  closed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrEvaluationCycleCreate {
  code: string;
  name: string;
  description?: string | null;
  period_label?: string | null;
  start_date: string;
  end_date: string;
  enable_self?: boolean;
  enable_supervisor?: boolean;
  enable_360?: boolean;
  scale_min?: string;
  scale_max?: string;
  competencies: HrCompetency[];
  notes?: string | null;
}

export interface HrEvaluation {
  id: string;
  organization_id: string;
  cycle_id: string;
  employee_id: string;
  supervisor_id: string | null;
  self_completed: boolean;
  self_score: string | null;
  supervisor_completed: boolean;
  supervisor_score: string | null;
  peer_count: number;
  peer_avg: string | null;
  overall_score: string | null;
  status: HrEvaluationStatus;
  completed_at: string | null;
  improvement_plan: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrEvaluationResponseItem {
  id: string;
  evaluator_type: HrEvaluatorType;
  evaluator_user_id: string | null;
  evaluator_employee_id: string | null;
  scores: Record<string, number>;
  overall_score: string | null;
  comments: string | null;
  submitted_at: string;
}

export interface HrEvaluationWithResponses extends HrEvaluation {
  responses: HrEvaluationResponseItem[];
}

export interface HrEvaluationResponseInput {
  evaluator_type: HrEvaluatorType;
  evaluator_employee_id?: string | null;
  scores: Record<string, number>;
  comments?: string | null;
}

// =================================================== Fase 4 — Training

export type HrDeliveryMode =
  | 'in_person' | 'virtual_live' | 'virtual_async' | 'hybrid' | 'external';
export type HrEnrollmentStatus =
  | 'enrolled' | 'in_progress' | 'completed' | 'failed' | 'cancelled';

export interface HrTrainingCourse {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  description: string | null;
  category: string;
  duration_hours: string | null;
  delivery_mode: HrDeliveryMode;
  is_mandatory: boolean;
  provider: string | null;
  cost_per_seat: string | null;
  certificate_template_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface HrTrainingCourseCreate {
  code: string;
  name: string;
  description?: string | null;
  category?: string;
  duration_hours?: string | null;
  delivery_mode?: HrDeliveryMode;
  is_mandatory?: boolean;
  provider?: string | null;
  cost_per_seat?: string | null;
  certificate_template_url?: string | null;
  is_active?: boolean;
}

export interface HrTrainingEnrollment {
  id: string;
  organization_id: string;
  course_id: string;
  employee_id: string;
  scheduled_date: string | null;
  completed_date: string | null;
  completion_status: HrEnrollmentStatus;
  score: string | null;
  attendance_pct: string | null;
  certificate_url: string | null;
  certificate_number: string | null;
  cost: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrTrainingEnrollmentCreate {
  course_id: string;
  employee_id: string;
  scheduled_date?: string | null;
  notes?: string | null;
}

// =================================================== Fase 4 — Reports

export interface HrReportHeadcountRow {
  label: string;
  count: number;
  percentage: number;
}
export interface HrReportHeadcountResponse {
  total: number;
  rows: HrReportHeadcountRow[];
}

export interface HrReportTenureBucket {
  label: string;
  min_years: number;
  max_years: number | null;
  count: number;
}
export interface HrReportTenureResponse {
  total: number;
  avg_years: number;
  buckets: HrReportTenureBucket[];
}

export interface HrReportCostRow {
  department_id: string | null;
  department_name: string;
  employee_count: number;
  total_cost: string;
}
export interface HrReportCostResponse {
  period_id: string;
  period_code: string;
  total: string;
  rows: HrReportCostRow[];
}

export interface HrReportAbsenteeismRow {
  employee_id: string;
  employee_code: string;
  employee_name: string;
  absent_days: number;
  late_days: number;
  leave_days: number;
  total_days: number;
}
export interface HrReportAbsenteeismResponse {
  date_from: string;
  date_to: string;
  rows: HrReportAbsenteeismRow[];
}

export interface HrReportTrainingSummary {
  course_id: string;
  course_code: string;
  course_name: string;
  enrollments: number;
  completed: number;
  in_progress: number;
  avg_score: number | null;
  total_cost: string;
}


// ============================================================ Fase 5 — Liquidación + Settings

export type LiquidationTemplate = 'formal' | 'moderna' | 'compacta';
export type LiquidationStatus = 'draft' | 'finalized' | 'paid' | 'cancelled';
export type TerminationReason =
  | 'voluntary' | 'mutual' | 'with_cause' | 'without_cause'
  | 'end_of_contract' | 'retirement' | 'death' | 'other';
export type LiquidationItemKind = 'earning' | 'deduction';

export interface HrSettings {
  id: string;
  organization_id: string;
  default_liquidation_template: LiquidationTemplate;
  liquidation_notes_default: string | null;
  admin_name: string | null;
  admin_title: string | null;
  signature_url: string | null;
  logo_url: string | null;
  brand_color: string | null;
  created_at: string;
  updated_at: string;
}

export interface HrSettingsUpdate {
  default_liquidation_template?: LiquidationTemplate;
  liquidation_notes_default?: string | null;
  admin_name?: string | null;
  admin_title?: string | null;
  signature_url?: string | null;
  logo_url?: string | null;
  brand_color?: string | null;
}

export interface LiquidationItem {
  id?: string;
  concept_code: string;
  concept_name: string;
  kind: LiquidationItemKind;
  quantity: string;
  base_amount: string;
  rate: string | null;
  amount: string;
  is_manual: boolean;
  sort_order: number;
  notes: string | null;
}

export interface LiquidationCalculationInput {
  employee_id: string;
  termination_date: string;
  termination_reason: TerminationReason;
  last_worked_date?: string | null;
  pending_period_days?: number;
  vacation_days_pending?: string;
  has_legal_protection?: boolean;
}

export interface LiquidationPreview {
  base_salary: string;
  average_salary: string;
  days_worked_total: number;
  contract_start_date: string;
  last_worked_date: string;
  termination_date: string;
  termination_reason: TerminationReason;
  total_earnings: string;
  total_deductions: string;
  net_amount: string;
  items: LiquidationItem[];
}

export interface LiquidationCreate extends LiquidationCalculationInput {
  notes?: string | null;
  pdf_template?: LiquidationTemplate | null;
  items_override?: LiquidationItem[] | null;
}

export interface LiquidationItemEdit {
  items: LiquidationItem[];
  notes?: string | null;
  pdf_template?: LiquidationTemplate | null;
}

export interface Liquidation {
  id: string;
  organization_id: string;
  employee_id: string;
  contract_id: string | null;
  liquidation_number: string;
  termination_date: string;
  termination_reason: TerminationReason;
  last_worked_date: string;
  contract_start_date: string;
  base_salary: string;
  average_salary: string;
  days_worked_total: number;
  total_earnings: string;
  total_deductions: string;
  net_amount: string;
  currency: string;
  status: LiquidationStatus;
  paid_at: string | null;
  finalized_at: string | null;
  notes: string | null;
  pdf_template: LiquidationTemplate | null;
  created_at: string;
  updated_at: string;
}

export interface LiquidationDetail extends Liquidation {
  employee_code: string;
  employee_name: string;
  department_name: string | null;
  position_name: string | null;
  items: LiquidationItem[];
}

export interface LiquidationListItem {
  id: string;
  liquidation_number: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  termination_date: string;
  termination_reason: TerminationReason;
  net_amount: string;
  currency: string;
  status: LiquidationStatus;
  created_at: string;
}
