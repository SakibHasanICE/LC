from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    String, Text, Numeric, Date, DateTime, ForeignKey, Float, Integer, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# doc_type: MT700 | MT799 | CHARGES_ADVICE | PACS008 | UNKNOWN
# status:   extracted | needs_review | failed | pending_extraction


class LetterOfCredit(Base):
    """One row per LC; the LC number links MT700, MT799, charges advices, transfers."""
    __tablename__ = "letters_of_credit"

    id: Mapped[int] = mapped_column(primary_key=True)
    lc_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    bank: Mapped[str | None] = mapped_column(String(32))
    applicant: Mapped[str | None] = mapped_column(Text)
    beneficiary: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(3))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    latest_shipment_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    documents: Mapped[list["Document"]] = relationship(back_populates="lc")


class Document(Base):
    """One row per PDF attachment."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    lc_id: Mapped[int | None] = mapped_column(ForeignKey("letters_of_credit.id", ondelete="SET NULL"), index=True)

    doc_type: Mapped[str] = mapped_column(String(32), index=True)
    bank: Mapped[str | None] = mapped_column(String(32), index=True)

    # provenance
    email_uid: Mapped[str | None] = mapped_column(String(64), index=True)
    email_sender: Mapped[str | None] = mapped_column(String(255))
    email_subject: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(Text)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)  # sha256 -> dedupe
    page_count: Mapped[int | None] = mapped_column(Integer)

    # content: nothing is thrown away
    raw_text: Mapped[str | None] = mapped_column(Text)               # full text, all pages
    extracted: Mapped[dict] = mapped_column(JSONB, default=dict)     # {"swift": {...}, "key_values": {...}}
    normalized: Mapped[dict] = mapped_column(JSONB, default=dict)    # canonical fields (lc_number, ...)

    extraction_method: Mapped[str | None] = mapped_column(String(16))  # rules | llm | none
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="extracted", index=True)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lc: Mapped["LetterOfCredit | None"] = relationship(back_populates="documents")
    pages: Mapped[list["DocumentPage"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentPage.page_no"
    )


class DocumentPage(Base):
    """Per-page text and tables, exactly as read from the PDF."""
    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_no: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, default="")
    tables: Mapped[list] = mapped_column(JSONB, default=list)

    document: Mapped["Document"] = relationship(back_populates="pages")


Index("ix_documents_extracted_gin", Document.extracted, postgresql_using="gin")
Index("ix_documents_normalized_gin", Document.normalized, postgresql_using="gin")