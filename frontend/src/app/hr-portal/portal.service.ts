import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

const TOKEN_KEY = 'hr_portal_token';
const EMPLOYEE_KEY = 'hr_portal_employee';

export interface PortalEmployee {
  id: string;
  organization_id: string;
  employee_code: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  mobile: string | null;
  address: string | null;
  department_id: string | null;
  department_name: string | null;
  position_id: string | null;
  position_name: string | null;
  hire_date: string;
  employment_type: string;
  work_location: string;
  status: string;
  organization_name: string;
}

export interface PortalAuthResponse {
  token: string;
  expires_in_seconds: number;
  employee: PortalEmployee;
}

export interface PortalContract {
  id: string;
  contract_number: string;
  contract_type: string;
  start_date: string;
  end_date: string | null;
  base_salary: string;
  currency: string;
  payment_frequency: string;
  status: string;
  eps_provider: string | null;
  pension_provider: string | null;
}

export interface PortalPayroll {
  id: string;
  period_id: string;
  period_code: string;
  period_name: string;
  period_start: string;
  period_end: string;
  payment_date: string | null;
  worked_days: string;
  total_earnings: string;
  total_deductions: string;
  net_amount: string;
  status: string;
  paid_at: string | null;
}

export interface PortalVacationBalance {
  period_year: number;
  days_accrued: string;
  days_taken: string;
  days_pending: string;
  days_compensated: string;
  days_available: string;
}

export interface PortalVacationRequest {
  id: string;
  request_number: string;
  request_type: string;
  start_date: string;
  end_date: string;
  days_count: string;
  status: string;
  request_reason: string | null;
  rejection_reason: string | null;
  requested_at: string;
}

export interface PortalLeave {
  id: string;
  leave_number: string;
  leave_type: string;
  subtype: string | null;
  start_date: string;
  end_date: string;
  days_count: string;
  is_paid: boolean;
  paid_percentage: string | null;
  amount_paid: string | null;
  status: string;
}

export interface PortalEvaluation {
  id: string;
  cycle_id: string;
  cycle_name: string;
  cycle_code: string;
  cycle_period: string | null;
  self_completed: boolean;
  supervisor_completed: boolean;
  overall_score: string | null;
  status: string;
}

export interface PortalCompetency {
  code: string;
  name: string;
  weight: number | null;
  description: string | null;
}

export interface PortalEvaluationDetail extends PortalEvaluation {
  competencies: PortalCompetency[];
  scale_min: string;
  scale_max: string;
  enable_self: boolean;
  enable_supervisor: boolean;
  enable_360: boolean;
}

export interface PortalTraining {
  id: string;
  course_id: string;
  course_code: string;
  course_name: string;
  course_category: string;
  duration_hours: string | null;
  scheduled_date: string | null;
  completed_date: string | null;
  completion_status: string;
  score: string | null;
  certificate_url: string | null;
  certificate_number: string | null;
}

export interface PortalDocument {
  id: string;
  document_type: string;
  title: string;
  description: string | null;
  file_url: string | null;
  issue_date: string | null;
  expiration_date: string | null;
  status: string;
}

@Injectable({ providedIn: 'root' })
export class HrPortalService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  }
  saveToken(t: string, employee: PortalEmployee): void {
    sessionStorage.setItem(TOKEN_KEY, t);
    sessionStorage.setItem(EMPLOYEE_KEY, JSON.stringify(employee));
  }
  getEmployeeSnapshot(): PortalEmployee | null {
    const raw = sessionStorage.getItem(EMPLOYEE_KEY);
    return raw ? JSON.parse(raw) as PortalEmployee : null;
  }
  clear(): void {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(EMPLOYEE_KEY);
  }

  private authHeaders(): HttpHeaders {
    const t = this.getToken();
    return new HttpHeaders(t ? { Authorization: `Bearer ${t}` } : {});
  }

  login(payload: { org_slug: string; employee_code: string; document_number: string }): Observable<PortalAuthResponse> {
    return this.http.post<PortalAuthResponse>(`${this.baseUrl}/hr-portal/auth`, payload);
  }
  me(): Observable<PortalEmployee> {
    return this.http.get<PortalEmployee>(`${this.baseUrl}/hr-portal/me`, { headers: this.authHeaders() });
  }
  contracts(): Observable<PortalContract[]> {
    return this.http.get<PortalContract[]>(`${this.baseUrl}/hr-portal/contracts`, { headers: this.authHeaders() });
  }
  payrolls(): Observable<PortalPayroll[]> {
    return this.http.get<PortalPayroll[]>(`${this.baseUrl}/hr-portal/payrolls`, { headers: this.authHeaders() });
  }
  downloadPayrollPdf(id: string): Observable<{ blob: Blob; filename: string | null }> {
    return new Observable((subscriber) => {
      const sub = this.http
        .get(`${this.baseUrl}/hr-portal/payrolls/${id}/pdf`, {
          headers: this.authHeaders(),
          responseType: 'blob',
          observe: 'response',
        })
        .subscribe({
          next: (res) => {
            const cd = res.headers.get('Content-Disposition') || '';
            const m = cd.match(/filename="?([^"]+)"?/i);
            subscriber.next({ blob: res.body as Blob, filename: m ? m[1] : null });
            subscriber.complete();
          },
          error: (err) => subscriber.error(err),
        });
      return () => sub.unsubscribe();
    });
  }
  vacationBalances(): Observable<PortalVacationBalance[]> {
    return this.http.get<PortalVacationBalance[]>(`${this.baseUrl}/hr-portal/vacation-balances`, { headers: this.authHeaders() });
  }
  vacationRequests(): Observable<PortalVacationRequest[]> {
    return this.http.get<PortalVacationRequest[]>(`${this.baseUrl}/hr-portal/vacation-requests`, { headers: this.authHeaders() });
  }
  createVacationRequest(data: { request_type: string; start_date: string; end_date: string; days_count: string; request_reason?: string }): Observable<PortalVacationRequest> {
    return this.http.post<PortalVacationRequest>(`${this.baseUrl}/hr-portal/vacation-requests`, data, { headers: this.authHeaders() });
  }
  leaves(): Observable<PortalLeave[]> {
    return this.http.get<PortalLeave[]>(`${this.baseUrl}/hr-portal/leaves`, { headers: this.authHeaders() });
  }
  evaluations(): Observable<PortalEvaluation[]> {
    return this.http.get<PortalEvaluation[]>(`${this.baseUrl}/hr-portal/evaluations`, { headers: this.authHeaders() });
  }
  evaluationDetail(id: string): Observable<PortalEvaluationDetail> {
    return this.http.get<PortalEvaluationDetail>(`${this.baseUrl}/hr-portal/evaluations/${id}`, { headers: this.authHeaders() });
  }
  submitEvaluationResponse(id: string, data: { evaluator_type: string; scores: Record<string, number>; comments?: string | null }): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/hr-portal/evaluations/${id}/responses`, data, { headers: this.authHeaders() });
  }
  trainings(): Observable<PortalTraining[]> {
    return this.http.get<PortalTraining[]>(`${this.baseUrl}/hr-portal/trainings`, { headers: this.authHeaders() });
  }
  documents(): Observable<PortalDocument[]> {
    return this.http.get<PortalDocument[]>(`${this.baseUrl}/hr-portal/documents`, { headers: this.authHeaders() });
  }
}
