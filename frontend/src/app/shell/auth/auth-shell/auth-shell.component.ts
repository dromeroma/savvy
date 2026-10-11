import { Component, inject, input } from '@angular/core';
import { ThemeService } from '../../../shared/services/theme.service';

/**
 * Tarjeta de acceso (login / registro) con la identidad compartida con Savvy Sites:
 * panel verde curvo de bienvenida + formulario. Estilos en styles.css (.auth-*).
 */
@Component({
  selector: 'app-auth-shell',
  template: `
    <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-gray-50 p-4 dark:bg-gray-950 sm:p-8">
      <div class="pointer-events-none absolute -left-40 -top-40 h-[28rem] w-[28rem] rounded-full bg-brand-200/40 blur-3xl dark:bg-brand-900/30"></div>
      <div class="pointer-events-none absolute -bottom-40 -right-32 h-[26rem] w-[26rem] rounded-full bg-brand-100/60 blur-3xl dark:bg-brand-900/20"></div>

      <div class="auth-card relative grid w-full max-w-5xl overflow-hidden rounded-[2.25rem] bg-white shadow-[0_30px_80px_-30px_rgba(2,44,34,0.45)] dark:bg-gray-900 lg:min-h-[36rem] lg:grid-cols-[1.05fr_1fr]">
        <!-- Panel verde -->
        <div class="relative overflow-hidden px-8 pb-24 pt-10 text-center text-white lg:px-12 lg:py-14 lg:text-left">
          <div class="auth-panel-bg absolute inset-0"></div>
          <div class="pointer-events-none absolute -bottom-24 -left-16 h-72 w-72 rounded-full border-[40px] border-white/[0.06]"></div>
          <div class="pointer-events-none absolute left-1/3 top-10 h-40 w-40 rounded-full bg-brand-300/20 blur-3xl"></div>

          <div class="relative flex h-full flex-col items-center lg:items-start">
            <span class="grid h-16 w-16 place-items-center rounded-full bg-white shadow-[0_14px_30px_-12px_rgba(0,0,0,0.45)]">
              <img src="savvy-logo.svg" alt="" width="36" height="36" class="h-9 w-9">
            </span>
            <span class="mt-3 text-xl font-bold tracking-tight">Savvy</span>

            <div class="mt-10 lg:mt-auto lg:max-w-sm">
              <h1 class="text-3xl font-extrabold leading-tight sm:text-4xl">{{ copy[mode()].title }}</h1>
              <p class="mx-auto mt-3 max-w-xs text-sm leading-relaxed text-white/80 lg:mx-0">{{ copy[mode()].text }}</p>
              <ul class="mt-7 hidden space-y-2.5 text-sm text-white/85 lg:block">
                @for (point of copy[mode()].points; track point) {
                  <li class="flex items-center gap-2.5">
                    <span class="grid h-6 w-6 place-items-center rounded-full bg-white/15">
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg>
                    </span>
                    {{ point }}
                  </li>
                }
              </ul>
            </div>

            <p class="mt-10 hidden text-xs text-white/55 lg:block">© Savvy · Savvytrix Solutions</p>
          </div>
        </div>

        <!-- Formulario -->
        <div class="relative flex items-center justify-center px-6 pb-10 pt-2 sm:px-12 lg:py-14">
          <div class="pointer-events-none absolute -right-16 -top-16 hidden h-40 w-40 rounded-full bg-gradient-to-br from-brand-500 to-brand-800 lg:block"></div>
          <div class="relative w-full max-w-sm">
            <ng-content />
            <p class="mt-10 text-center text-xs text-gray-400 lg:hidden">© Savvy · Savvytrix Solutions</p>
          </div>
        </div>
      </div>

      <button type="button" (click)="theme.toggleTheme()" aria-label="Cambiar tema"
        class="fixed bottom-6 right-6 z-50 hidden h-11 w-11 items-center justify-center rounded-full bg-white text-brand-700 shadow-lg ring-1 ring-black/5 transition hover:bg-brand-50 dark:bg-gray-800 dark:text-brand-300 sm:inline-flex">
        <svg class="hidden dark:block" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
        <svg class="dark:hidden" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
    </div>
  `,
})
export class AuthShellComponent {
  readonly theme = inject(ThemeService);
  readonly mode = input<'login' | 'register'>('login');

  readonly copy = {
    login: {
      title: '¡Bienvenido de nuevo!',
      text: 'Gestiona tu organización, tus equipos y tus apps Savvy desde un solo lugar.',
      points: ['Todas tus apps en una sola cuenta', 'Datos seguros y separados por organización', 'Acceso desde cualquier dispositivo'],
    },
    register: {
      title: 'Empieza hoy',
      text: 'Crea la cuenta de tu organización y activa las apps que necesitas.',
      points: ['Configuración guiada paso a paso', 'Prueba las apps antes de pagar', 'Soporte por WhatsApp'],
    },
  };
}
