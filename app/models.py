from typing import Optional, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON
import uuid


class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    company_id: str = Field(default="demo")

    filename: str
    content_type: str
    storage_path: str

    status: str = Field(default="queued")  # queued, processing, completed, failed
    error_message: Optional[str] = None

    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    ocr_text_path: Optional[str] = None

    extraction: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    emissions: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    flags: Optional[Any] = Field(default=None, sa_column=Column(JSON))

    report_html_path: Optional[str] = None
    report_xlsx_path: Optional[str] = None