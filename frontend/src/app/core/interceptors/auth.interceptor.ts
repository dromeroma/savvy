import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.getToken();

  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      // Don't try to refresh if it's already a refresh or login request
      const isAuthRequest = req.url.includes('/auth/refresh') || req.url.includes('/auth/login');

      if (err.status === 401 && !isAuthRequest && auth.getRefreshToken()) {
        // Try to silently refresh the token
        return auth.refreshAccessToken().pipe(
          switchMap((tokens) => {
            if (tokens) {
              // Retry the original request with the new token
              const retryReq = req.clone({
                setHeaders: { Authorization: `Bearer ${tokens.access_token}` },
              });
              return next(retryReq);
            }
            // Refresh failed — logout
            auth.logout();
            return throwError(() => err);
          }),
        );
      }

      if (err.status === 401 && !isAuthRequest) {
        auth.logout();
      }

      return throwError(() => err);
    }),
  );
};
