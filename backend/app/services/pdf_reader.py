"""
services/pdf_reader.py
Extracts plain text from a college brochure/prospectus PDF
(app/dataset/college.pdf) so it can be used as extra chatbot
knowledge or searched for keyword answers.
"""
import os
from typing import List
from PyPDF2 import PdfReader

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset")
PDF_PATH = os.path.join(DATASET_DIR, "college.pdf")


def extract_text_from_pdf(pdf_path: str = PDF_PATH) -> str:
    """Returns the full extracted text of the PDF (empty string if missing)."""
    if not os.path.exists(pdf_path):
        return ""
    reader = PdfReader(pdf_path)
    text_parts: List[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def search_pdf_for_keyword(keyword: str, pdf_path: str = PDF_PATH, context_chars: int = 200) -> List[str]:
    """Returns short text snippets around each occurrence of `keyword` in the PDF."""
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return []
    keyword_lower = keyword.lower()
    text_lower = text.lower()
    snippets = []
    start = 0
    while True:
        idx = text_lower.find(keyword_lower, start)
        if idx == -1:
            break
        snippet_start = max(0, idx - context_chars // 2)
        snippet_end = min(len(text), idx + len(keyword) + context_chars // 2)
        snippets.append(text[snippet_start:snippet_end].strip())
        start = idx + len(keyword)
    return snippets
