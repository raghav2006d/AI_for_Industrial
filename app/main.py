from __future__ import annotations
import os
import shutil
from datetime import datetime
from typing import List

from fastapi import FastAPI, UploadFile, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlmodel import select

from .db import init_db, get_session
from .models import Document
from .pipeline.ocr import extract_text
from .pipeline.nlp import extract_fields, extract_numeric
from .pipeline.emissions import compute_emissions
from .pipeline.validation import validate
from .pipeline.report import generate_html_report, generate_excel_report

app = FastAPI(title="Carbon Emissions Auditing Web App (MVP)")

templates = Jinja2Templates(directory="/workspace/app/templates")
app.mount("/static", StaticFiles(directory="/workspace/app/static"), name="static")

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/workspace/app_storage")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
OCR_DIR = os.path.join(STORAGE_DIR, "ocr")
REPORTS_DIR = os.path.join(STORAGE_DIR, "reports")

for d in (STORAGE_DIR, UPLOADS_DIR, OCR_DIR, REPORTS_DIR):
    os.makedirs(d, exist_ok=True)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    with get_session() as session:
        docs: List[Document] = session.exec(select(Document).order_by(Document.uploaded_at.desc())).all()
    return templates.TemplateResponse("index.html", {"request": request, "docs": docs})


@app.post("/upload")
async def upload(request: Request, file: UploadFile, background_tasks: BackgroundTasks):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    original_name = file.filename or "upload"
    ext = os.path.splitext(original_name)[1]
    # Use a temp file then atomic move
    tmp_path = os.path.join(UPLOADS_DIR, f"tmp_{datetime.utcnow().timestamp()}_{original_name}")
    final_basename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{ext}"
    final_path = os.path.join(UPLOADS_DIR, final_basename)

    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    os.replace(tmp_path, final_path)

    doc = Document(
        filename=original_name,
        content_type=file.content_type or "application/octet-stream",
        storage_path=final_path,
        status="queued",
    )

    with get_session() as session:
        session.add(doc)
        session.commit()
        session.refresh(doc)

    background_tasks.add_task(_process_document, doc.id)

    return RedirectResponse(url=f"/documents/{doc.id}", status_code=303)


@app.get("/documents/{doc_id}", response_class=HTMLResponse)
def document_detail(doc_id: str, request: Request):
    with get_session() as session:
        doc = session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
    return templates.TemplateResponse("detail.html", {"request": request, "doc": doc})


@app.get("/reports/{doc_id}/{kind}")
def download_report(doc_id: str, kind: str):
    with get_session() as session:
        doc = session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
    if kind == "html" and doc.report_html_path:
        return FileResponse(doc.report_html_path, media_type="text/html", filename=f"report_{doc_id}.html")
    if kind == "xlsx" and doc.report_xlsx_path:
        return FileResponse(doc.report_xlsx_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"report_{doc_id}.xlsx")
    raise HTTPException(status_code=404, detail="Report not available")


def _process_document(doc_id: str) -> None:
    with get_session() as session:
        doc = session.get(Document, doc_id)
        if not doc:
            return
        doc.status = "processing"
        session.add(doc)
        session.commit()

    try:
        # OCR
        text = extract_text(doc.storage_path)
        ocr_path = os.path.join(OCR_DIR, f"{doc.id}.txt")
        with open(ocr_path, "w", encoding="utf-8") as f:
            f.write(text)

        # NLP extraction
        fields = extract_fields(text)
        numeric = extract_numeric(fields)

        # Emissions calculation
        emissions = compute_emissions(fields)

        # Validation
        flags = validate(fields, numeric, emissions)

        # Reports
        context = {
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "uploaded_at": doc.uploaded_at,
            },
            "fields": fields,
            "numeric": numeric,
            "emissions": emissions,
            "flags": flags,
        }
        html_report_path = os.path.join(REPORTS_DIR, f"{doc.id}.html")
        xlsx_report_path = os.path.join(REPORTS_DIR, f"{doc.id}.xlsx")
        generate_html_report(context, template_dir="/workspace/app/templates", template_name="report.html", out_path=html_report_path)
        generate_excel_report(context, out_path=xlsx_report_path)

        # Persist
        with get_session() as session:
            doc = session.get(Document, doc_id)
            if not doc:
                return
            doc.ocr_text_path = ocr_path
            doc.extraction = fields
            doc.emissions = emissions
            doc.flags = flags
            doc.report_html_path = html_report_path
            doc.report_xlsx_path = xlsx_report_path
            doc.status = "completed"
            doc.processed_at = datetime.utcnow()
            session.add(doc)
            session.commit()

    except Exception as exc:  # pragma: no cover
        with get_session() as session:
            doc = session.get(Document, doc_id)
            if not doc:
                return
            doc.status = "failed"
            doc.error_message = str(exc)
            session.add(doc)
            session.commit()