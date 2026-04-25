import { expect, test } from '@playwright/test'

import { FIXTURE_PNG } from './fixtures'

const SUBJECT_ID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

test('fingerprint verify: matched response shows the success panel', async ({ page }) => {
  await page.route('**/api/v1/fingerprint/verify', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-fp-verify-ok',
        subject_id: SUBJECT_ID,
        modality: 'fingerprint',
        matched: true,
        similarity_score: 184.42,
        threshold: 40.0,
        decision_at: '2026-04-25T18:10:01+00:00',
      }),
    })
  })

  await page.goto(`/fingerprint/verify?subject_id=${SUBJECT_ID}`)
  await expect(page.getByLabel(/Subject ID/i)).toHaveValue(SUBJECT_ID)

  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Verify$/ }).click()

  await expect(page.getByText(/Match — same finger/)).toBeVisible()
  await expect(page.getByText('184.42')).toBeVisible()
  await expect(page.getByText('40.00')).toBeVisible()
  await expect(page.getByText(SUBJECT_ID)).toBeVisible()
})

test('fingerprint verify: not-matched response shows the no-match panel', async ({ page }) => {
  await page.route('**/api/v1/fingerprint/verify', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-fp-verify-no',
        subject_id: SUBJECT_ID,
        modality: 'fingerprint',
        matched: false,
        similarity_score: 12.34,
        threshold: 40.0,
        decision_at: '2026-04-25T18:10:02+00:00',
      }),
    })
  })

  await page.goto(`/fingerprint/verify?subject_id=${SUBJECT_ID}`)
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Verify$/ }).click()

  await expect(page.getByText(/No match — different finger/)).toBeVisible()
  await expect(page.getByText('12.34')).toBeVisible()
})

test('fingerprint verify: 404 SUBJECT_NOT_FOUND surfaces the error code', async ({ page }) => {
  await page.route('**/api/v1/fingerprint/verify', async (route) => {
    await route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-fp-verify-404',
        error_code: 'SUBJECT_NOT_FOUND',
        message: 'No fingerprint subject with id 00000000-0000-0000-0000-000000000000',
        details: null,
      }),
    })
  })

  await page.goto('/fingerprint/verify?subject_id=00000000-0000-0000-0000-000000000000')
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Verify$/ }).click()

  await expect(page.getByText('SUBJECT_NOT_FOUND')).toBeVisible()
  await expect(page.getByText(/No fingerprint subject with id/)).toBeVisible()
})
