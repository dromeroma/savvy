import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { RegisterRequest } from '../../../core/models/user.model';

@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  form: RegisterRequest = {
    org_name: '',
    slug: '',
    email: '',
    password: '',
    name: '',
  };
  loading = signal(false);
  error = signal('');

  onSlugify(): void {
    this.form.slug = this.form.org_name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  onSubmit(): void {
    this.loading.set(true);
    this.error.set('');

    this.auth.register(this.form).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(
          err.error?.detail ?? 'Error al registrarse. Intenta de nuevo.',
        );
      },
    });
  }
}
