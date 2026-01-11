# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import hashlib
import hmac
import json

from odoo import _, models
from odoo.exceptions import ValidationError
from werkzeug import urls

from odoo.addons.payment_monnify import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # -------------------------------------------------------------------------
    # Rendering values (Payment form)
    # -------------------------------------------------------------------------

    def _get_specific_rendering_values(self, processing_values):
        """Return provider-specific rendering values for Monnify."""
        rendering_values = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'monnify':
            return rendering_values

        base_url = self.provider_id.get_base_url()

        init_payload = {
            'amount': self.amount,
            'currency_code': self.currency_id.name,
            'reference': self.reference,
            'customer_name': self.partner_name or '',
            'customer_email': self.partner_email or '',
            'return_url': urls.url_join(base_url, const.MONNIFY_RETURN_URL),
            'meta': {
                'odoo_tx_id': self.id,
            },
        }

        monnify_response = self.provider_id._monnify_initialize_transaction(init_payload)

        if not monnify_response.get('checkoutUrl'):
            raise ValidationError(_('Monnify: Failed to initialize transaction.'))

        self.provider_reference = monnify_response.get('transactionReference')

        return {
            'checkout_url': monnify_response['checkoutUrl'],
        }

    # -------------------------------------------------------------------------
    # Transaction lookup from webhook / return data
    # -------------------------------------------------------------------------

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find the transaction based on Monnify notification data."""
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'monnify' or tx:
            return tx

        reference = (
            notification_data.get('paymentReference')
            or notification_data.get('transactionReference')
        )

        if not reference:
            raise ValidationError(_('Monnify: Missing transaction reference.'))

        tx = self.search([
            ('reference', '=', reference),
            ('provider_code', '=', 'monnify'),
        ], limit=1)

        if not tx:
            raise ValidationError(
                _('Monnify: No transaction found for reference %s.', reference)
            )

        return tx

    # -------------------------------------------------------------------------
    # Notification processing
    # -------------------------------------------------------------------------

    def _process_notification_data(self, notification_data):
        """Process Monnify webhook/return notification."""
        super()._process_notification_data(notification_data)

        if self.provider_code != 'monnify':
            return

        if not self.provider_reference:
            self.provider_reference = notification_data.get('transactionReference')

        status = notification_data.get('paymentStatus', '').lower()
        mapped_status = const.TRANSACTION_STATUS_MAPPING.get(status)

        if not mapped_status:
            _logger.warning(
                'Monnify: Unknown payment status %s for tx %s',
                status, self.reference
            )
            self._set_error(_('Unknown payment status: %s', status))
            return

        # Amount validation (required by Odoo 17)
        paid_amount = float(notification_data.get('amountPaid', 0.0))
        if mapped_status == 'done' and not self._is_amount_valid(paid_amount):
            self._set_error(
                _('Amount mismatch: expected %s, received %s')
                % (self.amount, paid_amount)
            )
            return

        if mapped_status == 'done':
            self._set_done()
        elif mapped_status == 'pending':
            self._set_pending()
        elif mapped_status == 'cancel':
            self._set_canceled(
                notification_data.get('paymentDescription') or _('Payment cancelled.')
            )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _is_amount_valid(self, amount):
        """Check if the paid amount matches the transaction amount."""
        self.ensure_one()
        return abs(self.amount - amount) < 0.01

    @staticmethod
    def _monnify_verify_signature(payload, signature, secret_key):
        """Verify Monnify webhook signature (SHA512)."""
        computed_signature = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed_signature, signature)
