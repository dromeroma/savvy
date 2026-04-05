import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { RegisterRequest } from '../../../core/models/user.model';
import { ThemeService } from '../../../shared/services/theme.service';

@Component({
  selector: 'app-register',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly themeService = inject(ThemeService);

  step = signal(1);
  showPassword = false;

  // Step 1 fields
  name = '';
  email = '';
  password = '';

  // Step 2 fields
  org_name = '';
  slug = '';

  loading = signal(false);
  error = signal('');

  onSlugify(): void {
    this.slug = this.org_name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  goToStep2(): void {
    if (!this.name || !this.email || !this.password) {
      this.error.set('Completa todos los campos obligatorios.');
      return;
    }
    if (this.password.length < 8) {
      this.error.set('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    this.error.set('');
    this.step.set(2);
  }

  backToStep1(): void {
    this.error.set('');
    this.step.set(1);
  }

  onRegister(): void {
    if (!this.org_name || !this.slug) {
      this.error.set('Completa todos los campos obligatorios.');
      return;
    }
    this.loading.set(true);
    this.error.set('');

    const data: RegisterRequest = {
      name: this.name,
      email: this.email,
      password: this.password,
      org_name: this.org_name,
      slug: this.slug,
    };

    this.auth.register(data).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        const detail = err.error?.detail;
        this.error.set(
          typeof detail === 'string' ? detail
          : Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ')
          : 'Error al registrarse.',
        );
      },
    });
  }

  toggleTheme(): void {
    const current = this.themeService.currentMode;
    this.themeService.toggleTheme();
  }
}
