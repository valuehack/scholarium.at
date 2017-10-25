import os, ipdb, json


def anfrage_token():
    befehl = """cd /home/scholarium; curl -v https://api.sandbox.paypal.com/v1/oauth2/token -H "Accept: application/json" -H "Accept-Language: en_US" -u "AasKeJoihSdkebF5q7QCuubWoIpnlZiV5vfklRN6onwfU9AJYOwXJ5HvDO-PFghOdi26gGzzpc38qb7B:EI3An34Ea1-D5oKS59QwAI0mGu8ELZRT3m9YxPKfRCdoGlqlYL3Oqc8jlelBMpebtxXsKBjO4GCZmnOz" -d "grant_type=client_credentials" > hallo.txt"""
    os.chdir('/home/scholarium/')
    os.system(befehl)
    with open("hallo.txt", 'r') as f:
        antwort = f.read()
    os.system('rm hallo.txt')
    return json.loads(antwort)['access_token']

def erstelle_payment(token):
    befehl = """curl -v -X POST https://api.sandbox.paypal.com/v1/payments/payment \
-H "Content-Type:application/json" \
-H "Authorization: Bearer %s" \
-d '{
  "intent": "sale",
  "payer": {
  "payment_method": "paypal"
  },
  "transactions": [
  {
    "amount": {
    "total": "30.11",
    "currency": "USD",
    "details": {
      "subtotal": "30.00",
      "tax": "0.07",
      "shipping": "0.03",
      "handling_fee": "1.00",
      "shipping_discount": "-1.00",
      "insurance": "0.01"
    }
    },
    "description": "The payment transaction description.",
    "custom": "EBAY_EMS_90048630024435",
    "invoice_number": "48787589673",
    "payment_options": {
    "allowed_payment_method": "INSTANT_FUNDING_SOURCE"
    },
    "soft_descriptor": "ECHI5786786",
    "item_list": {
    "items": [
      {
      "name": "hat",
      "description": "Brown hat.",
      "quantity": "5",
      "price": "3",
      "tax": "0.01",
      "sku": "1",
      "currency": "USD"
      },
      {
      "name": "handbag",
      "description": "Black handbag.",
      "quantity": "1",
      "price": "15",
      "tax": "0.02",
      "sku": "product34",
      "currency": "USD"
      }
    ],
    "shipping_address": {
      "recipient_name": "Brian Robinson",
      "line1": "4th Floor",
      "line2": "Unit #34",
      "city": "San Jose",
      "country_code": "US",
      "postal_code": "95131",
      "phone": "011862212345678",
      "state": "CA"
    }
    }
  }
  ],
  "note_to_payer": "Contact us for any questions on your order.",
  "redirect_urls": {
  "return_url": "http://127.0.0.1",
  "cancel_url": "http://127.0.0.1/scholien/"
  }
}'""" % token
    antwort = os.popen(befehl).read()
    return json.loads(antwort)

def pruefe_payment(paymentID, token):
    befehl = """curl -v -X GET https://api.sandbox.paypal.com/v1/payments/payment/%s \\
  -H "Content-Type:application/json" \\
  -H "Authorization: Bearer %s" """ % (paymentID, token)
    antwort = os.popen(befehl).read()
    return json.loads(antwort)

def fuehre_payment_aus(paymentID, token, transactions, payer_id):
    befehl = """curl -v -X POST https://api.sandbox.paypal.com/v1/payments/payment/%s/execute \
-H "Content-Type:application/json" \
-H "Authorization: Bearer %s" \
-d '{
  "payer_id": "%s", 
  "transactions": %s
}' """ % (paymentID, token, transactions, payer_id)
    antwort = os.popen(befehl).read()
    return json.loads(antwort)

if __name__=='__main__':
    access_token = anfrage_token()
    zahlung = erstelle_payment(access_token)
    zahlung = pruefe_payment(zahlung['id'], access_token)
    ipdb.set_trace()
