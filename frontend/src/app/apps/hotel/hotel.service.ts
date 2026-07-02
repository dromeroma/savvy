import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface RoomType {
  id: string; code: string; name: string; capacity: number; base_rate: number;
  description?: string | null; amenities: string[]; status: string;
}
export interface Room {
  id: string; room_type_id: string; number: string; floor?: string | null;
  status: string; housekeeping_status: string; notes?: string | null; room_type_name?: string | null;
}
export interface AvailabilityRow {
  room_type_id: string; room_type_name: string; base_rate: number; total_rooms: number; available: number;
}
export interface Availability { check_in: string; check_out: string; nights: number; rows: AvailabilityRow[]; }
export interface Reservation {
  id: string; code: string; guest_name: string; guest_document?: string | null;
  guest_email?: string | null; guest_phone?: string | null;
  room_type_id: string; room_id?: string | null; check_in_date: string; check_out_date: string;
  nights: number; adults: number; children: number; rate: number; total: number;
  status: string; source: string; notes?: string | null;
  room_type_name?: string | null; room_number?: string | null; folio_balance?: number | null;
}
export interface FolioCharge { id: string; kind: string; description: string; quantity: number; unit_price: number; amount: number; charged_at: string; }
export interface FolioPayment { id: string; amount: number; method: string; reference?: string | null; paid_at: string; }
export interface Folio {
  id: string; reservation_id: string; status: string; total_charges: number;
  total_payments: number; balance: number; closed_at?: string | null;
  charges: FolioCharge[]; payments: FolioPayment[];
}
export interface HotelDashboard {
  total_rooms: number; occupied_rooms: number; occupancy_rate: number;
  arrivals_today: number; departures_today: number; in_house: number;
  adr: number; revpar: number; revenue_today: number; dirty_rooms: number;
}

@Injectable({ providedIn: 'root' })
export class HotelService {
  private readonly api = inject(ApiService);

  dashboard(): Observable<HotelDashboard> { return this.api.get('/hotel/dashboard'); }

  // Room types
  listRoomTypes(): Observable<RoomType[]> { return this.api.get('/hotel/room-types'); }
  createRoomType(b: Partial<RoomType>): Observable<RoomType> { return this.api.post('/hotel/room-types', b); }
  updateRoomType(id: string, b: Partial<RoomType>): Observable<RoomType> { return this.api.patch(`/hotel/room-types/${id}`, b); }

  // Rooms
  listRooms(): Observable<Room[]> { return this.api.get('/hotel/rooms'); }
  createRoom(b: Partial<Room>): Observable<Room> { return this.api.post('/hotel/rooms', b); }
  updateRoom(id: string, b: Partial<Room>): Observable<Room> { return this.api.patch(`/hotel/rooms/${id}`, b); }
  setHousekeeping(id: string, status: string): Observable<Room> { return this.api.post(`/hotel/rooms/${id}/housekeeping`, { housekeeping_status: status }); }

  // Availability
  availability(check_in: string, check_out: string): Observable<Availability> {
    return this.api.get('/hotel/availability', { check_in, check_out });
  }
  availableRooms(check_in: string, check_out: string, room_type_id?: string): Observable<Room[]> {
    const p: Record<string, string> = { check_in, check_out };
    if (room_type_id) p['room_type_id'] = room_type_id;
    return this.api.get('/hotel/available-rooms', p);
  }

  // Reservations
  listReservations(params?: Record<string, string>): Observable<Reservation[]> { return this.api.get('/hotel/reservations', params); }
  createReservation(b: Partial<Reservation>): Observable<Reservation> { return this.api.post('/hotel/reservations', b); }
  checkIn(id: string, room_id: string): Observable<Reservation> { return this.api.post(`/hotel/reservations/${id}/check-in`, { room_id }); }
  checkOut(id: string): Observable<Reservation> { return this.api.post(`/hotel/reservations/${id}/check-out`, {}); }
  cancel(id: string): Observable<Reservation> { return this.api.post(`/hotel/reservations/${id}/cancel`, {}); }
  noShow(id: string): Observable<Reservation> { return this.api.post(`/hotel/reservations/${id}/no-show`, {}); }

  // Folio
  getFolio(rid: string): Observable<Folio> { return this.api.get(`/hotel/reservations/${rid}/folio`); }
  addCharge(rid: string, b: { kind?: string; description: string; quantity: number; unit_price: number }): Observable<Folio> {
    return this.api.post(`/hotel/reservations/${rid}/folio/charges`, b);
  }
  chargeFromPos(rid: string, sale_id: string): Observable<Folio> { return this.api.post(`/hotel/reservations/${rid}/folio/charge-from-pos`, { sale_id }); }
  addPayment(rid: string, b: { amount: number; method: string; reference?: string }): Observable<Folio> {
    return this.api.post(`/hotel/reservations/${rid}/folio/payments`, b);
  }
}
