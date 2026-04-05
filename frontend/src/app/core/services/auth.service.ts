import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import {
  AuthResponse,
  LoginRequest,
  TokenResponse,
  User,
} from '../models/user.model';

const ACCESS_TOKEN_KEY = 'savvy_access_token';
const REFRESH_TOKEN_KEY = 'savvy_refresh_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  login(data: LoginRequest): Observable<TokenResponse> {
    return this.api.post<TokenResponse>('/auth/login', data).pipe(
      tap((res) => this.storeTokens(res)),
    );
  }

  register(data: import('../models/user.model').RegisterRequest): Observable<AuthResponse> {
    return this.api.post<AuthResponse>('/auth/register', data).pipe(
      tap((res) => this.storeTokens(res.tokens)),
    );
  }

  logout(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    this.router.navigate(['/auth/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }

  getCurrentUser(): User | null {
    const token = this.getToken();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        id: payload.sub,
        name: payload.name ?? '',
        email: payload.email ?? '',
        created_at: '',
      };
    } catch {
      return null;
    }
  }

  private storeTokens(tokens: TokenResponse): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
}
