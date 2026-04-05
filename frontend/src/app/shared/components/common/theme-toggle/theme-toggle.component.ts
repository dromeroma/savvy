import { Component, ElementRef, HostListener, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThemeService, FUN_PALETTES, FunPalette } from '../../../services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  imports: [CommonModule],
  templateUrl: './theme-toggle.component.html',
})
export class ThemeToggleComponent {
  mode$;
  palette$;
  palettes = FUN_PALETTES;
  showPicker = false;

  @ViewChild('pickerContainer', { static: false }) pickerContainer!: ElementRef;
  @ViewChild('toggleBtn', { static: false }) toggleBtn!: ElementRef;

  constructor(private themeService: ThemeService) {
    this.mode$ = this.themeService.mode$;
    this.palette$ = this.themeService.palette$;
  }

  onToggleClick(): void {
    const current = this.themeService.currentMode;

    if (current === 'fun') {
      if (this.showPicker) {
        this.showPicker = false;
        this.themeService.toggleTheme(); // fun -> light
      } else {
        this.showPicker = true;
      }
    } else {
      this.themeService.toggleTheme();
      // If entering fun (coming from dark), open picker
      if (current === 'dark') {
        this.showPicker = true;
      }
    }
  }

  selectPalette(palette: FunPalette): void {
    this.themeService.selectPalette(palette);
    this.showPicker = false;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.showPicker) return;
    const target = event.target as Node;
    const pickerEl = this.pickerContainer?.nativeElement;
    const btnEl = this.toggleBtn?.nativeElement;
    if (pickerEl && !pickerEl.contains(target) && btnEl && !btnEl.contains(target)) {
      this.showPicker = false;
    }
  }
}
