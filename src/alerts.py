# alerts.py

_sent_messages = []

def send_sms(phone_number, message):
    # Mock SMS send - just log it
    msg = f"[SMS MOCK] From: +251912345678 To: {phone_number}\nMessage: {message}\n"
    print(msg)
    _sent_messages.append(msg)

def alert_farmers(farmers, message):
    for farmer in farmers:
        send_sms(farmer['phone'], message)

def display_sent_messages():
    if _sent_messages:
        print("\n=== All Sent SMS Messages ===")
        for msg in _sent_messages:
            print(msg)
    else:
        print("No SMS messages sent yet.")
