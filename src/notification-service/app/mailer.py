from email.mime.text import MIMEText
from smtplib import SMTP, SMTPException

from jinja2 import FileSystemLoader, Environment, TemplateError

from app import logger
from app.config import settings

import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.db import SessionLocal, Notification
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


def notify(message: dict):
    db: Session = SessionLocal()
    notif = None
    try:
        logger.info("processing notify request")

        # 1. создаём запись в БД со статусом queued
        notif = Notification(
            user_id=message.get("user_id"),
            email=message.get("email"),
            subject="Download mp3",
            template_name="app/demo.html",
            payload_json=json.dumps(message),
            status="queued",
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        # 2. рендер и отправка письма
        rendered = render_template('app/demo.html', {"mp3_fid": message.get("mp3_fid")})
        send_mail(message.get("email"), 'Download mp3', rendered)

        # 3. обновляем запись как sent
        notif.status = "sent"
        notif.sent_at = datetime.utcnow()
        notif.updated_at = datetime.utcnow()
        db.add(notif)
        db.commit()

        logger.info("email notification complete")
        return None

    except Exception as e:
        logger.error("notify failed", exc_info=True)
        if notif is not None:
            notif.status = "failed"
            notif.error_message = str(e)
            notif.updated_at = datetime.utcnow()
            db.add(notif)
            db.commit()
        return True
    finally:
        db.close()
