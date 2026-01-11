# -*- coding: utf-8 -*-
{
    'name': 'Monnify Payment Gateway',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 1,
    'summary': 'Payment Provider: Monnify Implementation',
    'description': """
Monnify Payment Gateway Integration for Odoo
=============================================

This module integrates Monnify payment gateway with Odoo, allowing you to:
- Accept payments via bank transfer, cards, USSD, and phone number
- Process one-time payments
- Handle webhooks for payment confirmations
- Support both test and production environments
- Multi-currency support (primarily NGN)

Configuration
-------------
1. Go to Accounting > Configuration > Payment Providers
2. Select Monnify or create a new Monnify provider
3. Enter your API Key, Secret Key, and Contract Code
4. Choose between Test or Production mode
5. Save and Publish the provider

For more information, visit: https://developers.monnify.com
    """,
    'author': 'Echo Tech',
    'website': 'https://www.echobooks.online',
    'license': 'LGPL-3',
    'depends': ['payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_monnify_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_monnify/static/src/js/payment_form.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}