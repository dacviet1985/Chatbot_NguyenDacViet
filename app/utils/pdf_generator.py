from __future__ import annotations

from pathlib import Path


PDF_HEADER = "%PDF-1.4\n"


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(path: Path, pages: list[str]) -> None:
    """Write a minimal text-only PDF file that can be parsed by pypdf."""

    objects: list[str] = []
    kids: list[str] = []
    font_object_id = 3 + len(pages) * 2

    objects.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    for page_index, page_text in enumerate(pages, start=0):
        page_object_id = 3 + page_index * 2
        content_object_id = 4 + page_index * 2
        kids.append(f"{page_object_id} 0 R")
        objects.append(
            f"{page_object_id} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> /Contents {content_object_id} 0 R >> endobj\n"
        )
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        stream_lines = ["BT", "/F1 12 Tf", "72 720 Td"]
        for line_index, line in enumerate(lines):
            safe_line = _escape_pdf_text(line)
            if line_index == 0:
                stream_lines.append(f"({safe_line}) Tj")
            else:
                stream_lines.append(f"0 -18 Td ({safe_line}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines)
        objects.append(
            f"{content_object_id} 0 obj << /Length {len(stream.encode('utf-8'))} >> stream\n{stream}\nendstream endobj\n"
        )

    objects.insert(1, f"2 0 obj << /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >> endobj\n")
    objects.append(f"{font_object_id} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")

    content = PDF_HEADER
    offsets = [0]
    for obj in objects:
        offsets.append(len(content.encode("utf-8")))
        content += obj

    xref_offset = len(content.encode("utf-8"))
    object_count = len(objects)
    content += f"xref\n0 {object_count + 1}\n"
    content += "0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n"
    content += (
        f"trailer << /Size {object_count + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    )
    path.write_bytes(content.encode("utf-8"))
