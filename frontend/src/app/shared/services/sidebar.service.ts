import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class SidebarService {
  private expandedSubject = new BehaviorSubject<boolean>(true);
  private mobileOpenSubject = new BehaviorSubject<boolean>(false);
  private hoveredSubject = new BehaviorSubject<boolean>(false);
  private headerHiddenSubject = new BehaviorSubject<boolean>(false);

  isExpanded$ = this.expandedSubject.asObservable();
  isMobileOpen$ = this.mobileOpenSubject.asObservable();
  isHovered$ = this.hoveredSubject.asObservable();
  headerHidden$ = this.headerHiddenSubject.asObservable();

  toggleExpanded(): void {
    this.expandedSubject.next(!this.expandedSubject.value);
  }

  setExpanded(val: boolean): void {
    this.expandedSubject.next(val);
  }

  toggleMobileOpen(): void {
    this.mobileOpenSubject.next(!this.mobileOpenSubject.value);
  }

  setMobileOpen(val: boolean): void {
    this.mobileOpenSubject.next(val);
  }

  closeMobile(): void {
    this.mobileOpenSubject.next(false);
  }

  setHovered(hovered: boolean): void {
    this.hoveredSubject.next(hovered);
  }

  setHeaderHidden(val: boolean): void {
    this.headerHiddenSubject.next(val);
  }

  toggleHeaderHidden(): void {
    this.headerHiddenSubject.next(!this.headerHiddenSubject.value);
  }

  get isExpanded(): boolean {
    return this.expandedSubject.value;
  }

  get isHeaderHidden(): boolean {
    return this.headerHiddenSubject.value;
  }
}
