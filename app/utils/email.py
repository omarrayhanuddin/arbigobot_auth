import aiosmtplib
from email.mime.text import MIMEText
from ..config import settings

async def send_verification_email(email: str, token: str):
    msg = MIMEText(f"Click to verify: {settings.SITE_URL}/verify-email?token={token}")
    msg["Subject"] = "Verify Your Email"
    msg["From"] = settings.SENDER_EMAIL
    msg["To"] = email

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_SERVER,
        port=settings.SMTP_PORT,
        username=settings.SENDER_EMAIL,
        password=settings.SENDER_PASSWORD,
        use_tls=False,
        start_tls=True
    )