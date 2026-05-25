// Models for SavvyWater Phase 6: notifications, audit, analytics

export interface WaterNotification {
  id: string;
  type: string;
  title: string;
  body: string | null;
  link: string | null;
  read_at: string | null;
  created_at: string;
}

export interface UnreadCount {
  unread: number;
}

// Audit
export interface WaterAuditEntry {
  id: string;
  actor_user_id: string | null;
  actor_name: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  created_at: string;
}

// Analytics
export interface MonthlyPoint {
  month: string;
  amount: string;
  count: number;
}

export interface StratumStat {
  stratum: number | null;
  subscribers: number;
  avg_consumption_cubic: string;
  total_billed: string;
}

export interface NeighborhoodStat {
  neighborhood: string | null;
  subscribers: number;
  open_balance: string;
}

export interface TopDebtor {
  subscriber_id: string;
  code: string;
  name: string;
  days_overdue: number;
  balance: string;
}

export interface WaterAnalyticsResponse {
  billed_trend: MonthlyPoint[];
  collected_trend: MonthlyPoint[];
  consumption_trend: MonthlyPoint[];
  by_stratum: StratumStat[];
  by_neighborhood: NeighborhoodStat[];
  top_debtors: TopDebtor[];
  new_subscribers_last_30d: number;
  avg_collection_per_day: string;
  collection_rate: string;
}
