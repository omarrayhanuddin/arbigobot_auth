from pathlib import Path
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

async def send_otp_verification_email(email: str, otp: str, is_pwd=False):
    message = "This is your email verification code:"
    if is_pwd:
        message = "This is your password reset link:"
        otp = f"https://arbigobot.com/admin/reset-password/{otp}"

    email_template_folder = Path(__file__).parent.parent.joinpath("templates")
    try:
        with open(f"{email_template_folder}/otp.html", "r", encoding="utf-8") as f:
            html_body = f.read()
    except FileNotFoundError:
        print(f"Error: HTML template file not found at {email_template_folder}/otp.html")
        return

    html_body = html_body.replace("{{ otp_code }}", otp).replace("{{ heading }}", message)

    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "Verify Your Email"
    msg["From"] = settings.SENDER_EMAIL
    msg["To"] = email

    # 4. Send the email
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            username=settings.SENDER_EMAIL,
            password=settings.SENDER_PASSWORD,
            use_tls=False,
            start_tls=True
        )
        print(f"Verification email sent to {email}")
    except aiosmtplib.SMTPException as e:
        print(f"Error sending email to {email}: {e}")


