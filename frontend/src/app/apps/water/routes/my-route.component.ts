import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WaterService } from '../../../core/services/water.service';
import {
  CollectorRouteSummary,
  CollectorSubscriberItem,
  PaymentMethod,
  WaterPaymentCreate,
} from '../../../core/models/water.model';
import { NotificationService } from '../../../shared/services/notification.service';

@Component({
  selector: 'app-my-route',
  imports: [CommonModule, FormsModule],
  templateUrl: './my-route.component.html',
})
export class MyRouteComponent implements OnInit {
  private readonly water = inject(WaterService);
  private readonly notify = inject(NotificationService);

  loading = signal(true);
  routes = signal<CollectorRouteSummary[]>([]);
  selectedRouteId = signal<string>('');
  routeLoading = signal(false);
  routeSubscribers = signal<CollectorSubscriberItem[]>([]);

  // Quick payment modal
  payOpen = signal(false);
  payTarget = signal<CollectorSubscriberItem | null>(null);
  payAmount: string | number = 0;
  payMethod: PaymentMethod = 'cash';
  payReceipt = '';
  payDate = new Date().toISOString().slice(0, 10);
  paySaving = signal(false);
  payError = signal('');

  readonly visible = computed(() => this.routeSubscribers());

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.water.myRoutes().subscribe({
      next: (data) => {
        this.routes.set(data);
        this.loading.set(false);
        if (data.length === 1) {
          this.openRoute(data[0].route_id);
        }
      },
      error: () => this.loading.set(false),
    });
  }

  openRoute(id: string): void {
    this.selectedRouteId.set(id);
    this.routeLoading.set(true);
    this.water.routeCollectionView(id, true).subscribe({
      next: (data) => {
        this.routeSubscribers.set(data);
        this.routeLoading.set(false);
      },
      error: (err) => {
        this.routeLoading.set(false);
        this.notify.show({
          type: 'error', title: 'Error',
          message: err?.error?.detail || 'No se pudo cargar la ruta.',
        });
      },
    });
  }

  backToRoutes(): void {
    this.selectedRouteId.set('');
    this.routeSubscribers.set([]);
  }

  // ---- Quick payment ----
  openPay(s: CollectorSubscriberItem): void {
    this.payTarget.set(s);
    this.payAmount = s.open_balance;
    this.payMethod = 'cash';
    this.payReceipt = '';
    this.payDate = new Date().toISOString().slice(0, 10);
    this.payError.set('');
    this.payOpen.set(true);
  }
  closePay(): void { this.payOpen.set(false); }

  submitPay(): void {
    const s = this.payTarget();
    if (!s) return;
    const amount = parseFloat(String(this.payAmount || 0));
    if (amount <= 0) {
      this.payError.set('El monto debe ser mayor a 0.');
      return;
    }
    const data: WaterPaymentCreate = {
      subscriber_id: s.subscriber_id,
      amount,
      payment_date: this.payDate,
      method: this.payMethod,
      receipt_number: this.payReceipt || null,
    };
    this.paySaving.set(true);
    this.payError.set('');
    this.water.registerPayment(data).subscribe({
      next: () => {
        this.paySaving.set(false);
        this.closePay();
        this.notify.show({ type: 'success', title: 'Pago registrado', message: `Pago aplicado a ${s.code}.` });
        // Refresh the route view
        this.openRoute(this.selectedRouteId());
      },
      error: (err) => {
        this.paySaving.set(false);
        this.payError.set(err?.error?.detail || 'Error al registrar el pago.');
      },
    });
  }

  statusBadge(status: string): string {
    switch (status) {
      case 'active': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300';
      case 'suspended': return 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300';
      case 'overdue': return 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  }
}
