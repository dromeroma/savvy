import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap, of, catchError, switchMap } from 'rxjs';
import { ApiService } from './api.service';
import {
  AuthResponse,
  LoginRequest,
  LoginResponse,
  TokenResponse,
  User,
} from '../models/user.model';

const ACCESS_TOKEN_KEY = 'savvy_access_token';
const REFRESH_TOKEN_KEY = 'savvy_refresh_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private refreshTimer: any;
  private isRefreshing = false;

  login(data: LoginRequest): Observable<LoginResponse> {
    return this.api.post<LoginResponse>('/auth/login', data).pipe(
      tap((res) => {
        if (res.tokens) {
          this.storeTokens(res.tokens);
          this.scheduleRefresh();
        }
      }),
    );
  }

  register(data: import('../models/user.model').RegisterRequest): Observable<AuthResponse> {
    return this.api.post<AuthResponse>('/auth/register', data).pipe(
      tap((res) => {
        this.storeTokens(res.tokens);
        this.scheduleRefresh();
      }),
    );
  }

  logout(): void {
    clearTimeout(this.refreshTimer);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    this.router.navigate(['/auth/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
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

  /** Return the list of platform roles from the JWT claim (may be empty). */
  getPlatformRoles(): string[] {
    const token = this.getToken();
    if (!token) return [];
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const roles = payload.platform_roles;
      return Array.isArray(roles) ? roles : [];
    } catch {
      return [];
    }
  }

  isSuperAdmin(): boolean {
    return this.getPlatformRoles().includes('super_admin');
  }

  /** Silently refresh the access token using the refresh token */
  refreshAccessToken(): Observable<TokenResponse | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken || this.isRefreshing) {
      return of(null);
    }

    this.isRefreshing = true;
    return this.api.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }).pipe(
      tap((tokens) => {
        this.isRefreshing = false;
        this.storeTokens(tokens);
        this.scheduleRefresh();
      }),
      catchError(() => {
        this.isRefreshing = false;
        this.logout();
        return of(null);
      }),
    );
  }

  /** Start refresh timer on app init if user has a valid session */
  initSession(): void {
    if (this.isAuthenticated()) {
      this.scheduleRefresh();
    }
  }

  private storeTokens(tokens: TokenResponse): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }

  /** Schedule a silent refresh 5 minutes before the access token expires */
  private scheduleRefresh(): void {
    clearTimeout(this.refreshTimer);

    const token = this.getToken();
    if (!token) return;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiresAt = payload.exp * 1000;
      const now = Date.now();
      // Refresh 5 minutes before expiration (or immediately if less than 5 min left)
      const refreshIn = Math.max((expiresAt - now) - 5 * 60 * 1000, 10_000);

      this.refreshTimer = setTimeout(() => {
        this.refreshAccessToken().subscribe();
      }, refreshIn);
    } catch {
      // Invalid token, do nothing
    }
  }
}
