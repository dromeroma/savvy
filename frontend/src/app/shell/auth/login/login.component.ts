import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { LoginRequest } from '../../../core/models/user.model';

@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterLink],
  templateUrl: './login.component.html',
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  form: LoginRequest = { email: '', password: '', org_slug: '' };
  loading = signal(false);
  error = signal('');

  onSubmit(): void {
    this.loading.set(true);
    this.error.set('');

    this.auth.login(this.form).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(
          err.error?.detail ?? 'Error al iniciar sesión. Intenta de nuevo.',
        );
      },
    });
  }
}
