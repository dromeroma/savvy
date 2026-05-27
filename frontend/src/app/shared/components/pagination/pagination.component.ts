import { Component, computed, input, model } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-pagination',
  imports: [CommonModule, FormsModule],
  template: `
    @if (totalItems() > 0) {
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-4 py-3 border-t border-slate-200 dark:border-slate-700 text-sm">
        <div class="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <span>Mostrando</span>
          <select [(ngModel)]="pageSizeProxy"
            class="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1 text-sm">
            @for (s of pageSizeOptions; track s) {
              <option [value]="s">{{ s }}</option>
            }
          </select>
          <span>de {{ totalItems() }} · página {{ page() + 1 }} de {{ totalPages() }}</span>
        </div>

        <div class="flex items-center gap-1">
          <button type="button" (click)="goTo(0)" [disabled]="page() === 0"
            class="px-2 py-1 rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800">«</button>
          <button type="button" (click)="goTo(page() - 1)" [disabled]="page() === 0"
            class="px-2 py-1 rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800">‹</button>

          @for (p of pageWindow(); track p) {
            <button type="button" (click)="goTo(p)"
              class="min-w-[32px] px-2 py-1 rounded-md border text-sm"
              [class.border-brand-500]="p === page()"
              [class.bg-brand-50]="p === page()"
              [class.dark:bg-brand-900\/30]="p === page()"
              [class.text-brand-700]="p === page()"
              [class.dark:text-brand-300]="p === page()"
              [class.border-slate-300]="p !== page()"
              [class.dark:border-slate-600]="p !== page()"
              [class.hover:bg-slate-100]="p !== page()"
              [class.dark:hover:bg-slate-800]="p !== page()">
              {{ p + 1 }}
            </button>
          }

          <button type="button" (click)="goTo(page() + 1)" [disabled]="page() >= totalPages() - 1"
            class="px-2 py-1 rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800">›</button>
          <button type="button" (click)="goTo(totalPages() - 1)" [disabled]="page() >= totalPages() - 1"
            class="px-2 py-1 rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800">»</button>
        </div>
      </div>
    }
  `,
})
export class PaginationComponent {
  totalItems = input.required<number>();
  page = model.required<number>();
  pageSize = model.required<number>();

  readonly pageSizeOptions = [10, 20, 30, 50];

  totalPages = computed(() => Math.max(1, Math.ceil(this.totalItems() / this.pageSize())));

  /** Sliding window de 5 páginas alrededor de la actual. */
  pageWindow = computed(() => {
    const total = this.totalPages();
    const current = this.page();
    const max = 5;
    if (total <= max) return Array.from({ length: total }, (_, i) => i);
    let start = Math.max(0, current - 2);
    const end = Math.min(total, start + max);
    start = Math.max(0, end - max);
    return Array.from({ length: end - start }, (_, i) => start + i);
  });

  goTo(p: number): void {
    const max = this.totalPages() - 1;
    this.page.set(Math.max(0, Math.min(max, p)));
  }

  /** Proxy para que ngModel del select escriba al model signal y resetee página. */
  get pageSizeProxy(): number {
    return this.pageSize();
  }
  set pageSizeProxy(v: number) {
    this.pageSize.set(+v);
    this.page.set(0);
  }
}
