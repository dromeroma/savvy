import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { ThemeService, ThemeMode, FunPalette, FUN_PALETTES } from '../../../services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  imports: [CommonModule],
  templateUrl: './theme-toggle.component.html',
})
export class ThemeToggleComponent implements OnInit, OnDestroy {
  private readonly themeService = inject(ThemeService);
  private subs: Subscription[] = [];

  mode: ThemeMode = 'light';
  palette!: FunPalette;
  palettes = FUN_PALETTES;
  showPalettePicker = false;

  ngOnInit() {
    this.subs.push(
      this.themeService.mode$.subscribe(m => this.mode = m),
      this.themeService.palette$.subscribe(p => this.palette = p),
    );
  }

  ngOnDestroy() {
    this.subs.forEach(s => s.unsubscribe());
  }

  toggleTheme() {
    this.themeService.toggleTheme();
    this.showPalettePicker = false;
  }

  togglePalettePicker() {
    this.showPalettePicker = !this.showPalettePicker;
  }

  selectPalette(p: FunPalette) {
    this.themeService.selectPalette(p);
    this.showPalettePicker = false;
  }
}
