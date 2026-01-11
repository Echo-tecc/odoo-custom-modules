# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
Monnify payment provider constants
Compatible with Odoo 17
"""

# -------------------------------------------------------------------------
# URLs
# -------------------------------------------------------------------------

MONNIFY_RETURN_URL = '/payment/monnify/return'
MONNIFY_WEBHOOK_URL = '/payment/monnify/webhook'

# -------------------------------------------------------------------------
# Payment Methods
# -------------------------------------------------------------------------

DEFAULT_PAYMENT_METHODS_CODES = [
    'card',
    'bank_transfer',
]

# -------------------------------------------------------------------------
# Transaction Status Mapping (Monnify → Odoo)
# -------------------------------------------------------------------------

TRANSACTION_STATUS_MAPPING = {
    'paid': 'done',
    'overpaid': 'done',
    'partially_paid': 'done',
    'pending': 'pending',
    'failed': 'cancel',
    'cancelled': 'cancel',
    'expired': 'cancel',
}

# -------------------------------------------------------------------------
# Webhook Security (Optional)
# -------------------------------------------------------------------------

# NOTE:
# Monnify may use multiple IPs depending on region and infrastructure.
# Do NOT rely solely on IP validation. Always verify webhook signature.
MONNIFY_WEBHOOK_IPS = [
    '35.242.133.146',
]
