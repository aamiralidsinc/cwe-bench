# SPDX-License-Identifier: MIT
"""Shared helpers for the security tests.

A small PNG with distinctive pixels stands for a private file on the host. A
test passes when, after docling loads a document that refers to that file,
none of docling's image outputs (embedded exports, referenced saves) carry its
pixels -- or when docling refuses the document with an error.

Everything here is computed with Pillow and the standard library only, never
with docling helpers, so a hardened product cannot break the bookkeeping.
"""

import base64
import re
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

WIDTH, HEIGHT = 7, 5


def write_marker_image(path: Path) -> bytes:
    """Write the 'private' PNG and return its RGB pixels."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    img.putdata([(i * 37 % 256, i * 91 % 256, i * 13 % 256) for i in range(WIDTH * HEIGHT)])
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return _Marker(img.tobytes())


class _Pixels(list):
    """A list of RGB pixel buffers whose repr stays short in assertion output."""

    def __repr__(self):
        return f"<{len(self)} image(s)>"


class _Marker(bytes):
    def __repr__(self):
        return "<private image pixels>"


def embedded_pixels(text: str) -> list:
    out = _Pixels()
    for data in re.findall(r"data:image/[a-z]+;base64,([A-Za-z0-9+/=]+)", text):
        try:
            out.append(Image.open(BytesIO(base64.b64decode(data))).convert("RGB").tobytes())
        except Exception:
            pass
    return out


def files_pixels(folder: Path) -> list:
    out = _Pixels()
    for p in folder.rglob("*"):
        if p.is_file():
            try:
                with Image.open(p) as im:
                    out.append(im.convert("RGB").tobytes())
            except Exception:
                pass
    return out


def image_ref_dict(uri: str) -> dict:
    """The JSON form of an image reference, as a document file carries it."""
    return {"mimetype": "image/png", "dpi": 72, "size": {"width": WIDTH, "height": HEIGHT}, "uri": uri}


def document_dict(picture_uri=None, page_uri=None, name="report") -> dict:
    """A DoclingDocument in JSON form with a paragraph, optionally a picture
    and optionally one page whose page image refers to ``page_uri``."""
    from docling_core.types.doc import DoclingDocument, ImageRef, Size

    doc = DoclingDocument(name=name)
    doc.add_text(label="text", text="Quarterly report body text.")
    data = doc.export_to_dict()
    if picture_uri is not None:
        doc.add_picture(image=ImageRef(mimetype="image/png", dpi=72, size=Size(width=WIDTH, height=HEIGHT),
                                       uri="data:image/png;base64,"))
        data = doc.export_to_dict()
        data["pictures"][0]["image"] = image_ref_dict(picture_uri)
    if page_uri is not None:
        data["pages"] = {"1": {"page_no": 1, "size": {"width": WIDTH, "height": HEIGHT},
                               "image": image_ref_dict(page_uri)}}
    return data


def assert_not_disclosed(doc, out_dir: Path, pixels: bytes) -> None:
    """None of the document's image outputs may contain the private pixels."""
    from docling_core.types.doc import ImageRefMode

    if doc is None:  # docling refused the document: nothing was loaded
        return
    emb = out_dir / "embedded" / "doc.json"
    emb.parent.mkdir(parents=True, exist_ok=True)
    doc.save_as_json(emb, image_mode=ImageRefMode.EMBEDDED)
    assert pixels not in embedded_pixels(emb.read_text()), "private image embedded in json save"
    ref = out_dir / "referenced"
    ref.mkdir(parents=True, exist_ok=True)
    doc.save_as_json(ref / "doc.json", image_mode=ImageRefMode.REFERENCED)
    assert pixels not in files_pixels(ref), "private image copied into referenced save"
    md = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
    assert pixels not in embedded_pixels(md), "private image embedded in markdown export"
    html = doc.export_to_html(image_mode=ImageRefMode.EMBEDDED)
    assert pixels not in embedded_pixels(html), "private image embedded in html export"


def loaded_or_none(fn):
    """Run a load; an error means docling refused the document (accepted)."""
    try:
        return fn()
    except Exception:
        return None


@pytest.fixture
def private_image(tmp_path):
    """(path, pixels) of a private image outside any output folder."""
    path = tmp_path / "home" / "private" / "scan.png"
    return path, write_marker_image(path)
