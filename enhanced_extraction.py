# enhanced_extraction.py
# Enhanced document extraction with page tracking and metadata
# This file contains updated extraction functions to replace the ones in chat bot 3 api.py

from typing import List, Dict
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_paragraphs_from_pdf_enhanced(path: str) -> List[Dict]:
    """
    Extract paragraphs from PDF with page tracking and metadata
    
    Returns:
        List of dicts: [{'text': str, 'page_number': int, 'word_count': int}, ...]
    """
    try:
        doc = fitz.open(path)
    except Exception as e:
        logger.exception("Failed to open PDF: %s", path)
        return []
    
    chunks = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if not text:
            continue
        
        # Split into paragraphs
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not parts:
            parts = [line.strip() for line in text.splitlines() if line.strip()]
        
        # Create structured chunks with metadata
        for para_text in parts:
            if para_text:
                chunks.append({
                    'text': para_text,
                    'page_number': page_num,
                    'word_count': len(para_text.split()),
                    'char_count': len(para_text)
                })
    
    logger.info("Extracted %d chunks from %d pages in PDF %s", len(chunks), doc.page_count, path)
    return chunks


def extract_text_from_txt_enhanced(path: str) -> List[Dict]:
    """Extract text from TXT file with metadata"""
    try:
        with open(path, 'r', encoding='utf-8') as file:
            text = file.read()
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paras:
            paras = [line.strip() for line in text.splitlines() if line.strip()]
        
        # Convert to structured chunks (no page numbers for TXT)
        chunks = []
        for para_text in paras:
            if para_text:
                chunks.append({
                    'text': para_text,
                    'page_number': None,  # TXT files don't have pages
                    'word_count': len(para_text.split()),
                    'char_count': len(para_text)
                })
        
        logger.info("Extracted %d chunks from TXT %s", len(chunks), path)
        return chunks
    except Exception:
        logger.exception("Failed to read TXT file: %s", path)
        return []


def extract_text_from_docx_enhanced(path: str) -> List[Dict]:
    """Extract text from DOCX with metadata"""
    try:
        import docx
        doc = docx.Document(path)
        chunks = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                chunks.append({
                    'text': text,
                    'page_number': None,  # DOCX doesn't have reliable page numbers
                    'word_count': len(text.split()),
                    'char_count': len(text)
                })
        logger.info("Extracted %d chunks from DOCX %s", len(chunks), path)
        return chunks
    except Exception:
        logger.exception("Failed to read DOCX file: %s", path)
        return []


def extract_text_from_file_enhanced(path: str) -> List[Dict]:
    """Extract text from any supported file format, returns structured chunks"""
    file_extension = path.split('.')[-1].lower()
    if file_extension == 'pdf':
        return extract_paragraphs_from_pdf_enhanced(path)
    elif file_extension == 'txt':
        return extract_text_from_txt_enhanced(path)
    elif file_extension in ['doc', 'docx']:
        return extract_text_from_docx_enhanced(path)
    else:
        logger.warning("Unsupported file type for text extraction: %s", file_extension)
        return []


# Helper function to convert chunks to old format (for backward compatibility)
def chunks_to_paragraphs(chunks: List[Dict]) -> List[str]:
    """Convert new chunk format to old paragraph list format"""
    return [chunk['text'] for chunk in chunks]
