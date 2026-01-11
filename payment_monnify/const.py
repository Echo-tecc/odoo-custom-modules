# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

""" Monnify payment provider constants """

# URL endpoints
MONNIFY_RETURN_URL = '/payment/monnify/return'
MONNIFY_WEBHOOK_URL = '/payment/monnify/webhook'

# Default payment methods supported by Monnify
DEFAULT_PAYMENT_METHODS_CODES = ['card', 'bank_transfer']

# Monnify transaction statuses
TRANSACTION_STATUS_MAPPING = {
    'PAID': 'done',
    'OVERPAID': 'done',
    'PARTIALLY_PAID': 'done',
    'PENDING': 'pending',
    'FAILED': 'cancel',
    'CANCELLED': 'cancel',
    'EXPIRED': 'cancel',
}

# Monnify webhook IP for whitelisting (optional security measure)
MONNIFY_WEBHOOK_IP = '35.242.133.146'