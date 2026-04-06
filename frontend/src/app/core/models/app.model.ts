export interface SavvyApp {
  code: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  is_active: boolean;
  is_external: boolean;
  external_url: string | null;
}

export interface MyApp {
  app: SavvyApp;
  role: string;
  status: string;
  activated_at: string;
  trial_ends_at: string | null;
}
