import { test, expect } from '@playwright/test';

/**
 * Smoke E2E — flujos críticos mínimos para el go-live.
 * El flujo de login solo corre si E2E_EMAIL/E2E_PASSWORD están definidos.
 */

test('la app carga y redirige al login', async ({ page }) => {
  await page.goto('/');
  // Sin sesión, debe terminar en /auth/login (o mostrar el formulario de login).
  await expect(page).toHaveURL(/auth|login/i, { timeout: 15_000 });
});

test('la página de login renderiza sus campos', async ({ page }) => {
  await page.goto('/auth/login');
  await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
});

test('login + dashboard (si hay credenciales)', async ({ page }) => {
  const email = process.env.E2E_EMAIL;
  const password = process.env.E2E_PASSWORD;
  test.skip(!email || !password, 'Define E2E_EMAIL y E2E_PASSWORD para el flujo de login.');

  await page.goto('/auth/login');
  await page.fill('input[type="email"], input[name="email"]', email!);
  await page.fill('input[type="password"]', password!);
  await page.click('button[type="submit"]');

  // Tras login, debe salir de /auth (al dashboard o selector de org).
  await expect(page).not.toHaveURL(/auth\/login/i, { timeout: 20_000 });
});

test('la barra Savvy Command (⌘K) abre con el atajo', async ({ page }) => {
  const email = process.env.E2E_EMAIL;
  const password = process.env.E2E_PASSWORD;
  test.skip(!email || !password, 'Requiere sesión.');

  await page.goto('/auth/login');
  await page.fill('input[type="email"], input[name="email"]', email!);
  await page.fill('input[type="password"]', password!);
  await page.click('button[type="submit"]');
  await page.waitForURL((u) => !/auth\/login/i.test(u.toString()), { timeout: 20_000 });

  await page.keyboard.press('Control+k');
  await expect(page.locator('input[placeholder*="Busca"]')).toBeVisible({ timeout: 5_000 });
});
