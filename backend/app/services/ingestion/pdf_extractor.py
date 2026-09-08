import re
from typing import List, Dict, Any, Tuple, Optional
import pymupdf
from app.services.ingestion.hasher import compute_text_hash
from app.core.logging import logger


class ExtractedPageData:
    def __init__(
        self,
        page_number: int,
        raw_text: str,
        has_tables: bool,
        is_scanned: bool,
        evidence_atoms: List[Dict[str, Any]],
        issues: List[Dict[str, Any]]
    ):
        self.page_number = page_number
        self.raw_text = raw_text
        self.has_tables = has_tables
        self.is_scanned = is_scanned
        self.evidence_atoms = evidence_atoms
        self.issues = issues


class PDFExtractor:
    """Extracts structured text, layout blocks, tables, and evidence atoms from PDF documents."""

    def __init__(self, min_atom_chars: int = 3, max_atom_chars: int = 1000):
        self.min_atom_chars = min_atom_chars
        self.max_atom_chars = max_atom_chars

    def extract_document(self, pdf_bytes: bytes) -> Tuple[List[ExtractedPageData], int]:
        """Process an entire PDF stream and return extracted page data and total page count."""
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        pages_data: List[ExtractedPageData] = []

        for pno in range(page_count):
            page = doc[pno]
            page_data = self.extract_page(page, pno + 1)
            pages_data.append(page_data)

        doc.close()
        return pages_data, page_count

    def extract_page(self, page: pymupdf.Page, page_number: int) -> ExtractedPageData:
        """Extracts text, detected tables, and evidence atoms for a single page."""
        raw_text = page.get_text() or ""
        raw_text_clean = raw_text.strip()
        issues: List[Dict[str, Any]] = []
        evidence_atoms: List[Dict[str, Any]] = []

        # 1. Scanned page / OCR check
        images = page.get_images()
        is_scanned = len(raw_text_clean) < 30 and len(images) > 0
        if is_scanned:
            # Check if OCR can be performed via PyMuPDF OCR
            ocr_performed = False
            try:
                # If pymupdf with tesseract/OCR support is available
                textpage = page.get_textpage_ocr(flags=0, language='eng')
                ocr_text = textpage.extractText()
                if ocr_text and len(ocr_text.strip()) > 30:
                    raw_text = ocr_text
                    raw_text_clean = ocr_text.strip()
                    ocr_performed = True
            except Exception as ocr_err:
                logger.debug(f"OCR not available or failed on page {page_number}: {ocr_err}")

            if not ocr_performed:
                issues.append({
                    "issue_type": "OCR_FAILURE",
                    "description": f"Page {page_number} appears to be a scanned image with minimal digital text ({len(raw_text_clean)} chars) and OCR engine was unable to extract high-confidence text.",
                    "affected_text": raw_text_clean[:200] if raw_text_clean else None,
                    "attempted_resolution": "Flagged page for OCR inspection without inventing synthetic text.",
                    "status": "UNRESOLVED"
                })

        # 2. Detect Tables
        has_tables = False
        table_bboxes = []
        try:
            tab_finder = page.find_tables()
            if tab_finder and len(tab_finder.tables) > 0:
                has_tables = True
                for t_idx, table in enumerate(tab_finder.tables):
                    t_bbox = list(table.bbox)
                    table_bboxes.append(t_bbox)
                    
                    # Extract header row
                    headers = [str(h).strip() if h is not None else f"Col_{i}" for i, h in enumerate(table.header.names)] if table.header else []
                    
                    # Extract rows
                    table_data = table.extract()
                    for r_idx, row in enumerate(table_data):
                        # Construct a coherent table row snippet
                        row_items = []
                        for c_idx, cell_val in enumerate(row):
                            if cell_val is not None and str(cell_val).strip():
                                col_name = headers[c_idx] if c_idx < len(headers) else f"Col_{c_idx}"
                                row_items.append(f"{col_name}: {str(cell_val).strip()}")
                        
                        if not row_items:
                            continue
                            
                        exact_row_text = " | ".join(row_items)
                        if len(exact_row_text) < 10:
                            continue

                        # Calculate char offset if found in raw_text
                        char_start = raw_text.find(str(row[0]).strip()) if row and row[0] else -1
                        char_end = char_start + len(exact_row_text) if char_start != -1 else None

                        evidence_atoms.append({
                            "page_number": page_number,
                            "section_heading": f"Table {t_idx + 1}",
                            "exact_text": exact_row_text,
                            "char_start": char_start if char_start != -1 else None,
                            "char_end": char_end,
                            "bbox": [round(coord, 2) for coord in t_bbox],
                            "table_cell_info": {
                                "table_index": t_idx + 1,
                                "row_index": r_idx,
                                "headers": headers,
                                "raw_cells": [str(c).strip() if c is not None else "" for c in row]
                            },
                            "extraction_method": "table_parser",
                            "source_hash": compute_text_hash(exact_row_text)
                        })
        except Exception as t_err:
            logger.debug(f"Table detection notice on page {page_number}: {t_err}")

        # 3. Extract Text Blocks & Paragraphs
        try:
            blocks = page.get_text("blocks")
            current_heading: Optional[str] = None

            for block in blocks:
                # block: (x0, y0, x1, y1, text, block_no, block_type)
                if len(block) < 5:
                    continue
                x0, y0, x1, y1, b_text = block[0], block[1], block[2], block[3], block[4]
                b_text_clean = b_text.strip()
                if not b_text_clean:
                    continue

                # Heading heuristic: short line, uppercase or title-case, no trailing period
                if len(b_text_clean) < 90 and "\n" not in b_text_clean:
                    if b_text_clean.isupper() or (b_text_clean.istitle() and not b_text_clean.endswith(".")):
                        current_heading = b_text_clean
                        continue

                # Skip if this block is entirely inside a detected table bounding box
                is_in_table = False
                for tbox in table_bboxes:
                    if x0 >= tbox[0] - 5 and y0 >= tbox[1] - 5 and x1 <= tbox[2] + 5 and y1 <= tbox[3] + 5:
                        is_in_table = True
                        break
                if is_in_table:
                    continue

                # Split block into paragraphs while strictly preserving exact substrings
                paragraphs = [p.strip() for p in re.split(r'\n\s*\n', b_text) if p.strip()]
                for para in paragraphs:
                    if len(para) < self.min_atom_chars:
                        continue

                    # Exact substring match in raw_text for grounding
                    char_start = raw_text.find(para)
                    if char_start == -1:
                        char_start = raw_text.find(para[:30])
                    char_end = char_start + len(para) if char_start != -1 else None

                    evidence_atoms.append({
                        "page_number": page_number,
                        "section_heading": current_heading,
                        "exact_text": para,
                        "char_start": char_start if char_start != -1 else None,
                        "char_end": char_end,
                        "bbox": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                        "table_cell_info": None,
                        "extraction_method": "native_text",
                        "source_hash": compute_text_hash(para)
                    })

            # 4. Generate visual card compound atoms for adjacent value-label pairs
            for i in range(len(blocks) - 1):
                b1_text = blocks[i][4].strip()
                b2_text = blocks[i+1][4].strip()
                # If one block has digits and is short, combine with adjacent block
                has_num_1 = any(c.isdigit() for c in b1_text) and len(b1_text) < 40
                has_num_2 = any(c.isdigit() for c in b2_text) and len(b2_text) < 40
                if (has_num_1 or has_num_2) and len(b1_text) > 1 and len(b2_text) > 1:
                    compound = f"{b1_text}\n{b2_text}"
                    c_start = raw_text.find(b1_text)
                    c_end = c_start + len(compound) if c_start != -1 else None
                    evidence_atoms.append({
                        "page_number": page_number,
                        "section_heading": current_heading,
                        "exact_text": compound,
                        "char_start": c_start if c_start != -1 else None,
                        "char_end": c_end,
                        "bbox": [round(blocks[i][0], 2), round(blocks[i][1], 2), round(blocks[i+1][2], 2), round(blocks[i+1][3], 2)],
                        "table_cell_info": None,
                        "extraction_method": "compound_card",
                        "source_hash": compute_text_hash(compound)
                    })

        except Exception as b_err:
            logger.error(f"Error extracting blocks on page {page_number}: {b_err}")
            issues.append({
                "issue_type": "PDF_EXTRACTION_FAILURE",
                "description": f"Failed to parse text blocks on page {page_number}: {str(b_err)}",
                "affected_text": None,
                "attempted_resolution": "Captured raw text only.",
                "status": "DETECTED"
            })

        return ExtractedPageData(
            page_number=page_number,
            raw_text=raw_text,
            has_tables=has_tables,
            is_scanned=is_scanned,
            evidence_atoms=evidence_atoms,
            issues=issues
        )
