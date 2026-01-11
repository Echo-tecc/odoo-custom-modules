# -*- coding: utf-8 -*-

import logging
import requests
import base64
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('monnify', 'Monnify')],
        ondelete={'monnify': 'set default'}
    )
    
    monnify_api_key = fields.Char(
        string='API Key',
        help='Your Monnify API Key',
        required_if_provider='monnify',
        groups='base.group_system'
    )
    
    monnify_secret_key = fields.Char(
        string='Secret Key',
        help='Your Monnify Secret Key',
        required_if_provider='monnify',
        groups='base.group_system'
    )
    
    monnify_contract_code = fields.Char(
        string='Contract Code',
        help='Your Monnify Contract Code',
        required_if_provider='monnify',
        groups='base.group_system'
    )

    def _get_monnify_urls(self):
        """ Return the Monnify API URLs based on the provider state.
        
        :return: The API base URL
        :rtype: str
        """
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://api.monnify.com'
        else:
            return 'https://sandbox.monnify.com'

    def _monnify_get_access_token(self):
        """ Get OAuth 2.0 access token from Monnify.
        
        :return: Access token
        :rtype: str
        """
        self.ensure_one()
        
        base_url = self._get_monnify_urls()
        auth_url = urls.url_join(base_url, '/api/v1/auth/login')
        
        # Create Basic Auth credentials
        credentials = f"{self.monnify_api_key}:{self.monnify_secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(auth_url, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('requestSuccessful'):
                return result['responseBody']['accessToken']
            else:
                error_msg = result.get('responseMessage', 'Unknown error')
                raise ValidationError(
                    _('Monnify: Authentication failed. %s', error_msg)
                )
                
        except requests.exceptions.RequestException as e:
            _logger.exception('Monnify: Error during authentication: %s', e)
            raise ValidationError(
                _('Monnify: Unable to authenticate. Please check your credentials.')
            )

    def _monnify_make_request(self, endpoint, payload=None, method='POST'):
        """ Make an authenticated request to Monnify API.
        
        :param str endpoint: API endpoint
        :param dict payload: Request payload
        :param str method: HTTP method
        :return: API response
        :rtype: dict
        """
        self.ensure_one()
        
        access_token = self._monnify_get_access_token()
        base_url = self._get_monnify_urls()
        url = urls.url_join(base_url, endpoint)
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            else:
                response = requests.get(url, headers=headers, timeout=10)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            _logger.exception('Monnify: API request failed: %s', e)
            raise ValidationError(
                _('Monnify: API request failed. Please try again.')
            )

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """ Override to filter Monnify based on currency support.
        
        Monnify primarily supports NGN (Nigerian Naira).
        """
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)
        
        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name != 'NGN':
            providers = providers.filtered(lambda p: p.code != 'monnify')
            
        return providers

    def _get_default_payment_method_codes(self):
        """ Override to return the default payment method codes for Monnify. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'monnify':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES

    def _monnify_initialize_transaction(self, transaction_values):
        """ Initialize a transaction on Monnify.
        
        :param dict transaction_values: Transaction data
        :return: Monnify transaction reference
        :rtype: str
        """
        self.ensure_one()
        
        payload = {
            'amount': transaction_values['amount'],
            'customerName': transaction_values['partner_name'],
            'customerEmail': transaction_values['partner_email'],
            'paymentReference': transaction_values['reference'],
            'paymentDescription': transaction_values.get('reference', 'Payment'),
            'currencyCode': transaction_values['currency_code'],
            'contractCode': self.monnify_contract_code,
            'redirectUrl': transaction_values['return_url'],
            'paymentMethods': ['CARD', 'ACCOUNT_TRANSFER'],
        }
        
        # Add metadata if available
        if transaction_values.get('custom'):
            payload['metadata'] = transaction_values['custom']
        
        result = self._monnify_make_request(
            '/api/v1/merchant/transactions/init-transaction',
            payload
        )
        
        if result.get('requestSuccessful'):
            return result['responseBody']
        else:
            error_msg = result.get('responseMessage', 'Transaction initialization failed')
            raise ValidationError(_('Monnify: %s', error_msg))


# Import constants after class definition to avoid circular import
from odoo.addons.payment_monnify import const