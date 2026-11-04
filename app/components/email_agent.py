"""
Email ingestion agent.

Polls a single IMAP inbox on an interval, pulls PDF attachments from
unread emails matching known bank senders, saves them to a staging
folder, and triggers the extraction pipeline for each new file.

Run standalone for testing:
    python -m app.components.email_agent
"""

import time
import json
from pathlib import Path
from typing import Callable, Optional

from imap_tools import MailBox, AND

from app.config.settings import settings
from app.common.logger import get_logger
from app.common.custom_exception import EmailFetchError, AttachmentError

logger = get_logger(__name__)

STAGING_DIR = Path(__file__).resolve().parent.parent.parent / "staging"
STAGING_DIR.mkdir(exist_ok=True)

PROCESSED_LOG = STAGING_DIR / "_processed_uids.json"

# Allowlist of senders to pull attachments from.
# Move this to bank_templates.py / DB once you have more than a couple banks.
KNOWN_BANK_SENDERS = [
 "hasansakib047@gmail.com"
 ]


class EmailAgent:
    def __init__(self, on_new_pdf: Optional[Callable[[Path, dict], None]] = None):
        """
        on_new_pdf: callback invoked with (saved PDF path, email metadata dict)
        each time a new attachment is pulled. Wire this to the extraction pipeline.
        """
        self.on_new_pdf = on_new_pdf or self._default_callback
        self._processed_uids = self._load_processed_uids()

    @staticmethod
    def _default_callback(pdf_path: Path, meta: dict) -> None:
        logger.info(f"[stub] Would process: {pdf_path.name}")

    def _load_processed_uids(self) -> set:
        if PROCESSED_LOG.exists():
            return set(json.loads(PROCESSED_LOG.read_text()))
        return set()

    def _save_processed_uids(self) -> None:
        PROCESSED_LOG.write_text(json.dumps(list(self._processed_uids)))

    def _is_allowed_sender(self, from_addr: str) -> bool:
        if not KNOWN_BANK_SENDERS:
            # No allowlist configured yet — allow everything (dev mode)
            return True
        return any(sender in from_addr for sender in KNOWN_BANK_SENDERS)

    def fetch_once(self) -> int:
        """Connects, pulls any new PDF attachments, returns count processed."""
        new_count = 0
        try:
            with MailBox(settings.IMAP_HOST, settings.IMAP_PORT).login(
                settings.IMAP_USER,
                settings.IMAP_PASSWORD,
                initial_folder=settings.IMAP_FOLDER,
            ) as mailbox:
                for msg in mailbox.fetch(AND(seen=False), mark_seen=False):
                    if msg.uid in self._processed_uids:
                        continue

                    if not self._is_allowed_sender(msg.from_):
                        logger.debug(f"Skipping email from unrecognized sender: {msg.from_}")
                        continue

                    pdf_attachments = [a for a in msg.attachments if a.filename.lower().endswith(".pdf")]
                    if not pdf_attachments:
                        continue

                    for att in pdf_attachments:
                        try:
                            saved_path = self._save_attachment(att, msg.uid)
                            new_count += 1
                            self.on_new_pdf(saved_path, {
                                "uid": msg.uid,
                                "sender": msg.from_,
                                "subject": msg.subject,
                                "date": msg.date,
                            })
                        except Exception as e:
                            raise AttachmentError(
                                f"Failed to save attachment from message {msg.uid}",
                                error_detail=e,
                            )

                    self._processed_uids.add(msg.uid)
                    mailbox.flag(msg.uid, "\\Seen", True)

            self._save_processed_uids()

        except Exception as e:
            raise EmailFetchError("Failed to fetch emails from inbox", error_detail=e)

        return new_count

    def _save_attachment(self, attachment, uid: str) -> Path:
        safe_name = f"{uid}_{attachment.filename}"
        out_path = STAGING_DIR / safe_name
        out_path.write_bytes(attachment.payload)
        logger.info(f"Saved attachment: {out_path.name}")
        return out_path

    def run_forever(self, poll_interval_seconds: int = 300) -> None:
        """Polling loop — checks the inbox every poll_interval_seconds."""
        logger.info(f"Starting email agent. Polling every {poll_interval_seconds}s.")
        while True:
            try:
                count = self.fetch_once()
                if count:
                    logger.info(f"Processed {count} new invoice PDF(s).")
                else:
                    logger.debug("No new invoices found.")
            except EmailFetchError as e:
                logger.error(str(e))
            except Exception as e:
                logger.exception(f"Unexpected error in email agent loop: {e}")

            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    from app.pipeline import process_pdf

    settings.validate()
    agent = EmailAgent(on_new_pdf=process_pdf)
    agent.run_forever(poll_interval_seconds=60)