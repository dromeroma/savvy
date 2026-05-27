import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

const TOKEN_KEY = 'memorial_portal_token';
const CONTRACT_KEY = 'memorial_portal_contract';

export interface PortalBeneficiary {
  id: string; first_name: string; last_name: string | null;
  document_number: string | null; relationship: string | null;
  is_titular: boolean; joined_at: string;
}

export interface PortalContract {
  id: string; code: string;
  plan_name: string; plan_code: string;
  affiliate_type: 'individual' | 'familiar' | 'empresarial';
  titular_first_name: string | null; titular_last_name: string | null;
  titular_business_name: string | null; titular_email: string | null;
  titular_phone: string | null; titular_mobile: string | null;
  titular_address: string | null;
  payment_frequency: 'monthly' | 'quarterly' | 'semiannual' | 'annual';
  fee_amount: string; start_date: string;
  next_payment_date: string | null;
  status: 'active' | 'suspended' | 'cancelled' | 'expired';
  beneficiaries: PortalBeneficiary[];
  organization_name: string;
}

export interface PortalAuthResponse {
  token: string; expires_in_seconds: number; contract: PortalContract;
}

export interface PortalInvoice {
  id: string; code: string;
  issue_date: string; due_date: string;
  subtotal: string; discounts: string; late_interest: string;
  surcharges: string; total: string; paid_amount: string; balance: string;
  status: 'pending' | 'partial' | 'paid' | 'overdue' | 'annulled';
  source_type: 'exequial_dues' | 'service';
  description: string | null;
}

export interface PortalPayment {
  id: string; code: string;
  payment_date: string; amount: string;
  method: 'cash' | 'transfer' | 'card' | 'check' | 'online';
  reference: string | null; notes: string | null;
}

export interface PortalServiceItem {
  id: string; code: string;
  deceased_first_name: string; deceased_last_name: string | null;
  deceased_death_date: string;
  service_type: string; status: string;
  final_total: string;
}

@Injectable({ providedIn: 'root' })
export class MemorialPortalService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  }
  saveToken(t: string, contract: PortalContract): void {
    sessionStorage.setItem(TOKEN_KEY, t);
    sessionStorage.setItem(CONTRACT_KEY, JSON.stringify(contract));
  }
  getContractSnapshot(): PortalContract | null {
    const raw = sessionStorage.getItem(CONTRACT_KEY);
    return raw ? JSON.parse(raw) as PortalContract : null;
  }
  clear(): void {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(CONTRACT_KEY);
  }

  private authHeaders(): HttpHeaders {
    const t = this.getToken();
    return new HttpHeaders(t ? { Authorization: `Bearer ${t}` } : {});
  }

  login(payload: { org_slug: string; email?: string; document_number?: string }):
    Observable<PortalAuthResponse> {
    return this.http.post<PortalAuthResponse>(`${this.baseUrl}/memorial-portal/auth`, payload);
  }

  me(): Observable<PortalContract> {
    return this.http.get<PortalContract>(
      `${this.baseUrl}/memorial-portal/me`, { headers: this.authHeaders() },
    );
  }

  invoices(): Observable<PortalInvoice[]> {
    return this.http.get<PortalInvoice[]>(
      `${this.baseUrl}/memorial-portal/invoices`, { headers: this.authHeaders() },
    );
  }

  payments(): Observable<PortalPayment[]> {
    return this.http.get<PortalPayment[]>(
      `${this.baseUrl}/memorial-portal/payments`, { headers: this.authHeaders() },
    );
  }

  services(): Observable<PortalServiceItem[]> {
    return this.http.get<PortalServiceItem[]>(
      `${this.baseUrl}/memorial-portal/services`, { headers: this.authHeaders() },
    );
  }

  invoicePdfUrl(invoiceId: string): string {
    return `${this.baseUrl}/memorial-portal/invoices/${invoiceId}/pdf`;
  }

  downloadInvoicePdf(invoiceId: string): Observable<{ blob: Blob; filename: string | null }> {
    return new Observable((subscriber) => {
      const sub = this.http
        .get(this.invoicePdfUrl(invoiceId), {
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
}
