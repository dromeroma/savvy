import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type ThemeMode = 'light' | 'dark' | 'fun';

export interface FunPalette {
  id: string;
  label: string;
  primary: string;
  accent: string;
  bg: string;
  isDark: boolean;
  brandScale: Record<string, string>;
  surfaceScale: Record<string, string>;
}

export const FUN_PALETTES: FunPalette[] = [
  {
    id: 'tropical',
    label: 'Tropical',
    primary: '#f97316',
    accent: '#fbbf24',
    bg: '#fffbeb',
    isDark: false,
    brandScale: {
      '25': '#fffcf0',
      '50': '#fff8e1',
      '100': '#ffecb3',
      '200': '#ffe082',
      '300': '#ffd54f',
      '400': '#ffca28',
      '500': '#f97316',
      '600': '#ea580c',
      '700': '#c2410c',
      '800': '#9a3412',
      '900': '#7c2d12',
      '950': '#431407',
    },
    surfaceScale: {
      '25': '#fffdf7',
      '50': '#fffbeb',
      '100': '#fef3c7',
      '200': '#fde68a',
      '300': '#fcd34d',
      '400': '#fbbf24',
      '500': '#f59e0b',
      '600': '#d97706',
      '700': '#b45309',
      '800': '#92400e',
      '900': '#78350f',
      '950': '#451a03',
      dark: '#2d1600',
    },
  },
  {
    id: 'neon',
    label: 'Neon',
    primary: '#a855f7',
    accent: '#22d3ee',
    bg: '#0f0b1a',
    isDark: true,
    brandScale: {
      '25': '#faf5ff',
      '50': '#f5f3ff',
      '100': '#ede9fe',
      '200': '#ddd6fe',
      '300': '#c4b5fd',
      '400': '#a78bfa',
      '500': '#a855f7',
      '600': '#9333ea',
      '700': '#7e22ce',
      '800': '#6b21a8',
      '900': '#581c87',
      '950': '#3b0764',
    },
    surfaceScale: {
      '25': '#fcfcfd',
      '50': '#1a1625',
      '100': '#1e1a2e',
      '200': '#2a2440',
      '300': '#3d3558',
      '400': '#6b5f8a',
      '500': '#8b7fb0',
      '600': '#a89ccc',
      '700': '#c5bae0',
      '800': '#ddd6f0',
      '900': '#ede9fa',
      '950': '#f5f3ff',
      dark: '#0f0b1a',
    },
  },
  {
    id: 'sunset',
    label: 'Sunset',
    primary: '#e11d48',
    accent: '#fb923c',
    bg: '#fff1f2',
    isDark: false,
    brandScale: {
      '25': '#fff5f6',
      '50': '#fff1f2',
      '100': '#ffe4e6',
      '200': '#fecdd3',
      '300': '#fda4af',
      '400': '#fb7185',
      '500': '#e11d48',
      '600': '#be123c',
      '700': '#9f1239',
      '800': '#881337',
      '900': '#4c0519',
      '950': '#2e0311',
    },
    surfaceScale: {
      '25': '#fffcfc',
      '50': '#fff7f7',
      '100': '#ffeded',
      '200': '#ffdada',
      '300': '#ffbfc0',
      '400': '#d9878a',
      '500': '#a65a5e',
      '600': '#7a3a3e',
      '700': '#5e2428',
      '800': '#3d1518',
      '900': '#2a0e10',
      '950': '#1a0809',
      dark: '#1f0a0b',
    },
  },
  {
    id: 'ocean',
    label: 'Ocean',
    primary: '#0ea5e9',
    accent: '#2dd4bf',
    bg: '#0c1929',
    isDark: true,
    brandScale: {
      '25': '#f0f9ff',
      '50': '#e0f2fe',
      '100': '#bae6fd',
      '200': '#7dd3fc',
      '300': '#38bdf8',
      '400': '#0ea5e9',
      '500': '#0284c7',
      '600': '#0369a1',
      '700': '#075985',
      '800': '#0c4a6e',
      '900': '#082f49',
      '950': '#051e31',
    },
    surfaceScale: {
      '25': '#fcfdfe',
      '50': '#0e1e33',
      '100': '#122640',
      '200': '#1a3452',
      '300': '#284a6e',
      '400': '#4a7094',
      '500': '#6d93b4',
      '600': '#90b3d0',
      '700': '#b3d0e5',
      '800': '#d1e6f3',
      '900': '#e8f3fa',
      '950': '#f0f9ff',
      dark: '#0c1929',
    },
  },
  {
    id: 'candy',
    label: 'Candy',
    primary: '#ec4899',
    accent: '#8b5cf6',
    bg: '#fdf2f8',
    isDark: false,
    brandScale: {
      '25': '#fef5fa',
      '50': '#fdf2f8',
      '100': '#fce7f3',
      '200': '#fbcfe8',
      '300': '#f9a8d4',
      '400': '#f472b6',
      '500': '#ec4899',
      '600': '#db2777',
      '700': '#be185d',
      '800': '#9d174d',
      '900': '#831843',
      '950': '#500724',
    },
    surfaceScale: {
      '25': '#fefcfd',
      '50': '#fef7fb',
      '100': '#feedf5',
      '200': '#fdd8ea',
      '300': '#fbbdd7',
      '400': '#d48aa6',
      '500': '#a35e78',
      '600': '#7a3e56',
      '700': '#5c2840',
      '800': '#3d1829',
      '900': '#290f1c',
      '950': '#1a0811',
      dark: '#1f0a14',
    },
  },
  {
    id: 'forest',
    label: 'Forest',
    primary: '#16a34a',
    accent: '#84cc16',
    bg: '#0a1f0e',
    isDark: true,
    brandScale: {
      '25': '#f0fdf4',
      '50': '#dcfce7',
      '100': '#bbf7d0',
      '200': '#86efac',
      '300': '#4ade80',
      '400': '#22c55e',
      '500': '#16a34a',
      '600': '#15803d',
      '700': '#166534',
      '800': '#14532d',
      '900': '#052e16',
      '950': '#022c22',
    },
    surfaceScale: {
      '25': '#fcfefa',
      '50': '#0f2914',
      '100': '#14331a',
      '200': '#1e4525',
      '300': '#2f6138',
      '400': '#508a5a',
      '500': '#72a87c',
      '600': '#95c49e',
      '700': '#b5dbbe',
      '800': '#d3edda',
      '900': '#e9f7ec',
      '950': '#f0fdf4',
      dark: '#0a1f0e',
    },
  },
  {
    id: 'lava',
    label: 'Lava',
    primary: '#dc2626',
    accent: '#f97316',
    bg: '#1a0a0a',
    isDark: true,
    brandScale: {
      '25': '#fff5f5',
      '50': '#fef2f2',
      '100': '#fee2e2',
      '200': '#fecaca',
      '300': '#fca5a5',
      '400': '#f87171',
      '500': '#dc2626',
      '600': '#b91c1c',
      '700': '#991b1b',
      '800': '#7f1d1d',
      '900': '#450a0a',
      '950': '#2a0505',
    },
    surfaceScale: {
      '25': '#fefcfc',
      '50': '#241010',
      '100': '#2e1515',
      '200': '#401e1e',
      '300': '#5c2e2e',
      '400': '#8a5050',
      '500': '#a87272',
      '600': '#c49595',
      '700': '#dbb5b5',
      '800': '#edd3d3',
      '900': '#f7e9e9',
      '950': '#fef2f2',
      dark: '#1a0a0a',
    },
  },
];

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private modeSubject = new BehaviorSubject<ThemeMode>(this.loadMode());
  private paletteSubject = new BehaviorSubject<FunPalette>(this.loadPalette());

  mode$ = this.modeSubject.asObservable();
  palette$ = this.paletteSubject.asObservable();

  get currentMode(): ThemeMode {
    return this.modeSubject.value;
  }

  get currentPalette(): FunPalette {
    return this.paletteSubject.value;
  }

  constructor() {
    this.applyMode();
  }

  toggleTheme(): void {
    const order: ThemeMode[] = ['light', 'dark', 'fun'];
    const idx = order.indexOf(this.currentMode);
    const next = order[(idx + 1) % order.length];
    this.modeSubject.next(next);
    localStorage.setItem('theme-mode', next);
    this.applyMode();
  }

  selectPalette(palette: FunPalette): void {
    this.paletteSubject.next(palette);
    localStorage.setItem('theme-palette', palette.id);
    if (this.currentMode === 'fun') {
      this.applyMode();
    }
  }

  applyMode(): void {
    const mode = this.currentMode;
    const html = document.documentElement;

    // Clear previous state
    html.classList.remove('dark');
    html.classList.remove('fun-mode');
    this.clearOverrides();

    if (mode === 'dark') {
      html.classList.add('dark');
    } else if (mode === 'fun') {
      const palette = this.currentPalette;
      html.classList.add('fun-mode');

      if (palette.isDark) {
        html.classList.add('dark');
      }

      this.applyOverrides(palette);
    }
  }

  private applyOverrides(palette: FunPalette): void {
    const root = document.documentElement;

    // Brand scale
    for (const [key, value] of Object.entries(palette.brandScale)) {
      root.style.setProperty(`--color-brand-${key}`, value);
    }

    // Surface scale → gray overrides
    for (const [key, value] of Object.entries(palette.surfaceScale)) {
      root.style.setProperty(`--color-gray-${key}`, value);
    }

    // Focus ring with palette primary
    root.style.setProperty(
      '--shadow-focus-ring',
      `0px 0px 0px 4px ${palette.primary}3d`
    );
  }

  private clearOverrides(): void {
    const root = document.documentElement;
    const keys = [
      '25', '50', '100', '200', '300', '400', '500',
      '600', '700', '800', '900', '950',
    ];

    for (const key of keys) {
      root.style.removeProperty(`--color-brand-${key}`);
      root.style.removeProperty(`--color-gray-${key}`);
    }

    root.style.removeProperty('--color-gray-dark');
    root.style.removeProperty('--shadow-focus-ring');
  }

  private loadMode(): ThemeMode {
    const stored = localStorage.getItem('theme-mode');
    if (stored === 'light' || stored === 'dark' || stored === 'fun') {
      return stored;
    }
    return 'light';
  }

  private loadPalette(): FunPalette {
    const storedId = localStorage.getItem('theme-palette');
    return FUN_PALETTES.find((p) => p.id === storedId) || FUN_PALETTES[0];
  }
}
