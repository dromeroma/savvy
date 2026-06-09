import { bootstrapApplication } from '@angular/platform-browser';
import * as Sentry from '@sentry/angular';
import { appConfig } from './app/app.config';
import { App } from './app/app';
import { environment } from './environments/environment';

// Observabilidad: Sentry solo si hay DSN configurado (no-op en caso contrario).
if (environment.sentryDsn) {
  Sentry.init({
    dsn: environment.sentryDsn,
    environment: environment.production ? 'prod' : 'dev',
    tracesSampleRate: 0.1,
    sendDefaultPii: false,
  });
}

bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));
