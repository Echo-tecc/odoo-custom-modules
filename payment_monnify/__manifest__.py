{
    'name': 'Monnify Payment Gateway',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: Monnify Implementation',
    'author': 'Echo Tech',
    'website': 'https://www.echobooks.online',
    'license': 'LGPL-3',
    'depends': ['payment'],
    'data': [
        'views/payment_monnify_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_monnify/static/src/js/payment_form.js',
        ],
    },
    'installable': True,
    'application': False,
}
