import { defineConfig, devices } from '@playwright/test';

/**
 * Smoke E2E. Requiere:
 *   npm i -D @playwright/test && npx playwright install chromium
 * y una instancia corriendo (frontend + backend). Configura la URL base con
 * PLAYWRIGHT_BASE_URL (por defecto http://localhost:4200).
 *
 * Credenciales opcionales para el flujo de login:
 *   E2E_EMAIL, E2E_PASSWORD
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
