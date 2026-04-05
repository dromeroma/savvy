export interface SavvyApp {
  code: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  is_active: boolean;
}

export interface MyApp {
  app: SavvyApp;
  role: string;
  status: string;
  activated_at: string;
  trial_ends_at: string | null;
}
