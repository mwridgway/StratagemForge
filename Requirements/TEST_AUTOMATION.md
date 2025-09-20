# AGENT OPERATING MANUAL — Web Test Automation in VS Code

## 1) Mission
Build a maintainable automation test suite for a modern web app using Playwright and TypeScript inside VS Code. Ship fast feedback on every PR, deep coverage nightly, and useful artifacts for debugging.

## 2) Tech choices
- Language: TypeScript  
- Runner: Playwright test  
- Assertions: built in Playwright expect  
- Accessibility: axe-core automated checks on smoke journeys  
- Reporting: Allure reports plus JUnit XML for CI  
- Visual checks: Playwright screenshot diffs on critical pages  
- Package manager: pnpm or npm (use repo default)  
- Node version: read from `.nvmrc` if present, else use LTS  

## 3) Repo layout
```
/tests/e2e/                    end to end specs
/tests/fixtures/               data builders and test users
/tests/helpers/                custom matchers and utils
/tests/a11y/                   accessibility checks
/tests/config/                 playwright configs and env loaders
/.github/workflows/            CI pipelines
/.vscode/                      VS Code tasks and settings
```

## 4) Install and bootstrap
```bash
npm i -D @playwright/test
npx playwright install
npm i -D allure-playwright @axe-core/playwright
```

Playwright config lives in `tests/config/playwright.config.ts` with projects for Chromium, Firefox, and WebKit.  
Add VS Code settings (`.vscode/settings.json`) and tasks (`.vscode/tasks.json`) for quick smoke/full/UI runs.

## 5) Locator strategy
- Prefer `getByRole`, `getByLabel`, `getByText`.  
- Use `data-testid` attributes when semantics aren’t enough.  
- No brittle CSS selectors.  
- Encapsulate page structure with Page Objects in `tests/helpers/pages`.

## 6) Test authoring rules
- One spec = one user intent.  
- Name files by intent (`checkout.apply-coupon.spec.ts`).  
- Tag tests with `@smoke`, `@critical`, `@a11y`.  
- Record a trace on first retry. Artifacts under `reports/artifacts`.

Example:
```ts
test('@smoke user can log in', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.TEST_USER_EMAIL!);
  await page.getByLabel('Password').fill(process.env.TEST_USER_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## 7) Test data and environments
- Secrets via `.env` (never commit).  
- Hermetic data with API/SQL seeds.  
- `dataBuilder` utils for rich objects.  
- Env presets: `dev`, `staging`, `prod-like`.

## 8) Accessibility checks
Use `axe-core/playwright` in smoke journeys. Fail on serious/critical issues.

## 9) Visual checks
Golden snapshots per browser using Playwright’s `toHaveScreenshot`. Gate only stable screens.

## 10) Performance smoke
Tiny Lighthouse CI job for homepage + checkout. Budget LCP and CLS.

## 11) Flake control
- Never sleep. Always assert on conditions.  
- Stub noisy backend calls with `page.route`.  
- Retries = 2. Track flakes in Allure.

## 12) Reporting
- Allure results in `./allure-results`.  
- Upload Playwright traces, videos, screenshots on failure.  
- JUnit XML for CI dashboards.

## 13) CI workflow
GitHub Actions runs smoke on PRs, full cross-browser on merge, nightly deep runs.  
Artifacts uploaded for traces and Allure.

## 14) Definition of done
- Smoke < 5 min.  
- Critical journeys tagged and covered.  
- A11y scan per critical journey.  
- Visual snapshot coverage.  
- Playwright traces on all failures.  
- Allure report published.  
- README updated with run/debug instructions.

## 15) Developer ergonomics
- Playwright Test Explorer extension.  
- ESLint + TypeScript strict mode.  
- Code snippets for common Playwright patterns.

## 16) Test pyramid & cadence
- Unit tests with components.  
- Smoke on PR.  
- Full suite on merge.  
- Nightly: a11y, visual, perf smoke.

## 17) Security and hygiene
- No secrets in tests/logs.  
- Mask tokens in CI.  
- Static analysis with ESLint + TS strict.

## 18) Extensions for the agent
- Playwright Test for VS Code  
- ESLint  
- EditorConfig  
- DotENV  
- GitHub Pull Requests & Issues  
- Allure Viewer  

## 19) Onboarding checklist
1. Detect package manager & Node version.  
2. Install dependencies & browsers.  
3. Generate config + VS Code tasks.  
4. Add first specs: login smoke, core journey, a11y scan.  
5. Run `npx playwright test --ui` locally.  
6. Wire CI & push PR with artifacts.

## 20) Maintenance rules
- One PR per feature/fix.  
- Update test IDs if markup changes.  
- Investigate flakes with traces, then fix or quarantine.  
- Review Allure trends weekly.  
- Remove obsolete specs.
