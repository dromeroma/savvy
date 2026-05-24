import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import {
  DashboardService,
  DashboardSummaryResponse,
} from '../../core/services/dashboard.service';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, DatePipe, RouterLink],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private readonly dashboard = inject(DashboardService);
  private readonly router = inject(Router);

  loading = signal(true);
  error = signal('');
  data = signal<DashboardSummaryResponse | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set('');
    this.dashboard.getSummary().subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail || 'No se pudo cargar el resumen.');
      },
    });
  }

  openApp(code: string): void {
    this.router.navigate([`/${code}`]);
  }
}
