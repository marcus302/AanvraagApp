import email.message
import smtplib
from aanvraagapp.config import LocalMailSettings


async def send_email_mailhog(email_addr: str, message: str, subject: str, settings: LocalMailSettings):
    server = smtplib.SMTP(settings.server, settings.port)
    server.login(settings.username, settings.password)
    email_message = email.message.Message()
    email_message["From"] = settings.from_name
    email_message["To"] = email_addr
    email_message["Subject"] = subject
    email_message.set_payload(message)
    response = server.sendmail(
        settings.from_email, email_addr, email_message.as_string()
    )
    if response:
        raise Exception(response)
    server.quit()
