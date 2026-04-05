import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { LoginRequest, OrgWithRole } from '../../../core/models/user.model';
import { ThemeService } from '../../../shared/services/theme.service';

@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterLink],
  templateUrl: './login.component.html',
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly themeService = inject(ThemeService);

  showPassword = false;

  form: LoginRequest = { email: '', password: '' };
  loading = signal(false);
  error = signal('');

  // Org selection state
  organizations = signal<OrgWithRole[]>([]);
  showOrgSelector = signal(false);

  onSubmit(): void {
    this.loading.set(true);
    this.error.set('');

    this.auth.login(this.form).subscribe({
      next: (res) => {
        this.loading.set(false);
        if (res.requires_org_selection && res.organizations) {
          // Multiple orgs → show selector
          this.organizations.set(res.organizations);
          this.showOrgSelector.set(true);
        } else {
          // Single org → go to dashboard
          this.router.navigate(['/dashboard']);
        }
      },
      error: (err) => {
        this.loading.set(false);
        const detail = err.error?.detail;
        const msg = typeof detail === 'string' ? detail
          : Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ')
          : 'Error al iniciar sesión. Intenta de nuevo.';
        this.error.set(msg);
      },
    });
  }

  toggleTheme(): void {
    const current = this.themeService.currentMode;
    this.themeService.toggleTheme();
  }

  selectOrg(org: OrgWithRole): void {
    this.loading.set(true);
    this.error.set('');

    this.auth.login({ ...this.form, org_id: org.id } as any).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.detail ?? 'Error al seleccionar organización.');
      },
    });
  }
}
