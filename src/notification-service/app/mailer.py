from email.mime.text import MIMEText
from smtplib import SMTP, SMTPException

from jinja2 import FileSystemLoader, Environment, TemplateError

from app import logger
from app.config import settings


def render_template(template_file: str, data: dict) -> str:
    try:
        logger.info(f"rendering template {template_file}")
        template_loader = FileSystemLoader(searchpath="./")
        env = Environment(loader=template_loader, autoescape=True)

        output = env.get_template(template_file).render(data)
        return output

    except TemplateError:
        logger.error("template rendering failed", exc_info=True)
        raise
    except Exception:
        logger.error("unexpected template rendering error", exc_info=True)
        raise


def send_mail(receiver: str, subject: str, message: str):
    try:
        logger.info(f"sending email to {receiver}")
        msg = MIMEText(message, 'html')
        msg['Subject'] = subject
        msg['From'] = settings.MAIL_DEFAULT_SENDER
        msg['To'] = receiver

        with SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_DEFAULT_SENDER, receiver, msg.as_string())

        logger.info("email successfully sent")

    except SMTPException:
        logger.error("smtp error occurred", exc_info=True)
        raise
    except TimeoutError:
        logger.error("smtp timeout", exc_info=True)
        raise
    except Exception:
        logger.error("unexpected email send error", exc_info=True)
        raise


def notify(message):
    try:
        logger.info("processing notify request")

        rendered = render_template('app/demo.html', {"mp3_fid": message.get("mp3_fid")})
        send_mail(message.get("email"), 'Download mp3', rendered)

        logger.info("email notification complete")
        return None

    except Exception:
        logger.error("notify failed", exc_info=True)
        return True
