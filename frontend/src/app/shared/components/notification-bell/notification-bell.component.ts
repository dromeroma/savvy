import { Component, HostListener, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { Subscription, timer } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { WaterExtrasService } from '../../../core/services/water-extras.service';
import { WaterNotification } from '../../../core/models/water-phase6.model';

@Component({
  selector: 'app-notification-bell',
  imports: [CommonModule, DatePipe],
  template: `
    <div class="relative">
      <button (click)="toggle($event)"
        class="relative inline-flex items-center justify-center w-9 h-9 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/40 transition">
        <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        @if (unread() > 0) {
          <span class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
            {{ unread() > 99 ? '99+' : unread() }}
          </span>
        }
      </button>

      @if (open()) {
        <div class="absolute right-0 mt-2 w-80 sm:w-96 max-h-[28rem] overflow-y-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-xl z-50"
          (click)="$event.stopPropagation()">
          <div class="flex items-center justify-between px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">
            <span class="text-sm font-semibold text-gray-800 dark:text-white/90">Notificaciones</span>
            @if (unread() > 0) {
              <button (click)="markAll()" class="text-xs text-brand-500 hover:text-brand-600 font-medium">Marcar todo leído</button>
            }
          </div>

          @if (loading()) {
            <div class="flex items-center justify-center py-6">
              <div class="animate-spin rounded-full h-5 w-5 border-2 border-brand-200 border-t-brand-600"></div>
            </div>
          } @else if (items().length === 0) {
            <div class="px-3 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
              Sin notificaciones
            </div>
          } @else {
            <ul class="divide-y divide-gray-100 dark:divide-gray-700">
              @for (n of items(); track n.id) {
                <li>
                  <button (click)="open_(n)"
                    class="w-full text-left px-3 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700/40 transition"
                    [ngClass]="!n.read_at ? 'bg-brand-50/40 dark:bg-brand-500/5' : ''">
                    <div class="flex items-start gap-2">
                      @if (!n.read_at) {
                        <span class="w-1.5 h-1.5 rounded-full bg-brand-500 mt-1.5 shrink-0"></span>
                      } @else {
                        <span class="w-1.5 h-1.5 mt-1.5 shrink-0"></span>
                      }
                      <div class="min-w-0 flex-1">
                        <div class="text-sm font-medium text-gray-800 dark:text-white/90 truncate">{{ n.title }}</div>
                        @if (n.body) {
                          <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{{ n.body }}</div>
                        }
                        <div class="text-[10px] text-gray-400 mt-1">{{ n.created_at | date:'short' }}</div>
                      </div>
                    </div>
                  </button>
                </li>
              }
            </ul>
          }
        </div>
      }
    </div>
  `,
})
export class NotificationBellComponent implements OnInit, OnDestroy {
  private readonly extras = inject(WaterExtrasService);
  private readonly router = inject(Router);

  open = signal(false);
  loading = signal(false);
  unread = signal(0);
  items = signal<WaterNotification[]>([]);

  private sub?: Subscription;

  ngOnInit(): void {
    // Refresh unread count every 60s
    this.sub = timer(0, 60_000).pipe(
      switchMap(() => this.extras.unreadCount()),
    ).subscribe({
      next: (r) => this.unread.set(r.unread),
      error: () => { /* ignore — likely no water app for this user */ },
    });
  }
  ngOnDestroy(): void { this.sub?.unsubscribe(); }

  toggle(ev: Event): void {
    ev.stopPropagation();
    const next = !this.open();
    this.open.set(next);
    if (next) this.refresh();
  }

  @HostListener('document:click') closeOnOutside(): void {
    if (this.open()) this.open.set(false);
  }

  refresh(): void {
    this.loading.set(true);
    this.extras.listNotifications(false, 30).subscribe({
      next: (data) => {
        this.items.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  open_(n: WaterNotification): void {
    if (!n.read_at) {
      this.extras.markRead([n.id]).subscribe(() => {
        this.unread.update((u) => Math.max(0, u - 1));
      });
    }
    this.open.set(false);
    if (n.link) this.router.navigateByUrl(n.link);
  }

  markAll(): void {
    this.extras.markAllRead().subscribe(() => {
      this.unread.set(0);
      this.refresh();
    });
  }
}
