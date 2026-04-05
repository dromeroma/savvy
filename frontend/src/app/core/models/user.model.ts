export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  org_slug: string;
}

export interface RegisterRequest {
  org_name: string;
  slug: string;
  email: string;
  password: string;
  name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  tokens: TokenResponse;
  user: User;
  organization: Organization;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  type: string;
}
