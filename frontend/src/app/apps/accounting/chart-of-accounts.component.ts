import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../shared/services/notification.service';

interface Account {
  id: string;
  code: string;
  name: string;
  type: string;
  parent_id: string | null;
  is_active: boolean;
  is_system: boolean;
}

interface TreeNode {
  account: Account;
  children: TreeNode[];
  expanded: boolean;
  level: number;
}

@Component({
  selector: 'app-chart-of-accounts',
  imports: [CommonModule, FormsModule],
  templateUrl: './chart-of-accounts.component.html',
})
export class ChartOfAccountsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly notify = inject(NotificationService);

  accounts = signal<Account[]>([]);
  tree = signal<TreeNode[]>([]);
  filteredTree = signal<TreeNode[]>([]);
  loading = signal(true);

  // Stats
  totalAccounts = signal(0);
  activeCount = signal(0);
  revenueCount = signal(0);
  expenseCount = signal(0);

  // Filters
  searchQuery = '';
  filterType = '';

  // Modal
  showCreateModal = signal(false);
  saving = signal(false);
  createForm = { code: '', name: '', type: 'asset', parent_id: '' };

  readonly accountTypes = [
    { value: 'asset', label: 'Activo' },
    { value: 'liability', label: 'Pasivo' },
    { value: 'equity', label: 'Patrimonio' },
    { value: 'revenue', label: 'Ingreso' },
    { value: 'expense', label: 'Gasto' },
  ];

  ngOnInit(): void {
    this.loadAccounts();
  }

  loadAccounts(): void {
    this.loading.set(true);
    this.api.get<Account[]>('/accounting/chart-of-accounts').subscribe({
      next: (data) => {
        this.accounts.set(data);
        this.computeStats(data);
        this.buildTree(data);
        this.applyFilters();
        this.loading.set(false);
      },
      error: () => {
        this.accounts.set([]);
        this.tree.set([]);
        this.filteredTree.set([]);
        this.loading.set(false);
        this.notify.show({ type: 'error', title: 'Error', message: 'No se pudo cargar el catálogo de cuentas' });
      },
    });
  }

  private computeStats(data: Account[]): void {
    this.totalAccounts.set(data.length);
    this.activeCount.set(data.filter(a => a.is_active).length);
    this.revenueCount.set(data.filter(a => a.type === 'revenue').length);
    this.expenseCount.set(data.filter(a => a.type === 'expense').length);
  }

  buildTree(accounts: Account[]): void {
    const map = new Map<string, TreeNode>();
    const roots: TreeNode[] = [];

    // Create nodes
    for (const a of accounts) {
      map.set(a.id, { account: a, children: [], expanded: false, level: 1 });
    }

    // Build hierarchy via parent_id
    for (const [id, node] of map) {
      if (node.account.parent_id && map.has(node.account.parent_id)) {
        const parent = map.get(node.account.parent_id)!;
        parent.children.push(node);
        node.level = parent.level + 1;
      } else {
        roots.push(node);
      }
    }

    // Sort children by code
    const sortFn = (a: TreeNode, b: TreeNode) => a.account.code.localeCompare(b.account.code);
    const sortTree = (nodes: TreeNode[]) => {
      nodes.sort(sortFn);
      nodes.forEach(n => sortTree(n.children));
    };
    sortTree(roots);

    // Expand level 1
    roots.forEach(r => r.expanded = true);
    this.tree.set(roots);
  }

  toggleExpand(node: TreeNode): void {
    node.expanded = !node.expanded;
  }

  applyFilters(): void {
    const query = this.searchQuery.trim().toLowerCase();
    const type = this.filterType;

    if (!query && !type) {
      this.filteredTree.set(this.tree());
      return;
    }

    const filterNodes = (nodes: TreeNode[]): TreeNode[] => {
      const result: TreeNode[] = [];
      for (const node of nodes) {
        const matchesSearch = !query ||
          node.account.code.toLowerCase().includes(query) ||
          node.account.name.toLowerCase().includes(query);
        const matchesType = !type || node.account.type === type;

        const filteredChildren = filterNodes(node.children);

        if ((matchesSearch && matchesType) || filteredChildren.length > 0) {
          result.push({
            ...node,
            children: filteredChildren,
            expanded: !!query || !!type || node.expanded,
          });
        }
      }
      return result;
    };

    this.filteredTree.set(filterNodes(this.tree()));
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  onTypeFilterChange(): void {
    this.applyFilters();
  }

  getLevelClasses(level: number): string {
    switch (level) {
      case 1: return 'font-bold text-base text-gray-900 dark:text-white';
      case 2: return 'font-semibold text-sm text-gray-800 dark:text-gray-200';
      case 3: return 'font-medium text-sm text-gray-700 dark:text-gray-300';
      default: return 'text-sm text-gray-600 dark:text-gray-400';
    }
  }

  getTypeBadgeClasses(type: string): string {
    switch (type) {
      case 'asset': return 'bg-blue-50 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400';
      case 'liability': return 'bg-red-50 text-red-700 dark:bg-red-500/20 dark:text-red-400';
      case 'equity': return 'bg-purple-50 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400';
      case 'revenue': return 'bg-green-50 text-green-700 dark:bg-green-500/20 dark:text-green-400';
      case 'expense': return 'bg-orange-50 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400';
      default: return 'bg-gray-50 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400';
    }
  }

  getTypeLabel(type: string): string {
    const found = this.accountTypes.find(t => t.value === type);
    return found ? found.label : type;
  }

  getIndentPx(level: number): string {
    return `${(level - 1) * 24}px`;
  }

  // Modal
  openCreateModal(): void {
    this.createForm = { code: '', name: '', type: 'asset', parent_id: '' };
    this.showCreateModal.set(true);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
  }

  saveAccount(): void {
    if (!this.createForm.code.trim() || !this.createForm.name.trim()) {
      this.notify.show({ type: 'warning', title: 'Campos requeridos', message: 'Código y nombre son obligatorios' });
      return;
    }

    this.saving.set(true);
    const payload: any = {
      code: this.createForm.code.trim(),
      name: this.createForm.name.trim(),
      type: this.createForm.type,
    };
    if (this.createForm.parent_id) {
      payload.parent_id = this.createForm.parent_id;
    }

    this.api.post<Account>('/accounting/chart-of-accounts', payload).subscribe({
      next: () => {
        this.notify.show({ type: 'success', title: 'Cuenta creada', message: `Cuenta ${payload.code} creada exitosamente` });
        this.saving.set(false);
        this.closeCreateModal();
        this.loadAccounts();
      },
      error: (err) => {
        const msg = err?.error?.detail || 'No se pudo crear la cuenta';
        this.notify.show({ type: 'error', title: 'Error', message: msg });
        this.saving.set(false);
      },
    });
  }
}
