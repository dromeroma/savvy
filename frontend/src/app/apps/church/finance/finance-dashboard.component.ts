import { Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';

interface Transaction {
  id: string;
  category_id: string;
  amount: number;
  description: string;
  date: string;
  payment_method: string;
  vendor?: string;
}

interface Category {
  id: string;
  name: string;
  code: string;
}

@Component({
  selector: 'app-finance-dashboard',
  imports: [FormsModule],
  templateUrl: './finance-dashboard.component.html',
})
export class FinanceDashboardComponent implements OnInit {
  private readonly api = inject(ApiService);

  activeTab = signal<'income' | 'expenses'>('income');
  transactions = signal<Transaction[]>([]);
  incomeCategories = signal<Category[]>([]);
  expenseCategories = signal<Category[]>([]);
  loading = signal(true);

  // Modal
  showModal = signal<'income' | 'expense' | null>(null);
  saving = signal(false);
  incomeForm = { category_code: '', amount: '', date: '', payment_method: 'cash', description: '' };
  expenseForm = { category_code: '', amount: '', date: '', payment_method: 'cash', description: '', vendor: '' };

  ngOnInit(): void {
    this.loadCategories();
    this.loadTransactions();
  }

  loadCategories(): void {
    this.api.get<Category[]>('/church/finance/categories/income').subscribe({
      next: (cats) => this.incomeCategories.set(cats),
    });
    this.api.get<Category[]>('/church/finance/categories/expenses').subscribe({
      next: (cats) => this.expenseCategories.set(cats),
    });
  }

  setTab(tab: 'income' | 'expenses'): void {
    this.activeTab.set(tab);
    this.loadTransactions();
  }

  loadTransactions(): void {
    this.loading.set(true);
    const endpoint = this.activeTab() === 'income' ? '/church/finance/income' : '/church/finance/expenses';

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

  openIncomeModal(): void {
    this.incomeForm = { category_code: '', amount: '', date: new Date().toISOString().slice(0, 10), payment_method: 'cash', description: '' };
    this.showModal.set('income');
  }

  openExpenseModal(): void {
    this.expenseForm = { category_code: '', amount: '', date: new Date().toISOString().slice(0, 10), payment_method: 'cash', description: '', vendor: '' };
    this.showModal.set('expense');
  }

  closeModal(): void {
    this.showModal.set(null);
  }

  saveIncome(): void {
    this.saving.set(true);
    this.api.post('/church/finance/income', {
      category_code: this.incomeForm.category_code,
      amount: parseFloat(this.incomeForm.amount),
      date: this.incomeForm.date,
      payment_method: this.incomeForm.payment_method,
      description: this.incomeForm.description || null,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeModal();
        this.activeTab.set('income');
        this.loadTransactions();
      },
      error: () => this.saving.set(false),
    });
  }

  saveExpense(): void {
    this.saving.set(true);
    this.api.post('/church/finance/expenses', {
      category_code: this.expenseForm.category_code,
      amount: parseFloat(this.expenseForm.amount),
      date: this.expenseForm.date,
      payment_method: this.expenseForm.payment_method,
      description: this.expenseForm.description || null,
      vendor: this.expenseForm.vendor || null,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeModal();
        this.activeTab.set('expenses');
        this.loadTransactions();
      },
      error: () => this.saving.set(false),
    });
  }

  getCategoryName(catId: string): string {
    const all = [...this.incomeCategories(), ...this.expenseCategories()];
    return all.find(c => c.id === catId)?.name ?? catId;
  }
}
