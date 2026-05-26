export type MemorialServiceStatus =
  | 'iniciado' | 'en_proceso' | 'pendiente' | 'finalizado' | 'cancelado';

export type MemorialServiceType =
  | 'velacion' | 'cremacion' | 'entierro'
  | 'velacion_cremacion' | 'velacion_entierro'
  | 'velacion_cremacion_entierro';

export interface MemorialFamilyMember {
  id: string;
  service_id: string;
  first_name: string;
  last_name: string | null;
  document_type: string | null;
  document_number: string | null;
  relationship: string | null;
  phone: string | null;
  mobile: string | null;
  email: string | null;
  address: string | null;
  is_primary: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface MemorialFamilyMemberCreate {
  first_name: string;
  last_name?: string | null;
  document_type?: string | null;
  document_number?: string | null;
  relationship?: string | null;
  phone?: string | null;
  mobile?: string | null;
  email?: string | null;
  address?: string | null;
  is_primary?: boolean;
  notes?: string | null;
}

export interface MemorialServiceListItem {
  id: string;
  code: string;
  consecutive: number;
  deceased_name: string;
  deceased_death_date: string;
  service_type: MemorialServiceType;
  status: MemorialServiceStatus;
  estimated_total: string;
  final_total: string;
  primary_family_name: string | null;
  primary_family_phone: string | null;
  family_count: number;
  created_at: string;
}

export interface MemorialService {
  id: string;
  organization_id: string;
  code: string;
  consecutive: number;

  deceased_first_name: string;
  deceased_last_name: string | null;
  deceased_document_type: string | null;
  deceased_document_number: string | null;
  deceased_birth_date: string | null;
  deceased_death_date: string;
  deceased_death_time: string | null;
  deceased_death_cause: string | null;
  deceased_death_place: string | null;

  service_type: MemorialServiceType;
  status: MemorialServiceStatus;

  velation_start_at: string | null;
  velation_end_at: string | null;
  velation_location: string | null;

  cremation_at: string | null;
  cremation_location: string | null;

  burial_at: string | null;
  burial_cemetery: string | null;
  burial_section: string | null;

  mass_at: string | null;
  mass_church: string | null;

  estimated_total: string;
  final_total: string;

  exequial_contract_id: string | null;
  notes: string | null;
  closed_at: string | null;
  closed_by: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;

  family_members: MemorialFamilyMember[];
}

export interface MemorialServiceCreate {
  deceased_first_name: string;
  deceased_last_name?: string | null;
  deceased_document_type?: string | null;
  deceased_document_number?: string | null;
  deceased_birth_date?: string | null;
  deceased_death_date: string;
  deceased_death_time?: string | null;
  deceased_death_cause?: string | null;
  deceased_death_place?: string | null;

  service_type: MemorialServiceType;
  status?: MemorialServiceStatus;

  velation_start_at?: string | null;
  velation_end_at?: string | null;
  velation_location?: string | null;

  cremation_at?: string | null;
  cremation_location?: string | null;

  burial_at?: string | null;
  burial_cemetery?: string | null;
  burial_section?: string | null;

  mass_at?: string | null;
  mass_church?: string | null;

  estimated_total?: string | number;
  final_total?: string | number;

  notes?: string | null;
  family_members?: MemorialFamilyMemberCreate[];
}

export interface MemorialServiceEvent {
  id: string;
  service_id: string;
  event_type: string;
  body: string | null;
  event_data: Record<string, unknown> | null;
  actor_user_id: string | null;
  created_at: string;
}

export interface MemorialDashboardKpis {
  services_total: number;
  services_active: number;
  services_closed: number;
  services_today: number;
  services_by_status: Record<string, number>;
}
