import { defineConfig, devices } from '@playwright/test'

// Tests run against the Next dev server on port 3100 to avoid stomping on a
// manual dev session at 3000. Backend is intentionally unreachable
// (NEXT_PUBLIC_API_BASE_URL points at a closed port) — every backend
// interaction is mocked via page.route() so tests are deterministic and
// don't need uvicorn running. Backend correctness is covered by pytest.
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://localhost:3100',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev -- --port 3100',
    url: 'http://localhost:3100',
    env: {
      NEXT_PUBLIC_API_BASE_URL: 'http://localhost:9',
      NPM_CONFIG_CACHE: '/tmp/npm-cache-tanik',
    },
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Real synthetic camera + auto-granted permission so the
        // WebcamCapture component can be exercised in headless e2e
        // without touching a physical device.
        permissions: ['camera'],
        launchOptions: {
          args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
          ],
        },
      },
    },
  ],
})
