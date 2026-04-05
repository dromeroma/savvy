import { inject } from '@angular/core';
import { CanActivateFn, ActivatedRouteSnapshot, Router } from '@angular/router';
import { map, catchError, of } from 'rxjs';
import { AppsService } from '../services/apps.service';

export const appAccessGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const appsService = inject(AppsService);
  const router = inject(Router);
  const appCode = route.data['app'] as string;

  if (!appCode) {
    return router.createUrlTree(['/dashboard']);
  }

  return appsService.getMyApps().pipe(
    map((apps) => {
      const hasAccess = apps.some(
        (a) => a.app.code === appCode && (a.status === 'active' || a.status === 'trial'),
      );
      return hasAccess || router.createUrlTree(['/dashboard']);
    }),
    catchError(() => of(router.createUrlTree(['/dashboard']))),
  );
};
