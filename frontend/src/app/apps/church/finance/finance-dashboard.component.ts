import { Component, inject, signal, OnInit } from '@angular/core';
import { ApiService } from '../../../core/services/api.service';

interface Transaction {
  id: string;
  type: string;
  category: string;
  amount: number;
  description: string;
  date: string;
}

@Component({
  selector: 'app-finance-dashboard',
  imports: [],
  templateUrl: './finance-dashboard.component.html',
})
export class FinanceDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  activeTab = signal<'income' | 'expenses'>('income');
  transactions = signal<Transaction[]>([]);
  loading = signal(true);

  ngOnInit(): void {
    this.loadTransactions();
  }

  setTab(tab: 'income' | 'expenses'): void {
    this.activeTab.set(tab);
    this.loadTransactions();
  }

  loadTransactions(): void {
    this.loading.set(true);
    const endpoint =
      this.activeTab() === 'income'
        ? '/church/finance/income'
        : '/church/finance/expenses';

    this.api.get<Transaction[]>(endpoint).subscribe({
      next: (data) => {
        this.transactions.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.transactions.set([]);
        this.loading.set(false);
      },
    });
  }
}
