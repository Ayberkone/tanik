import { expect, test } from '@playwright/test'

import { FIXTURE_PNG } from './fixtures'

test('fingerprint enroll: file upload + successful response renders the result panel', async ({ page }) => {
  await page.route('**/api/v1/fingerprint/enroll', async (route) => {
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-fp-enroll-1',
        subject_id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
        display_name: 'Bob',
        finger_position: 'right_thumb',
        enrolled_at: '2026-04-25T18:10:00+00:00',
        modality: 'fingerprint',
        template_version: 'sourceafis/3.18.1',
      }),
    })
  })

  await page.goto('/fingerprint/enroll')

  await page.getByLabel(/Display name/i).fill('Bob')
  await page.getByLabel(/Finger position/i).selectOption('right_thumb')
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)

  await page.getByRole('button', { name: /^Enroll$/ }).click()

  await expect(page.getByText('Enrollment created.')).toBeVisible()
  await expect(page.getByText('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')).toBeVisible()
  await expect(page.getByText('sourceafis/3.18.1')).toBeVisible()
  await expect(page.getByText('right_thumb')).toBeVisible()
  await expect(page.getByRole('link', { name: /Verify this subject/i })).toHaveAttribute(
    'href',
    /\/fingerprint\/verify\?subject_id=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/,
  )
})

test('fingerprint enroll: server returns PIPELINE_FAILURE → error panel with code', async ({ page }) => {
  await page.route('**/api/v1/fingerprint/enroll', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-fp-fail-1',
        error_code: 'PIPELINE_FAILURE',
        message: 'Fingerprint pipeline failed: no minutiae detected',
        details: { stage: 'encode' },
      }),
    })
  })

  await page.goto('/fingerprint/enroll')
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Enroll$/ }).click()

  await expect(page.getByText('PIPELINE_FAILURE')).toBeVisible()
  await expect(page.getByText(/no minutiae detected/)).toBeVisible()
  await expect(page.getByRole('button', { name: /Try again/i })).toBeVisible()
})
