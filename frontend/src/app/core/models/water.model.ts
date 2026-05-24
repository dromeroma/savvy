export type SubscriberStatus = 'active' | 'suspended' | 'overdue' | 'retired';
export type SubscriberType = 'residential' | 'commercial' | 'industrial' | 'official';
export type MeterStatus = 'active' | 'replaced' | 'damaged' | 'inactive';

export interface WaterSubscriberListItem {
  id: string;
  code: string;
  first_name: string;
  last_name: string | null;
  business_name: string | null;
  document_number: string | null;
  address: string | null;
  neighborhood: string | null;
  subscriber_type: SubscriberType;
  status: SubscriberStatus;
  stratum: number | null;
  meter_count: number;
}

export interface WaterSubscriber {
  id: string;
  organization_id: string;
  code: string;
  document_type: string | null;
  document_number: string | null;
  first_name: string;
  last_name: string | null;
  business_name: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  address: string | null;
  neighborhood: string | null;
  city_id: number | null;
  stratum: number | null;
  subscriber_type: SubscriberType;
  status: SubscriberStatus;
  latitude: string | null;
  longitude: string | null;
  notes: string | null;
  registered_at: string | null;
  retired_at: string | null;
  user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaterSubscriberCreate {
  code: string;
  document_type?: string | null;
  document_number?: string | null;
  first_name: string;
  last_name?: string | null;
  business_name?: string | null;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  address?: string | null;
  neighborhood?: string | null;
  city_id?: number | null;
  stratum?: number | null;
  subscriber_type?: SubscriberType;
  status?: SubscriberStatus;
  notes?: string | null;
  registered_at?: string | null;
}

export interface WaterMeterListItem {
  id: string;
  serial_number: string;
  brand: string | null;
  model: string | null;
  diameter: string | null;
  status: MeterStatus;
  last_reading: string;
  last_reading_date: string | null;
  subscriber_id: string | null;
  subscriber_code: string | null;
  subscriber_name: string | null;
}

export interface WaterMeter {
  id: string;
  organization_id: string;
  subscriber_id: string | null;
  serial_number: string;
  brand: string | null;
  model: string | null;
  diameter: string | null;
  install_date: string | null;
  initial_reading: string;
  last_reading: string;
  last_reading_date: string | null;
  status: MeterStatus;
  location_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaterMeterCreate {
  subscriber_id?: string | null;
  serial_number: string;
  brand?: string | null;
  model?: string | null;
  diameter?: string | null;
  install_date?: string | null;
  initial_reading?: string;
  last_reading?: string;
  last_reading_date?: string | null;
  status?: MeterStatus;
  location_notes?: string | null;
}

export interface WaterDashboardKpis {
  total_subscribers: number;
  by_status: {
    active: number;
    suspended: number;
    overdue: number;
    retired: number;
  };
  total_meters: number;
  assigned_meters: number;
  unassigned_meters: number;
}
