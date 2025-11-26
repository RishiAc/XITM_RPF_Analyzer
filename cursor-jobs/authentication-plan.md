# Supabase Authentication Implementation Plan

## Goal
Implement secure authentication so that:
- Only users with an `@example.com` email **or** whitelisted admin emails can sign in.
- Email-based 2FA (one-time code, ~5 minute expiry) is required after primary credentials.
- Sessions persist across visits; all app routes are protected unless a valid session exists.

## Assumptions & Existing Context
- Supabase client initialized in `src/frontend/src/SupaBase/supabaseClient.js`.
- React Router v6 is used (`src/frontend/src/App.js`).
- Frontend uses function components with `useState`/`useEffect`.
- Backend services (Python) exist but focus of this effort is the frontend + Supabase auth.
- Supabase project already provisioned.

## High-Level Architecture
1. **Credential Gate**: Validate email domain or admin list *before* submitting to Supabase.
2. **Primary Auth**: Supabase email/password (`auth.signInWithPassword`) or OTP sign-in for first step.
3. **2FA**: Trigger Supabase OTP (`auth.signInWithOtp`) or custom OTP table + email via Supabase functions; verify on frontend.
4. **Session Persistence**: Use `supabase.auth.getSession()` + `onAuthStateChange` to store session (e.g., in `localStorage` or React context).
5. **Route Guard**: Create higher-order component/`RequireAuth` wrapper that checks for session; redirect to `/login` if missing.

## Detailed Step-by-Step Tasks

| Step | Description | Key Files / Context Needed | Notes |
| --- | --- | --- | --- |
| 1 | **Audit current routing & auth usage**: Confirm pages needing protection and session handling patterns. | `src/frontend/src/App.js`, any existing auth helpers, context providers. | Document findings in this plan if additional helpers exist. |
| 2 | **Design login state shape**: Decide where to store session and user metadata (React Context vs simple hook). | `src/frontend/src/pages/LoginPage.jsx`, new `src/frontend/src/context/AuthContext.jsx`. | Ensure we can share state with router guard; capture session, user, loading, OTP state, helper actions. |
| 3 | **Implement domain/admin validation** on login form prior to Supabase request. | `LoginPage.jsx`, config for allowed domain & admin list (env or constants). | Add friendly errors for rejected emails. |
| 4 | **Primary Supabase sign-in** flow: add password input logic (if using password) or email OTP initiation. | `LoginPage.jsx`, `supabaseClient.js`. | For password-based, ensure we call `signInWithPassword`; for OTP-centric flow, we may need to combine with Step 5. |
| 5 | **2FA email code workflow**: trigger OTP send (`supabase.auth.signInWithOtp` or custom RPC) and add verification UI. | New components for code entry (e.g., `Login2FAStep.jsx`), Supabase auth docs. | Store OTP expiration timestamp client-side to show timer? |
| 6 | **Verify OTP and finalize session**: after code input, call Supabase `verifyOtp` or custom endpoint; persist session tokens. | Same as step 5 plus session handling utilities. | On success, route to home/dashboard. |
| 7 | **Session persistence utilities**: Use `supabase.auth.getSession()` in an `AuthProvider` component to hydrate session on load and subscribe to changes. | New `src/frontend/src/context/AuthContext.jsx` (or hook), `supabaseClient.js`. | Persist in memory + optional `localStorage` if needed. |
| 8 | **Protect routes with guard**: build `RequireAuth` wrapper using React Router `Outlet`, check session and redirect to `/login`. | New `src/frontend/src/components/RequireAuth.jsx`, update `App.js`. | Ensure guard also passes through when session loading is pending. |
| 9 | **Handle logout + session cleanup**: provide `supabase.auth.signOut()` and context cleanup. | Possibly update `Navbar` or dedicated logout button. | Clear stored OTP state. |
| 10 | **Add admin role handling (optional)**: store admin list-> set metadata/claims for role-based UI (if needed). | Possibly new constants file; update context & guard to expose `isAdmin`. | Might rely on Supabase `auth.admin.updateUserById` or `metadata`. |
| 11 | **Testing & verification**: manual test matrix for allowed/non-allowed emails, OTP expiry, session persistence, route protection. | Document test steps in repo `docs/` or this plan. | Include fallback flows (network failure, invalid code). |

## Configuration & Secrets
- Environment variables: `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY` already in use.
- Need new envs: `REACT_APP_ALLOWED_DOMAIN="example.com"`, `REACT_APP_ADMIN_EMAILS="dev1@example.com,dev2@other.com"`, `REACT_APP_OTP_EXPIRY_MIN=5` (optional).

## Pending Open Questions
- Are user accounts already seeded? If not, do we allow self-serve signup (subject to domain restriction) or require admin to create accounts? (Assume self-serve with restrictions.)
- For OTP send, do we rely entirely on Supabase’s email OTP (which sends an email automatically) or custom email service? (Plan assumes Supabase built-in.)

## Implementation Notes
- React Router guard should render nothing (or spinner) while session state is loading to avoid flicker.
- Use Supabase `auth.onAuthStateChange` to keep context in sync.
- Consider saving session to `localStorage` so a refresh doesn’t trigger unnecessary redirect while `getSession` resolves.
- Clean up OTP state in components when unmounted to avoid stale timers.

## Next Actions
1. Confirm Step 1 approval (routing audit) before coding.
2. After each step, update this plan (if necessary) and request approval to proceed to the next.


