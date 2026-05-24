export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  org_name: string;
  slug: string;
  email: string;
  password: string;
  name: string;
  // Wizard-driven optional fields
  business_type?: string;
  denomination_id?: string;
  denomination_name?: string;
  zone_id?: string;
  claim_zone_leader?: boolean;
}

export interface BusinessType {
  code: string;
  name: string;
  description: string | null;
  default_app_code: string | null;
  icon: string | null;
  color: string | null;
  sort_order: number;
}

export interface Denomination {
  id: string;
  code: string;
  name: string;
  is_system: boolean;
}

export interface Zone {
  id: string;
  number: number;
  name: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface OrganizationSettings {
  fiscal_period_mode?: 'per_app' | 'unified';
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  type: string;
  business_type?: string | null;
  denomination_id?: string | null;
  zone_id?: string | null;
  settings?: OrganizationSettings;
}

export interface OrgWithRole extends Organization {
  role: string;
}

export interface AuthResponse {
  tokens: TokenResponse;
  user: User;
  organization: Organization;
}

export interface LoginResponse {
  tokens: TokenResponse | null;
  user: User;
  organization: Organization | null;
  organizations: OrgWithRole[] | null;
  requires_org_selection: boolean;
}
