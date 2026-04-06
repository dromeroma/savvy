import { Component, inject, signal, Output, EventEmitter, OnInit, OnDestroy, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Subject, Subscription, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ApiService } from '../../../../core/services/api.service';

interface GeoItem {
  id: number;
  name: string;
  code?: string;
}

export interface LocationSelection {
  country_id: number | null;
  country_name: string;
  state_id: number | null;
  state_name: string;
  city_id: number | null;
  city_name: string;
}

@Component({
  selector: 'app-location-selector',
  imports: [CommonModule, FormsModule],
  templateUrl: './location-selector.component.html',
})
export class LocationSelectorComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);

  @Input() initialCountry: string = '';
  @Input() initialState: string = '';
  @Input() initialCity: string = '';
  @Output() locationChange = new EventEmitter<LocationSelection>();

  // Country
  countrySearch = '';
  countries = signal<GeoItem[]>([]);
  selectedCountry = signal<GeoItem | null>(null);
  showCountryDropdown = signal(false);
  private countrySubject = new Subject<string>();
  private countrySub?: Subscription;

  // State
  stateSearch = '';
  states = signal<GeoItem[]>([]);
  selectedState = signal<GeoItem | null>(null);
  showStateDropdown = signal(false);
  private stateSubject = new Subject<string>();
  private stateSub?: Subscription;

  // City
  citySearch = '';
  cities = signal<GeoItem[]>([]);
  selectedCity = signal<GeoItem | null>(null);
  showCityDropdown = signal(false);
  private citySubject = new Subject<string>();
  private citySub?: Subscription;

  ngOnInit(): void {
    // Country search
    this.countrySub = this.countrySubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => q.length >= 2 ? this.api.get<GeoItem[]>('/geography/countries', { q }) : of([])),
    ).subscribe(items => {
      this.countries.set(items);
      this.showCountryDropdown.set(items.length > 0);
    });

    // State search
    this.stateSub = this.stateSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => {
        const c = this.selectedCountry();
        if (!c || q.length < 2) return of([]);
        return this.api.get<GeoItem[]>(`/geography/countries/${c.id}/states`, { q });
      }),
    ).subscribe(items => {
      this.states.set(items);
      this.showStateDropdown.set(items.length > 0);
    });

    // City search
    this.citySub = this.citySubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => {
        const s = this.selectedState();
        if (!s || q.length < 2) return of([]);
        return this.api.get<GeoItem[]>(`/geography/states/${s.id}/cities`, { q });
      }),
    ).subscribe(items => {
      this.cities.set(items);
      this.showCityDropdown.set(items.length > 0);
    });
  }

  ngOnDestroy(): void {
    this.countrySub?.unsubscribe();
    this.stateSub?.unsubscribe();
    this.citySub?.unsubscribe();
  }

  onCountryInput(): void { this.countrySubject.next(this.countrySearch); }
  onStateInput(): void { this.stateSubject.next(this.stateSearch); }
  onCityInput(): void { this.citySubject.next(this.citySearch); }

  selectCountry(item: GeoItem): void {
    this.selectedCountry.set(item);
    this.countrySearch = item.name;
    this.showCountryDropdown.set(false);
    // Reset state and city
    this.selectedState.set(null);
    this.stateSearch = '';
    this.selectedCity.set(null);
    this.citySearch = '';
    this.emit();
    // Pre-load states
    this.api.get<GeoItem[]>(`/geography/countries/${item.id}/states`).subscribe(s => this.states.set(s));
  }

  selectState(item: GeoItem): void {
    this.selectedState.set(item);
    this.stateSearch = item.name;
    this.showStateDropdown.set(false);
    // Reset city
    this.selectedCity.set(null);
    this.citySearch = '';
    this.emit();
    // Pre-load cities
    this.api.get<GeoItem[]>(`/geography/states/${item.id}/cities`).subscribe(c => this.cities.set(c));
  }

  selectCity(item: GeoItem): void {
    this.selectedCity.set(item);
    this.citySearch = item.name;
    this.showCityDropdown.set(false);
    this.emit();
  }

  clearCountry(): void {
    this.selectedCountry.set(null);
    this.countrySearch = '';
    this.selectedState.set(null);
    this.stateSearch = '';
    this.selectedCity.set(null);
    this.citySearch = '';
    this.emit();
  }

  clearState(): void {
    this.selectedState.set(null);
    this.stateSearch = '';
    this.selectedCity.set(null);
    this.citySearch = '';
    this.emit();
  }

  clearCity(): void {
    this.selectedCity.set(null);
    this.citySearch = '';
    this.emit();
  }

  onFocusCountry(): void {
    if (this.countries().length > 0 && !this.selectedCountry()) {
      this.showCountryDropdown.set(true);
    }
  }

  onFocusState(): void {
    if (this.selectedCountry() && this.states().length > 0 && !this.selectedState()) {
      this.showStateDropdown.set(true);
    }
  }

  onFocusCity(): void {
    if (this.selectedState() && this.cities().length > 0 && !this.selectedCity()) {
      this.showCityDropdown.set(true);
    }
  }

  private emit(): void {
    const c = this.selectedCountry();
    const s = this.selectedState();
    const ci = this.selectedCity();
    this.locationChange.emit({
      country_id: c?.id ?? null,
      country_name: c?.name ?? '',
      state_id: s?.id ?? null,
      state_name: s?.name ?? '',
      city_id: ci?.id ?? null,
      city_name: ci?.name ?? '',
    });
  }
}
