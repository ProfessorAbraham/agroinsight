# alerts.py

YOUR_PHONE_NUMBER = "+251912345678"  # Replace with your demo sender number

# Store sent messages for display
sent_messages = []

def send_sms(phone_number, message):
    sms_text = f"[SMS MOCK] From: {YOUR_PHONE_NUMBER} To: {phone_number}\nMessage: {message}\n"
    print(sms_text)
    sent_messages.append(sms_text)

def alert_farmers(farmers, message):
    for farmer in farmers:
        send_sms(farmer['phone'], message)

def display_sent_messages():
    # For Jupyter or Colab, pretty print all sent SMS messages
    from IPython.display import display, Markdown
    if not sent_messages:
        print("No SMS messages sent yet.")
        return
    combined = "\n---\n".join(sent_messages)
    display(Markdown(f"### Sent SMS Messages\n\n```\n{combined}\n```"))
