import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { WaterExtrasService } from '../../../core/services/water-extras.service';
import { WaterNotification } from '../../../core/models/water-phase6.model';

@Component({
  selector: 'app-water-notifications',
  imports: [CommonModule, DatePipe],
  template: `
    <div class="p-4 sm:p-6 lg:p-8">
      <div class="flex items-start justify-between gap-3 mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">Notificaciones</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Todas tus notificaciones del acueducto.</p>
        </div>
        <button (click)="markAll()"
          class="px-3 py-1.5 rounded-lg text-xs font-medium bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-300 hover:bg-brand-100">
          Marcar todo como leído
        </button>
      </div>

      @if (loading()) {
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-brand-200 border-t-brand-600"></div>
        </div>
      } @else if (items().length === 0) {
        <div class="rounded-xl border border-dashed border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-10 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No tienes notificaciones todavía.</p>
        </div>
      } @else {
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          @for (n of items(); track n.id) {
            <button (click)="onOpen(n)"
              class="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/40 transition flex items-start gap-3"
              [ngClass]="!n.read_at ? 'bg-brand-50/30 dark:bg-brand-500/5' : ''">
              <span class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0"
                [ngClass]="n.read_at ? 'bg-transparent' : 'bg-brand-500'"></span>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-sm font-medium text-gray-800 dark:text-white/90">{{ n.title }}</span>
                  <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400">{{ n.type }}</span>
                </div>
                @if (n.body) {
                  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ n.body }}</div>
                }
                <div class="text-[10px] text-gray-400 mt-1">{{ n.created_at | date:'short' }}</div>
              </div>
            </button>
          }
        </div>
      }
    </div>
  `,
})
export class WaterNotificationsComponent implements OnInit {
  private readonly extras = inject(WaterExtrasService);
  private readonly router = inject(Router);

  loading = signal(true);
  items = signal<WaterNotification[]>([]);

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.extras.listNotifications(false, 100).subscribe({
      next: (data) => { this.items.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  onOpen(n: WaterNotification): void {
    if (!n.read_at) this.extras.markRead([n.id]).subscribe(() => this.load());
    if (n.link) this.router.navigateByUrl(n.link);
  }

  markAll(): void {
    this.extras.markAllRead().subscribe(() => this.load());
  }
}
