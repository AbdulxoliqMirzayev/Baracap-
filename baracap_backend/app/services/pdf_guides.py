from __future__ import annotations

from pathlib import Path


GUIDES_DIR = Path(__file__).resolve().parents[1] / "static" / "guides"

GUIDE_FILES = {
    "simple": {
        "path": GUIDES_DIR / "moliyaviy-tartib.pdf",
        "filename": "Moliyaviy savodxonlik bo'yicha sodda qo'llanma.pdf",
    },
    "professional": {
        "path": GUIDES_DIR / "moliyaviy-tartib-qollanmasi.pdf",
        "filename": "Moliyaviy savodxonlik bo'yicha professional qo'llanma.pdf",
    },
}


def build_guide_pdf(guide_type: str, language: str | None = None) -> bytes:
    guide = GUIDE_FILES[guide_type]
    return guide["path"].read_bytes()


def guide_filename(guide_type: str) -> str:
    return str(GUIDE_FILES[guide_type]["filename"])
