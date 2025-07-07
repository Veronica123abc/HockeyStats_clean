import smtplib
from email.message import EmailMessage
import os

def send_email():
    # Email content
    sender_email = "icehockeysecrets@gmail.com"
    sender_password = "asfyvcgbfebjcmgq"

    recipient_email = "veronica.eriksson580@gmail.com"
    subject = "Hello"
    body = "How are you"
    attachment_path = "/home/veronica/repos/HockeyStats_clean/a.csv"

    # Create the email
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)

    # Attach the file
    if os.path.exists(attachment_path):
        with open(attachment_path, "rb") as file:
            file_data = file.read()
            file_name = os.path.basename(attachment_path)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)
    else:
        print(f"Attachment not found: {attachment_path}")
        return

    # Send the email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_email()