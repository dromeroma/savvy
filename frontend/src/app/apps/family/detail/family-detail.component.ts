import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-family-detail',
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div>
      @if (family()) {
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white/90">{{ family()!.name }}</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ typeLabel(family()!.type) }}
              @if (family()!.city) { · {{ family()!.city }} }
            </p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/family', unitId, 'genogram']"
              class="px-4 py-2 text-sm font-medium rounded-lg border border-pink-500 text-pink-600 dark:border-pink-400 dark:text-pink-400 hover:bg-pink-50 dark:hover:bg-pink-900/20 transition">
              🌳 Ver Genograma
            </a>
            <button (click)="showMemberModal = true"
              class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 transition">
              + Agregar Miembro
            </button>
          </div>
        </div>

        <!-- Members -->
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Miembros ({{ members().length }})</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          @for (m of members(); track m.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full flex items-center justify-center text-lg"
                  [class]="m.gender === 'male' ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-pink-100 dark:bg-pink-900/30'">
                  {{ m.gender === 'male' ? '♂' : m.gender === 'female' ? '♀' : '?' }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="font-medium text-gray-800 dark:text-white/90 truncate"
                    [class.line-through]="m.is_deceased">
                    {{ m.first_name }} {{ m.last_name }}
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    {{ roleLabel(m.role) }} · Gen {{ m.generation }}
                    @if (m.is_deceased) { · ✝ }
                  </p>
                </div>
                <button (click)="removeMember(m.id)" class="text-red-400 hover:text-red-600 text-xs">✕</button>
              </div>
            </div>
          }
          @if (members().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 col-span-full text-center py-4">No hay miembros</p>
          }
        </div>

        <!-- Annotations -->
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Anotaciones Clínicas / Pastorales</h3>
          <button (click)="showAnnotationModal = true"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition">
            + Anotación
          </button>
        </div>
        <div class="space-y-3">
          @for (a of annotations(); track a.id) {
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex justify-between items-start">
              <div>
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 text-xs rounded-full"
                    [class]="a.severity === 'severe' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      : a.severity === 'moderate' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'">
                    {{ categoryLabel(a.category) }}
                  </span>
                  <span class="text-xs text-gray-500 dark:text-gray-400">{{ a.severity }}</span>
                </div>
                @if (a.description) {
                  <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">{{ a.description }}</p>
                }
              </div>
              <span class="text-xs text-gray-400">{{ a.is_active ? 'Activa' : 'Resuelta' }}</span>
            </div>
          }
          @if (annotations().length === 0) {
            <p class="text-sm text-gray-400 dark:text-gray-500 text-center py-4">Sin anotaciones</p>
          }
        </div>
      }

      <!-- Add Member Modal -->
      @if (showMemberModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showMemberModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Agregar Miembro</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Persona</label>
                <select [(ngModel)]="memberForm.person_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">-- Seleccionar --</option>
                  @for (p of people(); track p.id) {
                    <option [value]="p.id">{{ p.first_name }} {{ p.last_name }}</option>
                  }
                </select>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rol</label>
                  <select [(ngModel)]="memberForm.role" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option value="head">Cabeza de familia</option>
                    <option value="spouse">Cónyuge</option>
                    <option value="child">Hijo/a</option>
                    <option value="grandchild">Nieto/a</option>
                    <option value="grandparent">Abuelo/a</option>
                    <option value="uncle_aunt">Tío/a</option>
                    <option value="cousin">Primo/a</option>
                    <option value="in_law">Cuñado/suegro</option>
                    <option value="other">Otro</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Generación</label>
                  <input type="number" [(ngModel)]="memberForm.generation" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm" />
                </div>
              </div>
              <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input type="checkbox" [(ngModel)]="memberForm.is_deceased" class="rounded border-gray-300" />
                Fallecido/a
              </label>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showMemberModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="addMember()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Agregar</button>
            </div>
          </div>
        </div>
      }

      <!-- Annotation Modal -->
      @if (showAnnotationModal) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" (click)="showAnnotationModal = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6" (click)="$event.stopPropagation()">
            <h3 class="text-lg font-bold text-gray-800 dark:text-white/90 mb-4">Nueva Anotación</h3>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Persona (opcional)</label>
                <select [(ngModel)]="annForm.person_id" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                  <option value="">-- Toda la familia --</option>
                  @for (m of members(); track m.id) {
                    <option [value]="m.person_id">{{ m.first_name }} {{ m.last_name }}</option>
                  }
                </select>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoría</label>
                  <select [(ngModel)]="annForm.category" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    @for (cat of categories; track cat.value) {
                      <option [value]="cat.value">{{ cat.label }}</option>
                    }
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Severidad</label>
                  <select [(ngModel)]="annForm.severity" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm">
                    <option value="mild">Leve</option>
                    <option value="moderate">Moderado</option>
                    <option value="severe">Severo</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripción</label>
                <textarea [(ngModel)]="annForm.description" rows="2" class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-white/90 px-3 py-2 text-sm"></textarea>
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-6">
              <button (click)="showAnnotationModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Cancelar</button>
              <button (click)="addAnnotation()" class="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition">Guardar</button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class FamilyDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);
  private readonly route = inject(ActivatedRoute);

  unitId = '';
  family = signal<any>(null);
  members = signal<any[]>([]);
  annotations = signal<any[]>([]);
  people = signal<any[]>([]);

  showMemberModal = false;
  showAnnotationModal = false;

  memberForm: any = { person_id: '', role: 'member', generation: 0, is_deceased: false };
  annForm: any = { person_id: '', category: 'other', severity: 'moderate', description: '' };

  readonly categories = [
    { value: 'substance_abuse', label: 'Abuso de sustancias' },
    { value: 'mental_health', label: 'Salud mental' },
    { value: 'physical_illness', label: 'Enfermedad física' },
    { value: 'violence', label: 'Violencia' },
    { value: 'conflict', label: 'Conflicto' },
    { value: 'cutoff', label: 'Ruptura' },
    { value: 'disability', label: 'Discapacidad' },
    { value: 'adoption', label: 'Adopción' },
    { value: 'spiritual', label: 'Espiritual' },
    { value: 'financial', label: 'Financiero' },
    { value: 'other', label: 'Otro' },
  ];

  ngOnInit(): void {
    this.unitId = this.route.snapshot.paramMap.get('id') || '';
    this.loadAll();
    this.api.get<any>('/people', { page_size: 500 }).subscribe({
      next: (r) => this.people.set(r.items || []),
    });
  }

  loadAll(): void {
    this.api.get<any>(`/family/units/${this.unitId}`).subscribe({ next: (r) => this.family.set(r) });
    this.api.get<any[]>(`/family/units/${this.unitId}/members`).subscribe({ next: (r) => this.members.set(r) });
    this.api.get<any[]>(`/family/units/${this.unitId}/annotations`).subscribe({ next: (r) => this.annotations.set(r) });
  }

  addMember(): void {
    if (!this.memberForm.person_id) return;
    this.api.post(`/family/units/${this.unitId}/members`, this.memberForm).subscribe({
      next: () => {
        this.showMemberModal = false;
        this.memberForm = { person_id: '', role: 'member', generation: 0, is_deceased: false };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Miembro agregado' });
        this.loadAll();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo agregar' }),
    });
  }

  removeMember(memberId: string): void {
    this.api.delete(`/family/members/${memberId}`).subscribe({
      next: () => { this.notify.show({ type: 'success', title: 'Listo', message: 'Miembro removido' }); this.loadAll(); },
    });
  }

  addAnnotation(): void {
    const payload: any = { category: this.annForm.category, severity: this.annForm.severity };
    if (this.annForm.person_id) payload.person_id = this.annForm.person_id;
    if (this.annForm.description) payload.description = this.annForm.description;

    this.api.post(`/family/units/${this.unitId}/annotations`, payload).subscribe({
      next: () => {
        this.showAnnotationModal = false;
        this.annForm = { person_id: '', category: 'other', severity: 'moderate', description: '' };
        this.notify.show({ type: 'success', title: 'Listo', message: 'Anotación creada' });
        this.loadAll();
      },
      error: () => this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo crear' }),
    });
  }

  typeLabel(t: string): string {
    return { nuclear: 'Nuclear', extended: 'Extendida', single_parent: 'Monoparental', blended: 'Reconstituida', other: 'Otra' }[t] || t;
  }

  roleLabel(r: string): string {
    return { head: 'Cabeza', spouse: 'Cónyuge', child: 'Hijo/a', grandchild: 'Nieto/a', grandparent: 'Abuelo/a', uncle_aunt: 'Tío/a', cousin: 'Primo/a', in_law: 'Familiar político', other: 'Otro', member: 'Miembro' }[r] || r;
  }

  categoryLabel(c: string): string {
    return this.categories.find((cat) => cat.value === c)?.label || c;
  }
}
