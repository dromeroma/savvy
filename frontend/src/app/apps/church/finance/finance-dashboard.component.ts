import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';
import { DatePickerComponent } from '../../../shared/components/form/date-picker/date-picker.component';

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
  imports: [FormsModule, DatePickerComponent],
  templateUrl: './finance-dashboard.component.html',
})
export class FinanceDashboardComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);

  activeTab = signal<'income' | 'expenses'>('income');
  transactions = signal<Transaction[]>([]);
  incomeCategories = signal<Category[]>([]);
  expenseCategories = signal<Category[]>([]);
  loading = signal(true);

  // Modal
  showModal = signal<'income' | 'expense' | null>(null);
  saving = signal(false);
  incomeForm = { category_code: '', amount: '', date: '', payment_method: 'cash', description: '', person_id: '' };
  expenseForm = { category_code: '', amount: '', date: '', payment_method: 'cash', description: '', vendor: '' };

  // Person search
  personSearch = '';
  searchResults = signal<any[]>([]);
  selectedPerson = signal<any>(null);
  showSearchDropdown = signal(false);
  searchingPeople = signal(false);
  private searchSubject = new Subject<string>();
  private searchSubscription?: Subscription;

  ngOnInit(): void {
    this.loadCategories();
    this.loadTransactions();

    this.searchSubscription = this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((query) => {
        if (!query || query.length < 2) {
          this.searchResults.set([]);
          this.showSearchDropdown.set(false);
          this.searchingPeople.set(false);
          return [];
        }
        this.searchingPeople.set(true);
        return this.api.get<any>('/church/congregants', { search: query, page_size: 5 });
      }),
    ).subscribe({
      next: (res) => {
        const items = Array.isArray(res) ? res : (res?.items ?? []);
        this.searchResults.set(items);
        this.showSearchDropdown.set(true);
        this.searchingPeople.set(false);
      },
      error: () => {
        this.searchResults.set([]);
        this.searchingPeople.set(false);
      },
    });
  }

  ngOnDestroy(): void {
    this.searchSubscription?.unsubscribe();
  }

  onPersonSearchInput(): void {
    this.searchSubject.next(this.personSearch);
  }

  selectPerson(person: any): void {
    this.selectedPerson.set(person);
    this.incomeForm.person_id = person.id;
    this.personSearch = '';
    this.searchResults.set([]);
    this.showSearchDropdown.set(false);
  }

  clearPerson(): void {
    this.selectedPerson.set(null);
    this.incomeForm.person_id = '';
    this.personSearch = '';
    this.searchResults.set([]);
    this.showSearchDropdown.set(false);
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

    this.api.get<any>(endpoint).subscribe({
      next: (data) => {
        // Backend returns {items, total} or flat array depending on endpoint
        const items = Array.isArray(data) ? data : (data.items ?? []);
        this.transactions.set(items);
        this.loading.set(false);
      },
      error: () => {
        this.transactions.set([]);
        this.loading.set(false);
      },
    });
  }

  openIncomeModal(): void {
    this.incomeForm = { category_code: '', amount: '', date: new Date().toISOString().slice(0, 10), payment_method: 'cash', description: '', person_id: '' };
    this.clearPerson();
    this.showModal.set('income');
  }

  openExpenseModal(): void {
    this.expenseForm = { category_code: '', amount: '', date: new Date().toISOString().slice(0, 10), payment_method: 'cash', description: '', vendor: '' };
    this.showModal.set('expense');
  }

  closeModal(): void {
    this.showModal.set(null);
    this.clearPerson();
  }

  saveIncome(): void {
    this.saving.set(true);
    const body: Record<string, any> = {
      category_code: this.incomeForm.category_code,
      amount: parseFloat(this.incomeForm.amount),
      date: this.incomeForm.date,
      payment_method: this.incomeForm.payment_method,
      description: this.incomeForm.description || null,
    };
    if (this.incomeForm.person_id) {
      body['person_id'] = this.incomeForm.person_id;
    }
    this.api.post('/church/finance/income', body).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeModal();
        this.activeTab.set('income');
        this.loadTransactions();
      },
      error: (err) => {
        this.saving.set(false);
        console.error('Income creation error:', err);
        console.error('Body sent:', body);
      },
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
