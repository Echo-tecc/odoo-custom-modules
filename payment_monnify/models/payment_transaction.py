# -*- coding: utf-8 -*-

import logging
import hashlib
import hmac

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_monnify import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override to return Monnify-specific rendering values.
        
        :param dict processing_values: The processing values
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'monnify':
            return res

        # Get base URL for the payment provider
        base_url = self.provider_id.get_base_url()
        
        # Prepare transaction values for Monnify
        transaction_values = {
            'amount': self.amount,
            'currency_code': self.currency_id.name,
            'reference': self.reference,
            'partner_name': self.partner_name or '',
            'partner_email': self.partner_email or '',
            'return_url': urls.url_join(base_url, const.MONNIFY_RETURN_URL),
            'custom': {
                'transaction_id': self.id,
            }
        }
        
        # Initialize transaction with Monnify
        monnify_data = self.provider_id._monnify_initialize_transaction(transaction_values)
        
        # Store the Monnify transaction reference
        self.provider_reference = monnify_data.get('transactionReference')
        
        # Prepare rendering values for the payment form
        rendering_values = {
            'api_url': self.provider_id._get_monnify_urls(),
            'amount': self.amount,
            'currency': self.currency_id.name,
            'reference': self.reference,
            'monnify_reference': monnify_data.get('transactionReference'),
            'checkout_url': monnify_data.get('checkoutUrl'),
            'contract_code': self.provider_id.monnify_contract_code,
            'api_key': self.provider_id.monnify_api_key,
            'customer_name': self.partner_name or '',
            'customer_email': self.partner_email or '',
        }
        
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override to find the transaction based on Monnify data.
        
        :param str provider_code: The provider code
        :param dict notification_data: The notification data
        :return: The transaction
        :rtype: recordset of `payment.transaction`
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'monnify' or len(tx) == 1:
            return tx

        # Search by payment reference or transaction reference
        reference = notification_data.get('paymentReference') or notification_data.get('transactionReference')
        if not reference:
            raise ValidationError(
                'Monnify: ' + _('Received data with missing reference')
            )

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'monnify')])
        if not tx:
            raise ValidationError(
                'Monnify: ' + _('No transaction found matching reference %s.', reference)
            )
        
        return tx

    def _process_notification_data(self, notification_data):
        """ Override to process the transaction based on Monnify data.
        
        :param dict notification_data: The notification data
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'monnify':
            return

        # Update provider reference if not set
        if not self.provider_reference:
            self.provider_reference = notification_data.get('transactionReference')

        # Determine transaction status
        payment_status = notification_data.get('paymentStatus', '').upper()
        
        if payment_status == 'PAID':
            # Verify the amount and currency
            paid_amount = float(notification_data.get('amountPaid', 0))
            expected_amount = self.amount
            
            if abs(paid_amount - expected_amount) < 0.01:  # Allow small rounding differences
                self._set_done()
            else:
                _logger.warning(
                    'Monnify: Amount mismatch for transaction %s (expected: %s, received: %s)',
                    self.reference, expected_amount, paid_amount
                )
                self._set_error(
                    _('Amount mismatch: expected %s but received %s', expected_amount, paid_amount)
                )
        elif payment_status in ['OVERPAID', 'PARTIALLY_PAID']:
            # Handle overpayment or partial payment
            _logger.info(
                'Monnify: Transaction %s status: %s', self.reference, payment_status
            )
            self._set_done()
        elif payment_status == 'PENDING':
            self._set_pending()
        elif payment_status in ['FAILED', 'CANCELLED', 'EXPIRED']:
            self._set_canceled(
                _('Payment %s: %s', payment_status.lower(), 
                  notification_data.get('paymentDescription', ''))
            )
        else:
            _logger.warning(
                'Monnify: Unknown payment status %s for transaction %s',
                payment_status, self.reference
            )
            self._set_error(_('Unknown payment status: %s', payment_status))

    @staticmethod
    def _monnify_verify_signature(payload, signature, secret_key):
        """ Verify the Monnify webhook signature.
        
        :param str payload: The webhook payload as string
        :param str signature: The signature from the webhook header
        :param str secret_key: The provider's secret key
        :return: True if signature is valid
        :rtype: bool
        """
        computed_signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)


from werkzeug import urls