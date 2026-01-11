# -*- coding: utf-8 -*-

import logging
import base64
import requests

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # -------------------------------------------------------------------------
    # Provider Configuration
    # -------------------------------------------------------------------------

    code = fields.Selection(
        selection_add=[('monnify', 'Monnify')],
        ondelete={'monnify': 'set default'},
    )

    monnify_api_key = fields.Char(
        string='API Key',
        help='Your Monnify API Key',
        password=True,
        groups='base.group_system',
    )

    monnify_secret_key = fields.Char(
        string='Secret Key',
        help='Your Monnify Secret Key',
        password=True,
        groups='base.group_system',
    )

    monnify_contract_code = fields.Char(
        string='Contract Code',
        help='Your Monnify Contract Code',
        groups='base.group_system',
    )

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _get_monnify_base_url(self):
        """Return Monnify base URL based on provider state."""
        self.ensure_one()
        return (
            'https://api.monnify.com'
            if self.state == 'enabled'
            else 'https://sandbox.monnify.com'
        )

    def _monnify_get_access_token(self):
        """Authenticate and retrieve access token from Monnify."""
        self.ensure_one()

        if not all([
            self.monnify_api_key,
            self.monnify_secret_key,
            self.monnify_contract_code,
        ]):
            raise ValidationError(
                _('Monnify: Please configure API Key, Secret Key, and Contract Code.')
            )

        auth_url = urls.url_join(
            self._get_monnify_base_url(),
            '/api/v1/auth/login'
        )

        credentials = f"{self.monnify_api_key}:{self.monnify_secret_key}"
        encoded_credentials = base64.b64encode(
            credentials.encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(auth_url, headers=headers, timeout=15)
            response.raise_for_status()
            result = response.json()

            if not result.get('requestSuccessful'):
                raise ValidationError(
                    _('Monnify: Authentication failed (%s).')
                    % result.get('responseMessage', 'Unknown error')
                )

            return result['responseBody']['accessToken']

        except requests.exceptions.RequestException as e:
            _logger.exception('Monnify authentication error')
            raise ValidationError(
                _('Monnify: Unable to authenticate. Please verify your credentials.')
            ) from e

    def _monnify_request(self, endpoint, payload=None, method='POST'):
        """Make an authenticated request to Monnify."""
        self.ensure_one()

        token = self._monnify_get_access_token()
        url = urls.url_join(self._get_monnify_base_url(), endpoint)

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        try:
            if method == 'POST':
                response = requests.post(
                    url, json=payload, headers=headers, timeout=15
                )
            else:
                response = requests.get(
                    url, headers=headers, timeout=15
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            _logger.exception('Monnify API request failed')
            raise ValidationError(
                _('Monnify: API request failed. Please try again later.')
            ) from e

    # -------------------------------------------------------------------------
    # Odoo Payment Provider Overrides
    # -------------------------------------------------------------------------

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """Limit Monnify to NGN currency."""
        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, **kwargs
        )

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name != 'NGN':
            providers = providers.filtered(lambda p: p.code != 'monnify')

        return providers

    def _get_default_payment_method_codes(self):
        """Return supported payment method codes for Monnify."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'monnify':
            return default_codes

        return ['card', 'bank_transfer']

    # -------------------------------------------------------------------------
    # Monnify Transaction Logic
    # -------------------------------------------------------------------------

    def _monnify_initialize_transaction(self, transaction_values):
        """Initialize a transaction on Monnify."""
        self.ensure_one()

        payload = {
            'amount': transaction_values['amount'],
            'customerName': transaction_values['partner_name'],
            'customerEmail': transaction_values['partner_email'],
            'paymentReference': transaction_values['reference'],
            'paymentDescription': transaction_values.get(
                'reference', 'Odoo Payment'
            ),
            'currencyCode': transaction_values['currency_code'],
            'contractCode': self.monnify_contract_code,
            'redirectUrl': transaction_values['return_url'],
            'paymentMethods': ['CARD', 'ACCOUNT_TRANSFER'],
        }

        if transaction_values.get('custom'):
            payload['metadata'] = transaction_values['custom']

        result = self._monnify_request(
            '/api/v1/merchant/transactions/init-transaction',
            payload=payload,
            method='POST',
        )

        if not result.get('requestSuccessful'):
            raise ValidationError(
                _('Monnify: %s')
                % result.get('responseMessage', 'Transaction initialization failed')
            )

        return result['responseBody']
