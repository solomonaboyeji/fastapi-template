from email.mime.text import MIMEText
import os
import smtplib
from email.mime.multipart import MIMEMultipart

from loguru import logger

from core.config import (
    EMAIL_ADDRESS,
    EMAIL_FROM_NAME,
    EMAIL_HOST,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    TESTING,
)
from utils.errors import EmailException


def send_email(subject: str, to_email: str, body: str):
    # get the latest value
    under_testing = os.getenv("TESTING", TESTING)
    if under_testing.lower() == "true":
        logger.info(f"Subject: {subject}\nTo: {to_email}\nMessage: {body}")
        return

    msg = MIMEMultipart()
    msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
    except Exception as e:
        logger.error(e)
        raise EmailException("Failed to send email for email confirmation")
