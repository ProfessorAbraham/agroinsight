# alerts.py

def send_sms(phone_number, message):
    # TODO: integrate with SMS gateway like Twilio, Africa's Talking, or local SMS provider
    print(f"Sending SMS to {phone_number}: {message}")

def alert_farmers(farmers, message):
    for farmer in farmers:
        send_sms(farmer['phone'], message)
