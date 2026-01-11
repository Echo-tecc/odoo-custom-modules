/** @odoo-module **/

import paymentForm from '@payment/js/payment_form';
import { loadJS } from "@web/core/assets";

paymentForm.include({
    
    /**
     * Add Monnify to the list of providers using inline form
     * @override
     */
    _processPayment: function(provider, paymentOptionId, flow) {
        if (provider !== 'monnify') {
            return this._super(...arguments);
        }
        
        // For Monnify, we use inline/redirect flow
        if (flow === 'redirect') {
            return this._processMonnifyPayment();
        }
        
        return this._super(...arguments);
    },

    /**
     * Process Monnify payment using their SDK
     * @private
     */
    _processMonnifyPayment: function() {
        const self = this;
        const container = this.el.querySelector('.monnify-payment-container');
        
        if (!container) {
            console.error('Monnify: Payment container not found');
            return;
        }
        
        // Extract payment data from hidden inputs
        const apiKey = container.querySelector('[name="monnify_api_key"]').value;
        const contractCode = container.querySelector('[name="monnify_contract_code"]').value;
        const reference = container.querySelector('[name="monnify_reference"]').value;
        const amount = parseFloat(container.querySelector('[name="amount"]').value);
        const currency = container.querySelector('[name="currency"]').value;
        const customerName = container.querySelector('[name="customer_name"]').value;
        const customerEmail = container.querySelector('[name="customer_email"]').value;
        const apiUrl = container.querySelector('[name="api_url"]').value;
        
        // Determine SDK URL based on environment
        const sdkUrl = apiUrl.includes('sandbox') 
            ? 'https://sdk.monnify.com/plugin/monnify.js'
            : 'https://sdk.monnify.com/plugin/monnify.js';
        
        // Load Monnify SDK
        return loadJS(sdkUrl).then(function() {
            // Initialize Monnify payment
            MonnifySDK.initialize({
                amount: amount,
                currency: currency,
                reference: reference,
                customerFullName: customerName,
                customerEmail: customerEmail,
                apiKey: apiKey,
                contractCode: contractCode,
                paymentDescription: `Payment for ${reference}`,
                isTestMode: apiUrl.includes('sandbox'),
                metadata: {
                    odoo_reference: reference
                },
                onComplete: function(response) {
                    console.log('Monnify Payment Complete:', response);
                    self._handleMonnifyResponse(response, true);
                },
                onClose: function() {
                    console.log('Monnify Payment Modal Closed');
                    self._handleMonnifyResponse(null, false);
                }
            });
        }).catch(function(error) {
            console.error('Monnify: Failed to load SDK', error);
            self._displayErrorDialog(
                'Payment Error',
                'Unable to load Monnify payment system. Please try again.'
            );
        });
    },

    /**
     * Handle Monnify payment response
     * @private
     * @param {Object} response - Monnify response object
     * @param {Boolean} isComplete - Whether payment was completed
     */
    _handleMonnifyResponse: function(response, isComplete) {
        if (isComplete && response) {
            // Payment completed successfully
            if (response.status === 'SUCCESS' || response.paymentStatus === 'PAID') {
                // Redirect to payment status page
                window.location.href = '/payment/status';
            } else {
                // Payment failed or pending
                const message = response.message || 'Payment was not successful';
                this._displayErrorDialog('Payment Failed', message);
            }
        } else {
            // Payment modal was closed
            this._enableButton();
        }
    },

    /**
     * Display error dialog
     * @private
     * @param {String} title - Dialog title
     * @param {String} message - Error message
     */
    _displayErrorDialog: function(title, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <strong>${title}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = this.el.querySelector('.monnify-payment-container');
        if (container) {
            container.insertBefore(errorDiv, container.firstChild);
        }
        
        this._enableButton();
    },

    /**
     * Enable the payment button after error or cancellation
     * @private
     */
    _enableButton: function() {
        const button = this.el.querySelector('#monnify-pay-button');
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fa fa-lock me-2"></i>Pay with Monnify';
        }
    }
});

// Add click handler for Monnify pay button
document.addEventListener('DOMContentLoaded', function() {
    const payButton = document.getElementById('monnify-pay-button');
    if (payButton) {
        payButton.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Processing...';
            
            // Trigger the payment form submission
            const form = this.closest('form');
            if (form) {
                const event = new Event('submit', { bubbles: true, cancelable: true });
                form.dispatchEvent(event);
            }
        });
    }
});