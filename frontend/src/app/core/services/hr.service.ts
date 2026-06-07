import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  HrAttendance,
  HrAttendanceCreate,
  HrAttendanceListItem,
  HrContract,
  HrContractCreate,
  HrDepartment,
  HrDepartmentCreate,
  HrEmployee,
  HrEmployeeCreate,
  HrEmployeeDocument,
  HrEmployeeDocumentCreate,
  HrEmployeeListItem,
  HrEmployeeUpdate,
  HrEvaluation,
  HrEvaluationCycle,
  HrEvaluationCycleCreate,
  HrEvaluationResponseInput,
  HrEvaluationResponseItem,
  HrEvaluationWithResponses,
  HrLeave,
  HrLeaveCreate,
  HrPayroll,
  HrPayrollCalculationResult,
  HrPayrollConcept,
  HrPayrollConceptCreate,
  HrPayrollPeriod,
  HrPayrollPeriodCreate,
  HrPayrollWithItems,
  HrPosition,
  HrPositionCreate,
  HrReportAbsenteeismResponse,
  HrReportCostResponse,
  HrReportHeadcountResponse,
  HrReportTenureResponse,
  HrReportTrainingSummary,
  HrShift,
  HrShiftCreate,
  HrTrainingCourse,
  HrTrainingCourseCreate,
  HrTrainingEnrollment,
  HrTrainingEnrollmentCreate,
  HrVacationBalance,
  HrVacationBalanceAdjust,
  HrVacationRequest,
  HrVacationRequestCreate,
  HrSettings,
  HrSettingsUpdate,
  Liquidation,
  LiquidationCalculationInput,
  LiquidationCreate,
  LiquidationDetail,
  LiquidationItemEdit,
  LiquidationListItem,
  LiquidationPreview,
  LiquidationTemplate,
} from '../models/hr.model';

@Injectable({ providedIn: 'root' })
export class HrApiService {
  private readonly api = inject(ApiService);

  // ---- Departments ----
  listDepartments(activeOnly = false): Observable<HrDepartment[]> {
    return this.api.get<HrDepartment[]>('/hr/departments', { active_only: activeOnly });
  }
  getDepartment(id: string): Observable<HrDepartment> {
    return this.api.get<HrDepartment>(`/hr/departments/${id}`);
  }
  createDepartment(data: HrDepartmentCreate): Observable<HrDepartment> {
    return this.api.post<HrDepartment>('/hr/departments', data);
  }
  updateDepartment(id: string, data: Partial<HrDepartmentCreate>): Observable<HrDepartment> {
    return this.api.patch<HrDepartment>(`/hr/departments/${id}`, data);
  }
  deleteDepartment(id: string): Observable<void> {
    return this.api.delete(`/hr/departments/${id}`);
  }

  // ---- Positions ----
  listPositions(params?: { active_only?: boolean; department_id?: string }): Observable<HrPosition[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.active_only !== undefined) clean['active_only'] = params.active_only;
    if (params?.department_id) clean['department_id'] = params.department_id;
    return this.api.get<HrPosition[]>('/hr/positions', clean);
  }
  getPosition(id: string): Observable<HrPosition> {
    return this.api.get<HrPosition>(`/hr/positions/${id}`);
  }
  createPosition(data: HrPositionCreate): Observable<HrPosition> {
    return this.api.post<HrPosition>('/hr/positions', data);
  }
  updatePosition(id: string, data: Partial<HrPositionCreate>): Observable<HrPosition> {
    return this.api.patch<HrPosition>(`/hr/positions/${id}`, data);
  }
  deletePosition(id: string): Observable<void> {
    return this.api.delete(`/hr/positions/${id}`);
  }

  // ---- Employees ----
  listEmployees(params?: {
    status?: string; department_id?: string; position_id?: string; search?: string;
  }): Observable<HrEmployeeListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.status) clean['status'] = params.status;
    if (params?.department_id) clean['department_id'] = params.department_id;
    if (params?.position_id) clean['position_id'] = params.position_id;
    if (params?.search) clean['search'] = params.search;
    return this.api.get<HrEmployeeListItem[]>('/hr/employees', clean);
  }
  getEmployee(id: string): Observable<HrEmployee> {
    return this.api.get<HrEmployee>(`/hr/employees/${id}`);
  }
  createEmployee(data: HrEmployeeCreate): Observable<HrEmployee> {
    return this.api.post<HrEmployee>('/hr/employees', data);
  }
  updateEmployee(id: string, data: HrEmployeeUpdate): Observable<HrEmployee> {
    return this.api.patch<HrEmployee>(`/hr/employees/${id}`, data);
  }
  deleteEmployee(id: string): Observable<void> {
    return this.api.delete(`/hr/employees/${id}`);
  }

  // ---- Contracts ----
  listContracts(params?: { employee_id?: string; status?: string }): Observable<HrContract[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrContract[]>('/hr/contracts', clean);
  }
  getContract(id: string): Observable<HrContract> {
    return this.api.get<HrContract>(`/hr/contracts/${id}`);
  }
  createContract(data: HrContractCreate): Observable<HrContract> {
    return this.api.post<HrContract>('/hr/contracts', data);
  }
  updateContract(id: string, data: Partial<HrContractCreate> & { status?: string }): Observable<HrContract> {
    return this.api.patch<HrContract>(`/hr/contracts/${id}`, data);
  }
  deleteContract(id: string): Observable<void> {
    return this.api.delete(`/hr/contracts/${id}`);
  }

  // ---- Documents ----
  listDocuments(params?: { employee_id?: string; document_type?: string }): Observable<HrEmployeeDocument[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.document_type) clean['document_type'] = params.document_type;
    return this.api.get<HrEmployeeDocument[]>('/hr/documents', clean);
  }
  getDocument(id: string): Observable<HrEmployeeDocument> {
    return this.api.get<HrEmployeeDocument>(`/hr/documents/${id}`);
  }
  createDocument(data: HrEmployeeDocumentCreate): Observable<HrEmployeeDocument> {
    return this.api.post<HrEmployeeDocument>('/hr/documents', data);
  }
  updateDocument(id: string, data: Partial<HrEmployeeDocumentCreate> & { status?: string }): Observable<HrEmployeeDocument> {
    return this.api.patch<HrEmployeeDocument>(`/hr/documents/${id}`, data);
  }
  deleteDocument(id: string): Observable<void> {
    return this.api.delete(`/hr/documents/${id}`);
  }

  // ============================================================ Fase 2

  // ---- Shifts ----
  listShifts(activeOnly = false): Observable<HrShift[]> {
    return this.api.get<HrShift[]>('/hr/shifts', { active_only: activeOnly });
  }
  createShift(data: HrShiftCreate): Observable<HrShift> {
    return this.api.post<HrShift>('/hr/shifts', data);
  }
  updateShift(id: string, data: Partial<HrShiftCreate>): Observable<HrShift> {
    return this.api.patch<HrShift>(`/hr/shifts/${id}`, data);
  }
  deleteShift(id: string): Observable<void> {
    return this.api.delete(`/hr/shifts/${id}`);
  }

  // ---- Attendance ----
  listAttendance(params?: {
    employee_id?: string; date_from?: string; date_to?: string;
    status?: string; limit?: number; offset?: number;
  }): Observable<HrAttendanceListItem[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.date_from) clean['date_from'] = params.date_from;
    if (params?.date_to) clean['date_to'] = params.date_to;
    if (params?.status) clean['status'] = params.status;
    if (params?.limit !== undefined) clean['limit'] = params.limit;
    if (params?.offset !== undefined) clean['offset'] = params.offset;
    return this.api.get<HrAttendanceListItem[]>('/hr/attendance', clean);
  }
  upsertAttendance(data: HrAttendanceCreate): Observable<HrAttendance> {
    return this.api.post<HrAttendance>('/hr/attendance', data);
  }
  updateAttendance(id: string, data: Partial<HrAttendanceCreate>): Observable<HrAttendance> {
    return this.api.patch<HrAttendance>(`/hr/attendance/${id}`, data);
  }
  deleteAttendance(id: string): Observable<void> {
    return this.api.delete(`/hr/attendance/${id}`);
  }

  // ---- Vacation balances ----
  listVacationBalances(period_year?: number): Observable<HrVacationBalance[]> {
    const clean: Record<string, string | number> = {};
    if (period_year !== undefined) clean['period_year'] = period_year;
    return this.api.get<HrVacationBalance[]>('/hr/vacation-balances', clean);
  }
  employeeVacationBalances(employeeId: string): Observable<HrVacationBalance[]> {
    return this.api.get<HrVacationBalance[]>(`/hr/employees/${employeeId}/vacation-balances`);
  }
  adjustVacationBalance(employeeId: string, data: HrVacationBalanceAdjust): Observable<HrVacationBalance> {
    return this.api.post<HrVacationBalance>(`/hr/employees/${employeeId}/vacation-balances/adjust`, data);
  }
  runMonthlyAccrual(daysPerMonth = 1.25): Observable<{ accrued_employees: number }> {
    return this.api.post<{ accrued_employees: number }>(`/hr/vacation-balances/accrue?days_per_month=${daysPerMonth}`, {});
  }

  // ---- Vacation requests ----
  listVacationRequests(params?: { employee_id?: string; status?: string }): Observable<HrVacationRequest[]> {
    const clean: Record<string, string> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrVacationRequest[]>('/hr/vacation-requests', clean);
  }
  createVacationRequest(data: HrVacationRequestCreate): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>('/hr/vacation-requests', data);
  }
  approveVacation(rid: string, notes?: string): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>(`/hr/vacation-requests/${rid}/approve`, { notes });
  }
  rejectVacation(rid: string, rejection_reason: string): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>(`/hr/vacation-requests/${rid}/reject`, { rejection_reason });
  }
  cancelVacation(rid: string): Observable<HrVacationRequest> {
    return this.api.post<HrVacationRequest>(`/hr/vacation-requests/${rid}/cancel`, {});
  }

  // ---- Leaves ----
  listLeaves(params?: { employee_id?: string; leave_type?: string; status?: string }): Observable<HrLeave[]> {
    const clean: Record<string, string> = {};
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.leave_type) clean['leave_type'] = params.leave_type;
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrLeave[]>('/hr/leaves', clean);
  }
  getLeave(id: string): Observable<HrLeave> {
    return this.api.get<HrLeave>(`/hr/leaves/${id}`);
  }
  createLeave(data: HrLeaveCreate): Observable<HrLeave> {
    return this.api.post<HrLeave>('/hr/leaves', data);
  }
  updateLeave(id: string, data: Partial<HrLeaveCreate> & { status?: string }): Observable<HrLeave> {
    return this.api.patch<HrLeave>(`/hr/leaves/${id}`, data);
  }
  deleteLeave(id: string): Observable<void> {
    return this.api.delete(`/hr/leaves/${id}`);
  }

  // ============================================================ Fase 3

  // ---- Payroll Concepts ----
  listPayrollConcepts(params?: { active_only?: boolean; concept_type?: string }): Observable<HrPayrollConcept[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.active_only !== undefined) clean['active_only'] = params.active_only;
    if (params?.concept_type) clean['concept_type'] = params.concept_type;
    return this.api.get<HrPayrollConcept[]>('/hr/payroll-concepts', clean);
  }
  createPayrollConcept(data: HrPayrollConceptCreate): Observable<HrPayrollConcept> {
    return this.api.post<HrPayrollConcept>('/hr/payroll-concepts', data);
  }
  updatePayrollConcept(id: string, data: Partial<HrPayrollConceptCreate>): Observable<HrPayrollConcept> {
    return this.api.patch<HrPayrollConcept>(`/hr/payroll-concepts/${id}`, data);
  }
  deletePayrollConcept(id: string): Observable<void> {
    return this.api.delete(`/hr/payroll-concepts/${id}`);
  }
  seedPayrollCountryTemplate(country = 'CO'): Observable<{ country_code: string; created: number }> {
    return this.api.post<{ country_code: string; created: number }>(`/hr/payroll-concepts/seed-country?country_code=${country}`, {});
  }

  // ---- Payroll Periods ----
  listPayrollPeriods(params?: { status?: string; year?: number }): Observable<HrPayrollPeriod[]> {
    const clean: Record<string, string | number> = {};
    if (params?.status) clean['status'] = params.status;
    if (params?.year !== undefined) clean['year'] = params.year;
    return this.api.get<HrPayrollPeriod[]>('/hr/payroll-periods', clean);
  }
  getPayrollPeriod(id: string): Observable<HrPayrollPeriod> {
    return this.api.get<HrPayrollPeriod>(`/hr/payroll-periods/${id}`);
  }
  createPayrollPeriod(data: HrPayrollPeriodCreate): Observable<HrPayrollPeriod> {
    return this.api.post<HrPayrollPeriod>('/hr/payroll-periods', data);
  }
  updatePayrollPeriod(id: string, data: Partial<HrPayrollPeriodCreate>): Observable<HrPayrollPeriod> {
    return this.api.patch<HrPayrollPeriod>(`/hr/payroll-periods/${id}`, data);
  }
  deletePayrollPeriod(id: string): Observable<void> {
    return this.api.delete(`/hr/payroll-periods/${id}`);
  }
  calculatePayroll(id: string): Observable<HrPayrollCalculationResult> {
    return this.api.post<HrPayrollCalculationResult>(`/hr/payroll-periods/${id}/calculate`, {});
  }
  approvePayrollPeriod(id: string): Observable<HrPayrollPeriod> {
    return this.api.post<HrPayrollPeriod>(`/hr/payroll-periods/${id}/approve`, {});
  }
  payPayrollPeriod(id: string, payment_reference?: string): Observable<HrPayrollPeriod> {
    return this.api.post<HrPayrollPeriod>(`/hr/payroll-periods/${id}/pay`, {
      payment_reference,
      create_finance_transaction: true,
    });
  }
  closePayrollPeriod(id: string): Observable<HrPayrollPeriod> {
    return this.api.post<HrPayrollPeriod>(`/hr/payroll-periods/${id}/close`, {});
  }

  // ---- Payrolls ----
  listPayrollsByPeriod(periodId: string): Observable<HrPayroll[]> {
    return this.api.get<HrPayroll[]>(`/hr/payroll-periods/${periodId}/payrolls`);
  }
  getPayroll(id: string): Observable<HrPayrollWithItems> {
    return this.api.get<HrPayrollWithItems>(`/hr/payrolls/${id}`);
  }
  payrollPdfUrl(id: string): string {
    return `/api/v1/hr/payrolls/${id}/pdf`;
  }
  downloadPayrollPdf(id: string): Observable<{ blob: Blob; filename: string | null }> {
    return this.api.getBlob(`/hr/payrolls/${id}/pdf`);
  }

  // ============================================================ Fase 4

  // ---- Evaluation Cycles ----
  listEvaluationCycles(params?: { status?: string }): Observable<HrEvaluationCycle[]> {
    const clean: Record<string, string> = {};
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrEvaluationCycle[]>('/hr/evaluation-cycles', clean);
  }
  getEvaluationCycle(id: string): Observable<HrEvaluationCycle> {
    return this.api.get<HrEvaluationCycle>(`/hr/evaluation-cycles/${id}`);
  }
  createEvaluationCycle(data: HrEvaluationCycleCreate): Observable<HrEvaluationCycle> {
    return this.api.post<HrEvaluationCycle>('/hr/evaluation-cycles', data);
  }
  updateEvaluationCycle(id: string, data: Partial<HrEvaluationCycleCreate>): Observable<HrEvaluationCycle> {
    return this.api.patch<HrEvaluationCycle>(`/hr/evaluation-cycles/${id}`, data);
  }
  deleteEvaluationCycle(id: string): Observable<void> {
    return this.api.delete(`/hr/evaluation-cycles/${id}`);
  }
  openEvaluationCycle(id: string): Observable<{ cycle_id: string; evaluations_created: number; total_employees: number }> {
    return this.api.post<{ cycle_id: string; evaluations_created: number; total_employees: number }>(`/hr/evaluation-cycles/${id}/open`, {});
  }
  closeEvaluationCycle(id: string): Observable<HrEvaluationCycle> {
    return this.api.post<HrEvaluationCycle>(`/hr/evaluation-cycles/${id}/close`, {});
  }
  listEvaluationsByCycle(cycleId: string): Observable<HrEvaluation[]> {
    return this.api.get<HrEvaluation[]>(`/hr/evaluation-cycles/${cycleId}/evaluations`);
  }
  getEvaluationDetail(id: string): Observable<HrEvaluationWithResponses> {
    return this.api.get<HrEvaluationWithResponses>(`/hr/evaluations/${id}`);
  }
  submitEvaluationResponse(id: string, data: HrEvaluationResponseInput): Observable<HrEvaluationResponseItem> {
    return this.api.post<HrEvaluationResponseItem>(`/hr/evaluations/${id}/responses`, data);
  }

  // ---- Training ----
  listTrainingCourses(params?: { active_only?: boolean; category?: string }): Observable<HrTrainingCourse[]> {
    const clean: Record<string, string | number | boolean> = {};
    if (params?.active_only !== undefined) clean['active_only'] = params.active_only;
    if (params?.category) clean['category'] = params.category;
    return this.api.get<HrTrainingCourse[]>('/hr/training-courses', clean);
  }
  createTrainingCourse(data: HrTrainingCourseCreate): Observable<HrTrainingCourse> {
    return this.api.post<HrTrainingCourse>('/hr/training-courses', data);
  }
  updateTrainingCourse(id: string, data: Partial<HrTrainingCourseCreate>): Observable<HrTrainingCourse> {
    return this.api.patch<HrTrainingCourse>(`/hr/training-courses/${id}`, data);
  }
  deleteTrainingCourse(id: string): Observable<void> {
    return this.api.delete(`/hr/training-courses/${id}`);
  }
  listTrainingEnrollments(params?: { course_id?: string; employee_id?: string; status?: string }): Observable<HrTrainingEnrollment[]> {
    const clean: Record<string, string> = {};
    if (params?.course_id) clean['course_id'] = params.course_id;
    if (params?.employee_id) clean['employee_id'] = params.employee_id;
    if (params?.status) clean['status'] = params.status;
    return this.api.get<HrTrainingEnrollment[]>('/hr/training-enrollments', clean);
  }
  createTrainingEnrollment(data: HrTrainingEnrollmentCreate): Observable<HrTrainingEnrollment> {
    return this.api.post<HrTrainingEnrollment>('/hr/training-enrollments', data);
  }
  updateTrainingEnrollment(id: string, data: Partial<HrTrainingEnrollmentCreate> & { completion_status?: string; score?: string; completed_date?: string; certificate_url?: string }): Observable<HrTrainingEnrollment> {
    return this.api.patch<HrTrainingEnrollment>(`/hr/training-enrollments/${id}`, data);
  }
  deleteTrainingEnrollment(id: string): Observable<void> {
    return this.api.delete(`/hr/training-enrollments/${id}`);
  }

  // ---- Reports ----
  reportHeadcountByDepartment(): Observable<HrReportHeadcountResponse> {
    return this.api.get<HrReportHeadcountResponse>('/hr/reports/headcount-by-department');
  }
  reportTenureDistribution(): Observable<HrReportTenureResponse> {
    return this.api.get<HrReportTenureResponse>('/hr/reports/tenure-distribution');
  }
  reportCostByDepartment(periodId: string): Observable<HrReportCostResponse> {
    return this.api.get<HrReportCostResponse>(`/hr/reports/cost-by-department/${periodId}`);
  }
  reportAbsenteeism(date_from: string, date_to: string): Observable<HrReportAbsenteeismResponse> {
    return this.api.get<HrReportAbsenteeismResponse>('/hr/reports/absenteeism', { date_from, date_to });
  }
  reportTrainingSummary(): Observable<HrReportTrainingSummary[]> {
    return this.api.get<HrReportTrainingSummary[]>('/hr/reports/training-summary');
  }

  // ============================================== Fase 5 — Settings + Liquidación

  getSettings(): Observable<HrSettings> {
    return this.api.get<HrSettings>('/hr/settings');
  }
  updateSettings(data: HrSettingsUpdate): Observable<HrSettings> {
    return this.api.patch<HrSettings>('/hr/settings', data);
  }
  downloadSettingsPreviewPdf(template: LiquidationTemplate): Observable<{ blob: Blob; filename: string | null }> {
    return this.api.getBlob(`/hr/settings/preview-pdf?template=${template}`);
  }

  calculateLiquidation(data: LiquidationCalculationInput): Observable<LiquidationPreview> {
    return this.api.post<LiquidationPreview>('/hr/liquidations/calculate', data);
  }
  listLiquidations(filters: { status?: string; employee_id?: string } = {}): Observable<LiquidationListItem[]> {
    return this.api.get<LiquidationListItem[]>('/hr/liquidations', filters);
  }
  createLiquidation(data: LiquidationCreate): Observable<Liquidation> {
    return this.api.post<Liquidation>('/hr/liquidations', data);
  }
  getLiquidation(id: string): Observable<LiquidationDetail> {
    return this.api.get<LiquidationDetail>(`/hr/liquidations/${id}`);
  }
  editLiquidationItems(id: string, data: LiquidationItemEdit): Observable<Liquidation> {
    return this.api.patch<Liquidation>(`/hr/liquidations/${id}`, data);
  }
  finalizeLiquidation(id: string): Observable<Liquidation> {
    return this.api.post<Liquidation>(`/hr/liquidations/${id}/finalize`, {});
  }
  markLiquidationPaid(id: string): Observable<Liquidation> {
    return this.api.post<Liquidation>(`/hr/liquidations/${id}/mark-paid`, {});
  }
  downloadLiquidationPdf(id: string, template?: LiquidationTemplate): Observable<{ blob: Blob; filename: string | null }> {
    const qs = template ? `?template=${template}` : '';
    return this.api.getBlob(`/hr/liquidations/${id}/pdf${qs}`);
  }
}
