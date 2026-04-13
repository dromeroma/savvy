import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Blocks access to /platform/* routes for anyone who isn't a super admin.
 * Non-super-admins are redirected to /dashboard.
 */
export const superAdminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/auth/login']);
  }
  if (!auth.isSuperAdmin()) {
    return router.createUrlTree(['/dashboard']);
  }
  return true;
};
