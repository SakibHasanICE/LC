from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentPage, LetterOfCredit
from app.db.session import get_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="LC Automation API", lifespan=lifespan)


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lc_id: int | None
    doc_type: str
    bank: str | None
    file_name: str
    status: str
    extraction_method: str | None
    confidence: float | None
    error: str | None
    page_count: int | None
    normalized: dict
    extracted: dict
    created_at: datetime


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page_no: int
    text: str
    tables: list


class LCOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lc_number: str
    bank: str | None
    applicant: str | None
    beneficiary: str | None
    currency: str | None
    amount: float | None


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok"}


@app.get("/documents", response_model=list[DocumentOut])
def list_documents(
    doc_type: str | None = None,
    bank: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = select(Document).order_by(Document.id.desc()).limit(limit).offset(offset)
    if doc_type:
        q = q.where(Document.doc_type == doc_type)
    if bank:
        q = q.where(Document.bank == bank)
    if status:
        q = q.where(Document.status == status)
    return db.scalars(q).all()


@app.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@app.get("/documents/{doc_id}/pages", response_model=list[PageOut])
def get_pages(doc_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(DocumentPage).where(DocumentPage.document_id == doc_id).order_by(DocumentPage.page_no)
    ).all()


@app.get("/lcs", response_model=list[LCOut])
def list_lcs(limit: int = Query(50, le=500), offset: int = 0, db: Session = Depends(get_db)):
    return db.scalars(select(LetterOfCredit).order_by(LetterOfCredit.id.desc()).limit(limit).offset(offset)).all()


@app.get("/lcs/{lc_number}/documents", response_model=list[DocumentOut])
def lc_documents(lc_number: str, db: Session = Depends(get_db)):
    lc = db.scalar(select(LetterOfCredit).where(LetterOfCredit.lc_number == lc_number))
    if not lc:
        raise HTTPException(404, "LC not found")
    return lc.documents