# SPDX-License-Identifier: MIT
"""Helpers for the functional tests (Pillow and stdlib only for bookkeeping)."""

import base64
import re
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

WIDTH, HEIGHT = 7, 5


def make_image(seed: int) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT))
    img.putdata([((i + seed) * 53 % 256, (i * seed + 7) % 256, (i * 29 + seed) % 256) for i in range(WIDTH * HEIGHT)])
    return img


def data_uri(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def embedded_pixels(text: str) -> list:
    out = []
    for data in re.findall(r"data:image/[a-z]+;base64,([A-Za-z0-9+/=]+)", text):
        try:
            out.append(Image.open(BytesIO(base64.b64decode(data))).convert("RGB").tobytes())
        except Exception:
            pass
    return out


def image_ref_dict(uri: str) -> dict:
    return {"mimetype": "image/png", "dpi": 72, "size": {"width": WIDTH, "height": HEIGHT}, "uri": uri}


def document_dict(pictures=(), page_uri=None, table=False, name="report") -> dict:
    """A DoclingDocument in JSON form: a paragraph, optional table, one picture
    per URI in ``pictures`` and optionally a page image."""
    from docling_core.types.doc import DoclingDocument, ImageRef, Size, TableCell, TableData

    doc = DoclingDocument(name=name)
    doc.add_text(label="text", text="Quarterly report body text.")
    if table:
        cells = [TableCell(text=t, start_row_offset_idx=0, end_row_offset_idx=1,
                           start_col_offset_idx=i, end_col_offset_idx=i + 1)
                 for i, t in enumerate(["Revenue", "4711"])]
        doc.add_table(data=TableData(num_rows=1, num_cols=2, table_cells=cells))
    for _ in pictures:
        doc.add_picture(image=ImageRef(mimetype="image/png", dpi=72, size=Size(width=WIDTH, height=HEIGHT),
                                       uri="https://example.com/placeholder.png"))
    data = doc.export_to_dict()
    for i, uri in enumerate(pictures):
        data["pictures"][i]["image"] = image_ref_dict(uri)
    if page_uri is not None:
        data["pages"] = {"1": {"page_no": 1, "size": {"width": WIDTH, "height": HEIGHT},
                               "image": image_ref_dict(page_uri)}}
    return data


@pytest.fixture
def images():
    a, b = make_image(3), make_image(11)
    return {"a": (a, data_uri(a), a.tobytes()), "b": (b, data_uri(b), b.tobytes())}
