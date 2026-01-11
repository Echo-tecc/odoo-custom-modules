# Monnify Payment Gateway for Odoo 17

Integrate Monnify payment gateway with your Odoo 17 installation to accept payments from Nigerian customers via bank transfers, cards, USSD, and phone numbers.

## Features

- ✅ Accept payments via multiple channels (Cards, Bank Transfer, USSD, Phone Number)
- ✅ Secure webhook integration for real-time payment notifications
- ✅ Support for both test (sandbox) and production environments
- ✅ Automatic transaction status verification
- ✅ Nigerian Naira (NGN) support
- ✅ Easy configuration through Odoo backend
- ✅ Odoo 17 compatible

## Installation

### Method 1: From Odoo Apps Store
1. Go to **Apps** in your Odoo instance
2. Search for "Monnify Payment Gateway"
3. Click **Install**

### Method 2: Manual Installation
1. Download or clone this repository
2. Copy the `payment_monnify` folder to your Odoo addons directory
3. Update the apps list: **Apps** → **Update Apps List**
4. Search for "Monnify Payment Gateway" and install

## Configuration

### Step 1: Get Monnify Credentials

1. Sign up for a Monnify account at [https://monnify.com](https://monnify.com)
2. Login to your Monnify dashboard
3. Navigate to **Settings** → **API Keys**
4. Copy your:
   - API Key
   - Secret Key
   - Contract Code

### Step 2: Configure in Odoo

1. Go to **Accounting** → **Configuration** → **Payment Providers**
2. Find or create "Monnify" provider
3. Fill in your credentials:
   - **API Key**: Your Monnify API Key
   - **Secret Key**: Your Monnify Secret Key
   - **Contract Code**: Your Monnify Contract Code
4. Set the **State**:
   - **Test Mode**: For sandbox/testing (uses sandbox.monnify.com)
   - **Enabled**: For production (uses api.monnify.com)
5. Click **Save**
6. Click **Publish** to make it available to customers

### Step 3: Webhook Configuration

Configure webhook in your Monnify dashboard:

1. Login to Monnify dashboard
2. Go to **Settings** → **Webhooks**
3. Add webhook URL: `https://yourdomain.com/payment/monnify/webhook`
4. Save the configuration

**Note:** Replace `yourdomain.com` with your actual Odoo domain.

## Usage

Once configured, Monnify will appear as a payment option during checkout. Customers can:

1. Select Monnify as their payment method
2. Click "Pay with Monnify"
3. Choose their preferred payment channel (Card, Bank Transfer, USSD, etc.)
4. Complete the payment
5. Get automatically redirected back to your store

## Testing

Use Monnify's test credentials and test cards for testing:

### Test Cards
- **Successful Card**: 5061020000000000094
- **CVV**: 123
- **Expiry**: Any future date
- **PIN**: 1234
- **OTP**: 123456

For more test cards, visit: [Monnify Test Cards](https://developers.monnify.com/docs/test-cards)

## Supported Currencies

Currently supports:
- NGN (Nigerian Naira)

## Troubleshooting

### Payment not confirming
- Check webhook configuration in Monnify dashboard
- Verify webhook URL is accessible from internet
- Check Odoo logs for webhook errors

### "Authentication failed" error
- Verify API Key and Secret Key are correct
- Ensure you're using correct credentials for your environment (test/production)
- Check that Contract Code matches your account

### Payment button not appearing
- Clear browser cache
- Check that provider is Published
- Verify currency is NGN

## Support

For issues related to:
- **This module**: Create an issue on GitHub or contact Echo Tech at [www.echobooks.online](https://www.echobooks.online)
- **Monnify service**: Contact [Monnify Support](https://support.monnify.com)

## Credits

**Developer**: Echo Tech  
**Website**: [www.echobooks.online](https://www.echobooks.online)  
**Monnify Documentation**: [developers.monnify.com](https://developers.monnify.com)

## License

LGPL-3

## Changelog

### Version 17.0.1.0.0
- Initial release
- Support for one-time payments
- Webhook integration
- Test and production mode support
- Odoo 17 compatibility