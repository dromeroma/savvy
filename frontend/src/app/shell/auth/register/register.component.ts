import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { OnboardingService } from '../../../core/services/onboarding.service';
import {
  BusinessType,
  Denomination,
  RegisterRequest,
  Zone,
} from '../../../core/models/user.model';
import { ThemeService } from '../../../shared/services/theme.service';
import { NotificationService } from '../../../shared/services/notification.service';

// Logical step keys (we render only those that apply to the current selection)
type StepKey =
  | 'business_type'
  | 'church_setup'   // denomination + zone + leader
  | 'account'        // name, email, password
  | 'organization';  // org_name + slug

// Sentinel to indicate the user wants to create a custom denomination
const CUSTOM_DENOMINATION = '__custom__';

@Component({
  selector: 'app-register',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly onboarding = inject(OnboardingService);
  private readonly router = inject(Router);
  private readonly themeService = inject(ThemeService);
  private readonly notify = inject(NotificationService);

  // --- Wizard state ---
  step = signal<StepKey>('business_type');
  showPassword = false;
  loading = signal(false);
  error = signal('');

  // --- Catalogs ---
  businessTypes = signal<BusinessType[]>([]);
  denominations = signal<Denomination[]>([]);
  zones = signal<Zone[]>([]);

  // --- Selections ---
  selectedBusinessType = signal<string>('');
  // Use the special CUSTOM_DENOMINATION sentinel when the user is creating one.
  selectedDenominationId = signal<string>('');
  customDenominationName = '';
  selectedZoneId = signal<string>('');
  claimZoneLeader = signal<boolean>(false);

  // Step 'account'
  name = '';
  email = '';
  password = '';

  // Step 'organization'
  org_name = '';
  slug = '';

  // --- Derived ---
  readonly isChurch = computed(() => this.selectedBusinessType() === 'church');
  readonly isCustomDenomination = computed(
    () => this.selectedDenominationId() === CUSTOM_DENOMINATION,
  );
  readonly selectedDenominationCode = computed(() => {
    const id = this.selectedDenominationId();
    return this.denominations().find((d) => d.id === id)?.code ?? null;
  });
  /** Zones only apply to MMM today; future denominations may not have any. */
  readonly needsZone = computed(() => this.isChurch() && this.zones().length > 0);

  /** Ordered list of step keys that actually apply to the current selection. */
  readonly activeSteps = computed<StepKey[]>(() => {
    const steps: StepKey[] = ['business_type'];
    if (this.isChurch()) steps.push('church_setup');
    steps.push('account', 'organization');
    return steps;
  });

  readonly currentStepIndex = computed(() =>
    this.activeSteps().indexOf(this.step()),
  );

  readonly totalSteps = computed(() => this.activeSteps().length);

  // --- Sentinel exposed to template ---
  readonly CUSTOM = CUSTOM_DENOMINATION;

  // --- Lifecycle ---
  constructor() {
    this.onboarding.listBusinessTypes().subscribe({
      next: (types) => this.businessTypes.set(types),
      error: () => this.error.set('No se pudieron cargar los tipos de negocio.'),
    });
  }

  // --- Step navigation ---
  goNext(): void {
    const steps = this.activeSteps();
    const idx = steps.indexOf(this.step());
    if (idx < steps.length - 1) {
      this.error.set('');
      this.step.set(steps[idx + 1]);
    }
  }

  goBack(): void {
    const steps = this.activeSteps();
    const idx = steps.indexOf(this.step());
    if (idx > 0) {
      this.error.set('');
      this.step.set(steps[idx - 1]);
    }
  }

  // --- Step 1: business type ---
  selectBusinessType(code: string): void {
    this.selectedBusinessType.set(code);
    // Reset church-specific selections when switching away from church
    if (code !== 'church') {
      this.selectedDenominationId.set('');
      this.customDenominationName = '';
      this.selectedZoneId.set('');
      this.claimZoneLeader.set(false);
      this.zones.set([]);
    } else {
      // Lazy-load denominations the first time the user picks church
      if (this.denominations().length === 0) {
        this.onboarding.listDenominations('church').subscribe({
          next: (denoms) => {
            this.denominations.set(denoms);
            // Default to MMM if available
            const mmm = denoms.find((d) => d.code === 'MMM');
            if (mmm) {
              this.selectedDenominationId.set(mmm.id);
              this.loadZonesFor(mmm.id);
            }
          },
          error: () => this.error.set('No se pudieron cargar las denominaciones.'),
        });
      }
    }
  }

  confirmBusinessType(): void {
    if (!this.selectedBusinessType()) {
      this.error.set('Selecciona un tipo de negocio.');
      return;
    }
    this.goNext();
  }

  // --- Step 2: church setup ---
  onDenominationChange(id: string): void {
    this.selectedDenominationId.set(id);
    this.selectedZoneId.set('');
    this.claimZoneLeader.set(false);
    if (id && id !== CUSTOM_DENOMINATION) {
      this.loadZonesFor(id);
    } else {
      this.zones.set([]);
    }
  }

  private loadZonesFor(denominationId: string): void {
    this.onboarding.listZones(denominationId).subscribe({
      next: (zones) => this.zones.set(zones),
      error: () => this.error.set('No se pudieron cargar las zonas.'),
    });
  }

  confirmChurchSetup(): void {
    if (this.isCustomDenomination()) {
      if (!this.customDenominationName.trim()) {
        this.error.set('Escribe el nombre de tu denominación.');
        return;
      }
    } else if (!this.selectedDenominationId()) {
      this.error.set('Selecciona una denominación.');
      return;
    }
    if (this.needsZone() && !this.selectedZoneId()) {
      this.error.set('Selecciona una zona.');
      return;
    }
    this.goNext();
  }

  // --- Step 3: account ---
  confirmAccount(): void {
    if (!this.name || !this.email || !this.password) {
      this.error.set('Completa todos los campos obligatorios.');
      return;
    }
    if (this.password.length < 8) {
      this.error.set('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    this.goNext();
  }

  // --- Step 4: organization + final submit ---
  onSlugify(): void {
    this.slug = this.org_name
      .toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
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
      business_type: this.selectedBusinessType() || undefined,
    };

    if (this.isChurch()) {
      if (this.isCustomDenomination()) {
        data.denomination_name = this.customDenominationName.trim();
      } else if (this.selectedDenominationId()) {
        data.denomination_id = this.selectedDenominationId();
      }
      if (this.needsZone() && this.selectedZoneId()) {
        data.zone_id = this.selectedZoneId();
        data.claim_zone_leader = this.claimZoneLeader();
      }
    }

    this.auth.register(data).subscribe({
      next: () => {
        this.notify.show({
          type: 'success',
          title: 'Cuenta creada',
          message: 'Tu cuenta se creó exitosamente',
        });
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        const detail = err.error?.detail;
        this.error.set(
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: any) => d.msg).join(', ')
              : 'Error al registrarse.',
        );
      },
    });
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }
}
