# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

from odoo.addons.payment_monnify.models.payment_transaction import PaymentTransaction

_logger = logging.getLogger(__name__)


class MonnifyController(http.Controller):
    _return_url = '/payment/monnify/return'
    _webhook_url = '/payment/monnify/webhook'

    # -------------------------------------------------------------------------
    # Return from checkout
    # -------------------------------------------------------------------------
    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def monnify_return_from_checkout(self, **data):
        """Process return from Monnify checkout page."""
        _logger.info('Monnify: Return from checkout:\n%s', pprint.pformat(data))

        reference = data.get('paymentReference') or data.get('transactionReference')

        if reference:
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference),
                ('provider_code', '=', 'monnify')
            ], limit=1)

            if tx_sudo:
                try:
                    self._verify_transaction_status(tx_sudo)
                except Exception as e:
                    _logger.exception('Monnify: Error verifying transaction: %s', e)

                # Redirect user to standard payment status page
                return request.redirect('/payment/status')

        _logger.warning('Monnify: Return data missing reference')
        return request.redirect('/payment/status')

    # -------------------------------------------------------------------------
    # Webhook endpoint
    # -------------------------------------------------------------------------
    @http.route(_webhook_url, type='json', auth='public', methods=['POST'], csrf=False)
    def monnify_webhook(self):
        """Process Monnify webhook notifications."""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            _logger.exception('Monnify: Failed to parse webhook payload')
            return {'status': 'error', 'message': 'Invalid payload'}

        _logger.info('Monnify: Webhook received:\n%s', pprint.pformat(data))

        signature = request.httprequest.headers.get('monnify-signature')
        if not signature:
            _logger.warning('Monnify: Webhook missing signature')
            return {'status': 'error', 'message': 'Missing signature'}

        event_type = data.get('eventType')
        event_data = data.get('eventData', {})

        # Only process successful transactions
        if event_type != 'SUCCESSFUL_TRANSACTION':
            _logger.info('Monnify: Ignoring event type: %s', event_type)
            return {'status': 'success'}

        try:
            # Find transaction
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'monnify', event_data
            )

            # Verify webhook signature
            if not PaymentTransaction._monnify_verify_signature(
                request.httprequest.data.decode('utf-8'),
                signature,
                tx_sudo.provider_id.monnify_secret_key
            ):
                _logger.warning('Monnify: Invalid webhook signature for tx %s', tx_sudo.reference)
                return {'status': 'error', 'message': 'Invalid signature'}

            # Process notification
            tx_sudo._process_notification_data(event_data)

            return {'status': 'success'}

        except ValidationError as e:
            _logger.exception('Monnify: Webhook processing failed: %s', e)
            return {'status': 'error', 'message': str(e)}

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _verify_transaction_status(self, tx_sudo):
        """Verify transaction status by calling Monnify API."""
        provider = tx_sudo.provider_id

        if not tx_sudo.provider_reference:
            _logger.warning('Monnify: Transaction %s has no provider reference', tx_sudo.reference)
            return

        endpoint = f'/api/v2/transactions/{tx_sudo.provider_reference}'

        try:
            result = provider._monnify_make_request(endpoint, method='GET')
        except Exception as e:
            _logger.exception('Monnify: Failed to fetch transaction %s: %s', tx_sudo.reference, e)
            return

        if result.get('requestSuccessful'):
            tx_sudo._process_notification_data(result.get('responseBody', {}))
        else:
            _logger.warning(
                'Monnify: Failed to verify transaction %s: %s',
                tx_sudo.reference,
                result.get('responseMessage')
            )
