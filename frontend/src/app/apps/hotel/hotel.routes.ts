import { Routes } from '@angular/router';
import { RouterOutlet } from '@angular/router';
import { Component } from '@angular/core';

@Component({ selector: 'app-hotel-layout', imports: [RouterOutlet], template: `<router-outlet />` })
export class HotelLayoutComponent {}

export const HOTEL_ROUTES: Routes = [
  { path: '', component: HotelLayoutComponent, children: [
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    { path: 'dashboard', loadComponent: () => import('./dashboard/hotel-dashboard.component').then(m => m.HotelDashboardComponent) },
    { path: 'reservations', loadComponent: () => import('./reservations/hotel-reservations.component').then(m => m.HotelReservationsComponent) },
    { path: 'rooms', loadComponent: () => import('./rooms/hotel-rooms.component').then(m => m.HotelRoomsComponent) },
    { path: 'housekeeping', loadComponent: () => import('./housekeeping/hotel-housekeeping.component').then(m => m.HotelHousekeepingComponent) },
  ]},
];
