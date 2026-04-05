import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class SidebarService {
  private expandedSubject = new BehaviorSubject<boolean>(true);
  private mobileOpenSubject = new BehaviorSubject<boolean>(false);
  private hoveredSubject = new BehaviorSubject<boolean>(false);

  isExpanded$ = this.expandedSubject.asObservable();
  isMobileOpen$ = this.mobileOpenSubject.asObservable();
  isHovered$ = this.hoveredSubject.asObservable();

  toggleExpanded(): void {
    this.expandedSubject.next(!this.expandedSubject.value);
  }

  toggleMobileOpen(): void {
    this.mobileOpenSubject.next(!this.mobileOpenSubject.value);
  }

  closeMobile(): void {
    this.mobileOpenSubject.next(false);
  }

  setHovered(hovered: boolean): void {
    this.hoveredSubject.next(hovered);
  }

  get isExpanded(): boolean {
    return this.expandedSubject.value;
  }
}
