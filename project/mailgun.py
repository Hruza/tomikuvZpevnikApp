from logging import getLogger

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage

HTTP_TIMEOUT = 10
HTTP_STATUS_OK = 200

logger = getLogger("tomikuvzpevnik")


class MailgunBackend(BaseEmailBackend):
    def send_messages(self, email_messages: list[EmailMessage]) -> int:
        sent_count = 0
        for email_message in email_messages:
            try:
                self.send_email(email_message)
                sent_count += 1
            except (requests.HTTPError, ConnectionError):  # noqa: PERF203
                if not self.fail_silently:
                    raise
        return sent_count

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send_email(self, email_message: EmailMessage) -> None:
        try:
            data = {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": email_message.to,
                "subject": email_message.subject,
            }
            if email_message.cc:
                data["cc"] = email_message.cc
            if email_message.bcc:
                data["bcc"] = email_message.bcc
            if email_message.content_subtype == "html":
                data["html"] = email_message.body
            else:
                data["text"] = email_message.body

            response = requests.post(
                f"https://api.eu.mailgun.net/v3/{settings.EMAIL_HOST_USER}/messages",
                auth=("api", settings.EMAIL_HOST_PASSWORD),
                data=data,
                timeout=HTTP_TIMEOUT,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            msg = "Failed to send email via Mailgun"
            logger.exception(msg)
            raise ConnectionError(msg) from e



