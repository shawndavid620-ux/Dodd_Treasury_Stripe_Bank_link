# Dodd Foundation Treasury — Prototype with Stripe Financial Connections

## Included
- `index.html`: responsive treasury app with bank linking
- `manifest.webmanifest`: installable-web-app metadata
- `sw.js`: basic service worker
- `app.py`: Flask backend that talks to Stripe Financial Connections
- `requirements.txt`: Python dependencies
- `README.txt`: this guide

## What it does
- Manual account/transaction ledger (localStorage)
- **Connect real bank accounts** via Stripe Financial Connections
- Pull live balances for linked accounts
- Local approval workflow for transfers
- **On approval, creates a real Stripe Payout** (test mode by default)
- JSON / CSV export

## Current limits (still a prototype)
- Single local user; no auth
- In-memory backend state (restart loses linked accounts until you reconnect)
- Approval is recorded only; no actual Stripe Payout/Transfer is initiated
- Requires your own Stripe account and keys
- Do not enter sensitive credentials, full account numbers, or real confidential data in the browser

## Quick start
1. Create a free Stripe account (or use your existing one) and enable Financial Connections.
2. Get your **test** secret key (`sk_test_…`) and publishable key (`pk_test_…`) from the Stripe Dashboard → Developers → API keys.
3. In a terminal:
   ```bash
   cd dodd_foundation_treasury
   pip install -r requirements.txt
   export STRIPE_SECRET_KEY=sk_test_your_key_here
   export STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
   python app.py
   ```
4. Open http://localhost:5000
5. Click **Connect bank accounts** → complete the Stripe Link flow with a test bank (Stripe provides test institutions in sandbox).
6. Linked accounts and balances appear in the registry and overview.

## Production path
1. Host the Flask (or FastAPI) backend on a real server with HTTPS.
2. Store Stripe Customer IDs, Financial Connections account IDs, and access tokens in a database (never in the browser).
3. Add authentication + MFA and role-based access.
4. After approval, create Stripe Payouts or Transfers from the linked accounts.
5. Add webhooks for balance updates and transaction sync.
6. Security review, audit logging, and compliance before real money.

## Stripe notes
- Use **test mode** keys while developing.
- Financial Connections sessions request `balances`, `transactions`, `payment_method`, and `ownership`.
- Tokenized account numbers can later be used for ACH via Stripe.

This is the next step from the pure client-side prototype toward a real treasury tool.
