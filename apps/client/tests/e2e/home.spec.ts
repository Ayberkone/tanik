import { expect, test } from '@playwright/test'

test('home page renders TANIK header and the four flow entry points', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'TANIK' })).toBeVisible()
  await expect(page.getByRole('link', { name: /Enroll iris/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Verify iris/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Enroll fingerprint/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Verify fingerprint/i })).toBeVisible()
})

test('home page surfaces "unreachable" when the backend is down', async ({ page }) => {
  // The dev server's NEXT_PUBLIC_API_BASE_URL points at a closed port,
  // so the server-render of /api/v1/health will always fail here.
  await page.goto('/')
  const status = page.getByLabel(/Inference service status/i)
  await expect(status).toContainText(/unreachable/i)
})
