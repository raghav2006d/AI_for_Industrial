import re
from typing import Dict

DATE_REGEX = re.compile(r"\b(20\d{2}[-/\.](?:0?[1-9]|1[0-2])[-/\.](?:0?[1-9]|[12]\d|3[01]))\b")
ALT_DATE_REGEX = re.compile(r"\b((?:0?[1-9]|[12]\d|3[01])[-/\.](?:0?[1-9]|1[0-2])[-/\.](20\d{2}))\b")
KWH_REGEX = re.compile(r"(?i)\b([\d,.]+)\s*(?:kwh|kwh\b)\b")
COST_REGEX = re.compile(r"(?i)(?:total|amount due|balance)[:\s]*([\$£€]?\s*[\d,.]+)")
VENDOR_REGEX = re.compile(r"(?im)^(?:vendor|supplier|utility)[:\s]*([\w\- &.,]+)$")
INVOICE_REGEX = re.compile(r"(?i)invoice\s*(?:no\.?|#|number)[:\s]*([\w\-]+)")


def _to_number(token: str) -> float:
    token = token.replace(",", "").replace(" ", "")
    token = token.replace("$", "").replace("€", "").replace("£", "")
    try:
        return float(token)
    except Exception:
        return 0.0


def extract_fields(text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}

    m = DATE_REGEX.search(text) or ALT_DATE_REGEX.search(text)
    if m:
        fields["DATE"] = m.group(0)

    m = KWH_REGEX.search(text)
    if m:
        fields["KWH"] = m.group(1)

    m = COST_REGEX.search(text)
    if m:
        fields["COST"] = m.group(1).strip()

    m = VENDOR_REGEX.search(text)
    if m:
        fields["VENDOR_NAME"] = m.group(1).strip()

    m = INVOICE_REGEX.search(text)
    if m:
        fields["INVOICE_NO"] = m.group(1).strip()

    return fields


def extract_numeric(fields: Dict[str, str]) -> Dict[str, float]:
    return {
        "kwh": _to_number(fields.get("KWH", "0")),
        "cost": _to_number(fields.get("COST", "0")),
    }