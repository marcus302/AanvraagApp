import email.message
import smtplib


async def send_email_mailhog(email_addr: str, message: str, subject: str):
    server = smtplib.SMTP("mail", 1025)
    server.login("mark", "mark")
    email_message = email.message.Message()
    email_message["From"] = "mark@aanvraagapp.nl"
    email_message["To"] = email_addr
    email_message["Subject"] = subject
    email_message.set_payload(message)
    response = server.sendmail(
        "mark@aanvraagapp.nl", email_addr, email_message.as_string()
    )
    if response:
        raise Exception(response)
    server.quit()
