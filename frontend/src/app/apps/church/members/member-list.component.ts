import { Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';

interface Member {
  id: string;
  name: string;
  email: string;
  phone: string;
  status: string;
  membership_date: string;
}

interface PaginatedResponse {
  items: Member[];
  total: number;
  page: number;
  page_size: number;
}

@Component({
  selector: 'app-member-list',
  imports: [FormsModule],
  templateUrl: './member-list.component.html',
})
export class MemberListComponent implements OnInit {
  private readonly api = inject(ApiService);

  members = signal<Member[]>([]);
  loading = signal(true);
  total = signal(0);
  page = signal(1);
  pageSize = signal(20);
  search = '';
  statusFilter = '';

  ngOnInit(): void {
    this.loadMembers();
  }

  loadMembers(): void {
    this.loading.set(true);
    const params: Record<string, string | number> = {
      page: this.page(),
      page_size: this.pageSize(),
    };
    if (this.search) params['search'] = this.search;
    if (this.statusFilter) params['status'] = this.statusFilter;

    this.api.get<PaginatedResponse>('/church/members', params).subscribe({
      next: (res) => {
        this.members.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      },
    });
  }

  onSearch(): void {
    this.page.set(1);
    this.loadMembers();
  }

  onFilterChange(): void {
    this.page.set(1);
    this.loadMembers();
  }

  nextPage(): void {
    if (this.page() * this.pageSize() < this.total()) {
      this.page.update((p) => p + 1);
      this.loadMembers();
    }
  }

  prevPage(): void {
    if (this.page() > 1) {
      this.page.update((p) => p - 1);
      this.loadMembers();
    }
  }

  get totalPages(): number {
    return Math.ceil(this.total() / this.pageSize());
  }
}
