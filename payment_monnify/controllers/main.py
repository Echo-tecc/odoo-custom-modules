# -*- coding: utf-8 -*-

import json
import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MonnifyController(http.Controller):
    _return_url = '/payment/monnify/return'
    _webhook_url = '/payment/monnify/webhook'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def monnify_return_from_checkout(self, **data):
        """ Process the return from Monnify checkout.
        
        This endpoint is called when the customer returns from Monnify payment page.
        """
        _logger.info('Monnify: Handling return from checkout with data:\n%s', pprint.pformat(data))
        
        # Extract transaction reference from return data
        reference = data.get('paymentReference') or data.get('transactionReference')
        
        if reference:
            # Find the transaction
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference),
                ('provider_code', '=', 'monnify')
            ], limit=1)
            
            if tx_sudo:
                # Verify transaction status with Monnify API
                try:
                    self._verify_transaction_status(tx_sudo)
                except Exception as e:
                    _logger.exception('Monnify: Error verifying transaction: %s', e)
                
                # Redirect to status page
                return request.redirect('/payment/status')
        
        _logger.warning('Monnify: Return data does not contain valid reference')
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='json', auth='public', methods=['POST'], csrf=False)
    def monnify_webhook(self):
        """ Process webhook notification from Monnify.
        
        Monnify sends webhook notifications for successful transactions.
        The webhook is signed with SHA512 HMAC using the secret key.
        """
        data = json.loads(request.httprequest.data)
        _logger.info('Monnify: Webhook notification received:\n%s', pprint.pformat(data))
        
        # Get the signature from headers
        signature = request.httprequest.headers.get('monnify-signature')
        
        if not signature:
            _logger.warning('Monnify: Webhook received without signature')
            return {'status': 'error', 'message': 'Missing signature'}
        
        # Extract event data
        event_type = data.get('eventType')
        event_data = data.get('eventData', {})
        
        if event_type != 'SUCCESSFUL_TRANSACTION':
            _logger.info('Monnify: Ignoring webhook event type: %s', event_type)
            return {'status': 'success'}
        
        try:
            # Find the transaction
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'monnify', event_data
            )
            
            # Verify webhook signature
            if not self._verify_webhook_signature(
                request.httprequest.data.decode('utf-8'),
                signature,
                tx_sudo.provider_id.monnify_secret_key
            ):
                _logger.warning('Monnify: Invalid webhook signature for transaction %s', tx_sudo.reference)
                return {'status': 'error', 'message': 'Invalid signature'}
            
            # Process the notification
            tx_sudo._process_notification_data(event_data)
            
            return {'status': 'success'}
            
        except ValidationError as e:
            _logger.exception('Monnify: Webhook processing failed: %s', e)
            return {'status': 'error', 'message': str(e)}

    def _verify_transaction_status(self, tx_sudo):
        """ Verify transaction status with Monnify API.
        
        :param tx_sudo: Payment transaction recordset
        """
        provider = tx_sudo.provider_id
        
        # Get transaction details from Monnify
        endpoint = f'/api/v2/transactions/{tx_sudo.provider_reference}'
        result = provider._monnify_make_request(endpoint, method='GET')
        
        if result.get('requestSuccessful'):
            transaction_data = result.get('responseBody', {})
            tx_sudo._process_notification_data(transaction_data)
        else:
            _logger.warning(
                'Monnify: Failed to verify transaction %s: %s',
                tx_sudo.reference,
                result.get('responseMessage')
            )

    @staticmethod
    def _verify_webhook_signature(payload, signature, secret_key):
        """ Verify the webhook signature.
        
        :param str payload: Raw webhook payload
        :param str signature: Signature from webhook header
        :param str secret_key: Provider secret key
        :return: True if signature is valid
        :rtype: bool
        """
        from odoo.addons.payment.models.payment_transaction import PaymentTransaction
        return PaymentTransaction._monnify_verify_signature(payload, signature, secret_key)