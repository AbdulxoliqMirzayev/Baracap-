from __future__ import annotations


def build_guide_pdf(guide_type: str, language: str) -> bytes:
    is_professional = guide_type == "professional"
    is_ru = language == "ru"

    if is_ru:
        title = "BARACAP Financial Literacy Guide"
        subtitle = "Professional version" if is_professional else "Simple version"
        lines = [
            "This PDF is a placeholder guide.",
            "Your final PDF can be connected from the project settings.",
            "Inside the guide: budget, savings, credit and planning basics.",
            "Use it as a compact roadmap for improving financial literacy.",
        ]
    else:
        title = "BARACAP Moliyaviy Savodxonlik Qollanmasi"
        subtitle = "Professional qollanma" if is_professional else "Sodda qollanma"
        lines = [
            "Bu PDF vaqtinchalik sovga qollanmasi.",
            "Yakuniy PDF fayl keyin loyiha sozlamalariga ulanadi.",
            "Qollanmada budjet, jamgarma, kredit va reja asoslari bor.",
            "Undan moliyaviy savodxonlikni yaxshilash uchun foydalaning.",
        ]

    return _minimal_pdf([title, subtitle, "", *lines])


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _minimal_pdf(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 20 Tf", "72 760 Td"]
    for index, line in enumerate(lines):
        if index == 1:
            content_lines.extend(["/F1 14 Tf", "0 -30 Td"])
        elif index > 0:
            content_lines.append("0 -24 Td")
        content_lines.append(f"({_pdf_escape(line)}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_at = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)
