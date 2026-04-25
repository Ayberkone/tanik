import { expect, test } from '@playwright/test'

import { FIXTURE_PNG } from './fixtures'

const SUBJECT_ID = '11111111-2222-3333-4444-555555555555'

test('verify: matched response shows the success panel', async ({ page }) => {
  await page.route('**/api/v1/iris/verify', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-verify-ok',
        subject_id: SUBJECT_ID,
        modality: 'iris',
        matched: true,
        hamming_distance: 0.1234,
        threshold: 0.37,
        decision_at: '2026-04-25T18:00:01+00:00',
      }),
    })
  })

  await page.goto(`/verify?subject_id=${SUBJECT_ID}`)
  await expect(page.getByLabel(/Subject ID/i)).toHaveValue(SUBJECT_ID)

  await page.getByRole('tab', { name: /Upload file/i }).click()
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Verify$/ }).click()

  await expect(page.getByText(/Match — same iris/)).toBeVisible()
  await expect(page.getByText('0.1234')).toBeVisible()
  await expect(page.getByText('0.3700')).toBeVisible()
  await expect(page.getByText(SUBJECT_ID)).toBeVisible()
})

test('verify: not-matched response shows the no-match panel', async ({ page }) => {
  await page.route('**/api/v1/iris/verify', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-verify-no',
        subject_id: SUBJECT_ID,
        modality: 'iris',
        matched: false,
        hamming_distance: 0.4501,
        threshold: 0.37,
        decision_at: '2026-04-25T18:00:02+00:00',
      }),
    })
  })

  await page.goto(`/verify?subject_id=${SUBJECT_ID}`)
  await page.getByRole('tab', { name: /Upload file/i }).click()
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Verify$/ }).click()

  await expect(page.getByText(/No match — different iris/)).toBeVisible()
  await expect(page.getByText('0.4501')).toBeVisible()
})

test('verify: 404 SUBJECT_NOT_FOUND surfaces the error code', async ({ page }) => {
  await page.route('**/api/v1/iris/verify', async (route) => {
    await route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({
        request_id: 'rid-verify-404',
        error_code: 'SUBJECT_NOT_FOUND',
        message: 'No subject with id 00000000-0000-0000-0000-000000000000',
        details: null,
      }),
    })
  })

  await page.goto('/verify?subject_id=00000000-0000-0000-0000-000000000000')
  await page.getByRole('tab', { name: /Upload file/i }).click()
  await page.locator('input[type="file"]').setInputFiles(FIXTURE_PNG)
  await page.getByRole('button', { name: /^Verify$/ }).click()

  await expect(page.getByText('SUBJECT_NOT_FOUND')).toBeVisible()
  await expect(page.getByText(/No subject with id/)).toBeVisible()
})
