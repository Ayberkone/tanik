import { expect, test } from '@playwright/test'

import { FIXTURE_PNG } from './fixtures'

test('enroll: file upload + successful response renders the result panel', async ({ page }) => {
  await page.route('**/api/v1/iris/enroll', async (route) => {
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-enroll-1',
        subject_id: '11111111-2222-3333-4444-555555555555',
        display_name: 'Alice',
        eye_side: 'left',
        enrolled_at: '2026-04-25T18:00:00+00:00',
        modality: 'iris',
        template_version: 'open-iris/1.11.1',
      }),
    })
  })

  await page.goto('/enroll')

  await page.getByLabel(/Display name/i).fill('Alice')

  // Switch to file upload (avoid the camera path in headless e2e).
  await page.getByRole('tab', { name: /Upload file/i }).click()
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)

  await page.getByRole('button', { name: /^Enroll$/ }).click()

  await expect(page.getByText('Enrollment created.')).toBeVisible()
  await expect(page.getByText('11111111-2222-3333-4444-555555555555')).toBeVisible()
  await expect(page.getByText('open-iris/1.11.1')).toBeVisible()
  await expect(page.getByRole('link', { name: /Verify this subject/i })).toHaveAttribute(
    'href',
    /subject_id=11111111-2222-3333-4444-555555555555/,
  )
})

test('enroll: server returns INVALID_IMAGE → error panel with code', async ({ page }) => {
  await page.route('**/api/v1/iris/enroll', async (route) => {
    await route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-fail-1',
        error_code: 'INVALID_IMAGE',
        message: 'Could not determine file type from content',
        details: null,
      }),
    })
  })

  await page.goto('/enroll')
  await page.getByRole('tab', { name: /Upload file/i }).click()
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Enroll$/ }).click()

  await expect(page.getByText('INVALID_IMAGE')).toBeVisible()
  await expect(page.getByText(/Could not determine file type/)).toBeVisible()
  await expect(page.getByRole('button', { name: /Try again/i })).toBeVisible()
})
