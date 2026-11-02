"""
Dodd Foundation Treasury — Flask backend for Stripe Financial Connections

Run:
  pip install flask stripe python-dotenv
  export STRIPE_SECRET_KEY=sk_test_...
  export STRIPE_PUBLISHABLE_KEY=pk_test_...
  python app.py

Then open http://localhost:5000
"""

import os
from flask import Flask, jsonify, request, send_from_directory
import stripe

app = Flask(__name__, static_folder='.', static_url_path='')

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')
PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_placeholder')

# Simple in-memory store for prototype (replace with DB in production)
# Maps local session or fixed user → Stripe Customer ID and linked account IDs
state = {
    'customer_id': None,
    'linked_accounts': []  # list of {id, institution, display_name, last4, balance, ...}
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/manifest.webmanifest')
def manifest():
    return send_from_directory('.', 'manifest.webmanifest')

@app.route('/sw.js')
def sw():
    return send_from_directory('.', 'sw.js')

@app.route('/api/config')
def config():
    return jsonify({'publishableKey': PUBLISHABLE_KEY})

@app.route('/api/create-fc-session', methods=['POST'])
def create_fc_session():
    """Create a Financial Connections Session and return client_secret."""
    try:
        # Create or reuse a Customer for this prototype
        if not state['customer_id']:
            customer = stripe.Customer.create(
                name='Dodd Foundation (Prototype)',
                email='treasury@dodd.foundation.example',
                description='Local prototype customer for Financial Connections'
            )
            state['customer_id'] = customer.id

        session = stripe.financial_connections.Session.create(
            account_holder={
                'type': 'customer',
                'customer': state['customer_id']
            },
            permissions=['balances', 'transactions', 'payment_method', 'ownership'],
            filters={'countries': ['US']}
        )
        return jsonify({'clientSecret': session.client_secret, 'sessionId': session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sync-accounts', methods=['POST'])
def sync_accounts():
    """After Link completes, retrieve the session and store account details + balances."""
    data = request.get_json() or {}
    session_id = data.get('sessionId')
    if not session_id:
        return jsonify({'error': 'sessionId required'}), 400

    try:
        session = stripe.financial_connections.Session.retrieve(session_id)
        accounts = []
        for acc in session.accounts.data:
            # Refresh balance
            try:
                balance = stripe.financial_connections.Account.retrieve(acc.id, expand=['balance'])
                bal = balance.balance.current[0] if balance.balance and balance.balance.current else None
                available = balance.balance.available[0] if balance.balance and balance.balance.available else None
            except Exception:
                bal = available = None

            accounts.append({
                'id': acc.id,
                'institution': acc.institution_name,
                'display_name': acc.display_name or acc.subcategory or 'Account',
                'last4': acc.last4,
                'category': acc.category,
                'subcategory': acc.subcategory,
                'status': acc.status,
                'balance': bal / 100 if bal is not None else None,  # cents → dollars
                'available': available / 100 if available is not None else None
            })
        state['linked_accounts'] = accounts
        return jsonify({'accounts': accounts})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/accounts')
def get_accounts():
    return jsonify({'accounts': state['linked_accounts'], 'customerId': state['customer_id']})

@app.route('/api/refresh-balances', methods=['POST'])
def refresh_balances():
    """Re-fetch balances for already-linked accounts."""
    updated = []
    for acc in state['linked_accounts']:
        try:
            full = stripe.financial_connections.Account.retrieve(acc['id'], expand=['balance'])
            bal = full.balance.current[0] if full.balance and full.balance.current else None
            avail = full.balance.available[0] if full.balance and full.balance.available else None
            acc['balance'] = bal / 100 if bal is not None else None
            acc['available'] = avail / 100 if avail is not None else None
            updated.append(acc)
        except Exception as e:
            acc['error'] = str(e)
            updated.append(acc)
    state['linked_accounts'] = updated
    return jsonify({'accounts': updated})

@app.route('/api/execute-payout', methods=['POST'])
def execute_payout():
    """
    Prototype: create a Stripe payout for an approved transfer.
    In test mode this creates a payout object. Live mode moves real money.
    Requires a linked external account or uses the platform balance.
    """
    data = request.get_json() or {}
    amount = data.get('amount')  # in dollars
    description = data.get('description', 'Foundation grant / transfer')
    destination_last4 = data.get('destinationLast4')
    request_id = data.get('requestId')

    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Valid amount required'}), 400

    try:
        # Convert to cents
        amount_cents = int(float(amount) * 100)

        # For prototype: create a payout from the Stripe account balance
        # (In production you would select a specific external account or use ACH debit/credit)
        payout = stripe.Payout.create(
            amount=amount_cents,
            currency='usd',
            description=description[:140] if description else 'Treasury payout',
            statement_descriptor='DODD FOUND',
            metadata={
                'request_id': request_id or '',
                'destination_last4': destination_last4 or '',
                'source': 'dodd-treasury-prototype'
            }
        )
        return jsonify({
            'success': True,
            'payoutId': payout.id,
            'status': payout.status,
            'amount': amount,
            'arrivalDate': payout.arrival_date
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print('Starting Dodd Foundation Treasury backend on http://localhost:5000')
    print('Set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY environment variables.')
    app.run(host='0.0.0.0', port=5000, debug=True)
