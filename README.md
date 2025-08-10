# AI-powered Carbon Emissions Auditing Web App (MVP)

This is a minimal end-to-end web app that:
- Accepts document uploads (PDF/images)
- Runs OCR (best-effort: pdf text extraction, optional Tesseract for images)
- Extracts key fields with simple rules (placeholder for BERT/LayoutLM)
- Computes Scope 2 electricity emissions from kWh
- Runs basic validation checks
- Generates an HTML and Excel report

## Quickstart

1. Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Open the UI at http://localhost:8000

Uploaded files and outputs are stored under `/workspace/app_storage` by default.

## Notes
- OCR: For best results on scanned images, install `tesseract-ocr` on your system. The app gracefully falls back to PDF embedded text extraction when possible.
- NLP: The extractor is rule-based for the MVP. Replace `app/pipeline/nlp.py` with a Hugging Face model for production.
- Reports: Generates HTML and Excel (no PDF dependency to keep setup light). Convert HTML to PDF as needed.

## Project Structure
```
app/
  main.py
  db.py
  models.py
  pipeline/
    ocr.py
    nlp.py
    emissions.py
    validation.py
    report.py
  templates/
    base.html
    index.html
    detail.html
    report.html
  static/
    style.css
app_storage/
  uploads/
  ocr/
  reports/
```