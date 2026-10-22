"""A module run through the execution API must not create, overwrite or remove
anything outside the operator's sandbox directory, whatever location value the
caller supplies. Each test: the run is refused and the outside directory is
exactly as it was before."""
import os
from pathlib import Path

from conftest import (
    SANDBOX,
    image_url,
    make_docx,
    make_pdf,
    make_png,
    refused,
    snapshot,
)


def _blocked(outside, before, status, data):
    assert refused(status, data), f"run was not refused: {status} {data}"
    assert snapshot(outside) == before, "the run changed files outside the sandbox"


# --------------------------------------------------------------- image modules

def test_image_download_explicit_path_outside(run, outside):
    before = snapshot(outside)
    target = outside / "fresh" / "x.png"
    status, data = run("image.download", {
        "url": image_url(), "output_path": str(target), "output_dir": str(outside),
    })
    _blocked(outside, before, status, data)


def test_image_download_default_name_into_outside_dir(run, outside):
    before = snapshot(outside)
    status, data = run("image.download", {
        "url": image_url("pic.png"), "output_dir": str(outside / "dl"),
    })
    _blocked(outside, before, status, data)


def test_image_download_refusal_creates_no_directory(run, inside, outside):
    before = snapshot(outside)
    status, data = run("image.download", {
        "url": image_url(), "output_path": str(outside / "made" / "y.png"),
        "output_dir": str(inside),
    })
    _blocked(outside, before, status, data)


def test_image_compress_absolute_outside(run, inside, outside):
    src = make_png(inside / "in.png")
    before = snapshot(outside)
    status, data = run("image.compress", {
        "input_path": src, "output_path": str(outside / "a.png"),
    })
    _blocked(outside, before, status, data)


def test_image_convert_into_new_outside_directory(run, inside, outside):
    src = make_png(inside / "in.png")
    before = snapshot(outside)
    status, data = run("image.convert", {
        "input_path": src, "output_path": str(outside / "newdir" / "b.jpg"),
        "format": "jpeg",
    })
    _blocked(outside, before, status, data)


def test_image_crop_dot_dot_segments(run, inside, outside):
    src = make_png(inside / "in.png")
    before = snapshot(outside)
    rel = os.path.relpath(outside, inside)
    escaping = f"{inside}/{rel}/c.png"
    assert ".." in escaping
    status, data = run("image.crop", {
        "input_path": src, "output_path": escaping,
        "left": 0, "top": 0, "right": 10, "bottom": 10,
    })
    _blocked(outside, before, status, data)


def test_image_resize_default_output_next_to_outside_input(run, outside):
    src = make_png(outside / "photo.png")
    before = snapshot(outside)
    status, data = run("image.resize", {"input_path": src, "width": 10, "height": 10})
    _blocked(outside, before, status, data)


def test_image_rotate_through_symlink_in_sandbox(run, inside, outside):
    src = make_png(inside / "in.png")
    link = inside / "shared"
    os.symlink(outside, link)
    before = snapshot(outside)
    status, data = run("image.rotate", {
        "input_path": src, "output_path": str(link / "r.png"), "angle": 90,
    })
    _blocked(outside, before, status, data)


def test_image_watermark_absolute_outside(run, inside, outside):
    src = make_png(inside / "in.png")
    before = snapshot(outside)
    status, data = run("image.watermark", {
        "input_path": src, "output_path": str(outside / "w.png"), "text": "x",
    })
    _blocked(outside, before, status, data)


def test_qrcode_svg_outside(run, outside):
    before = snapshot(outside)
    status, data = run("image.qrcode_generate", {
        "data": "hello", "output_path": str(outside / "code.png"), "format": "svg",
    })
    _blocked(outside, before, status, data)


def test_qrcode_png_outside(run, outside):
    before = snapshot(outside)
    status, data = run("image.qrcode_generate", {
        "data": "hello", "output_path": str(outside / "code.png"),
    })
    _blocked(outside, before, status, data)


# ------------------------------------------------------------ document modules

def test_excel_write_outside(run, outside):
    before = snapshot(outside)
    status, data = run("excel.write", {"path": str(outside / "h.xlsx"), "data": [{"a": 1}]})
    _blocked(outside, before, status, data)


def test_excel_write_into_new_outside_directory(run, outside):
    before = snapshot(outside)
    status, data = run("excel.write", {"path": str(outside / "new" / "h.xlsx"), "data": [{"a": 1}]})
    _blocked(outside, before, status, data)
    assert not (outside / "new").exists()


def test_pdf_fill_form_outside(run, inside, outside):
    tpl = make_pdf(inside / "form.pdf")
    before = snapshot(outside)
    status, data = run("pdf.fill_form", {
        "template": tpl, "output": str(outside / "filled.pdf"), "fields": {},
    })
    _blocked(outside, before, status, data)


def test_pdf_to_word_outside(run, inside, outside):
    pdf = make_pdf(inside / "doc.pdf")
    before = snapshot(outside)
    status, data = run("pdf.to_word", {"input_path": pdf, "output_path": str(outside / "j.docx")})
    _blocked(outside, before, status, data)


def test_word_to_pdf_default_output_next_to_outside_input(run, outside):
    docx = make_docx(outside / "letter.docx")
    before = snapshot(outside)
    status, data = run("word.to_pdf", {"input_path": docx})
    _blocked(outside, before, status, data)


def test_pdf_generate_outside(run, outside):
    before = snapshot(outside)
    status, data = run("pdf.generate", {"content": "hi", "output_path": str(outside / "n.pdf")})
    _blocked(outside, before, status, data)


def test_word_parse_images_outside(run, inside, outside):
    docx = make_docx(inside / "pics.docx", with_image=make_png(inside / "p.png"))
    before = snapshot(outside)
    status, data = run("word.parse", {
        "file_path": docx, "extract_images": True, "images_output_dir": str(outside / "imgs"),
    })
    _blocked(outside, before, status, data)


# ---------------------------------------------------------------- data modules

def test_csv_write_absolute_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.csv.write", {"file_path": str(outside / "l.csv"), "data": [{"a": 1}]})
    _blocked(outside, before, status, data)


def test_json_to_csv_absolute_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.json_to_csv", {
        "input_data": [{"a": 1}], "output_path": str(outside / "sub" / "m.csv"),
    })
    _blocked(outside, before, status, data)


# ---------------------------------------------------------------- file modules

def test_file_copy_destination_outside(run, inside, outside):
    src = inside / "note.txt"
    src.write_text("note")
    before = snapshot(outside)
    status, data = run("file.copy", {"source": str(src), "destination": str(outside / "o.txt")})
    _blocked(outside, before, status, data)


def test_file_move_destination_outside(run, inside, outside):
    src = inside / "note.txt"
    src.write_text("note")
    before = snapshot(outside)
    status, data = run("file.move", {"source": str(src), "destination": str(outside / "p.txt")})
    _blocked(outside, before, status, data)
    assert src.read_text() == "note"


def test_file_move_source_outside(run, inside, outside):
    src = outside / "secret.txt"
    src.write_text("secret")
    before = snapshot(outside)
    dest = inside / "taken.txt"
    status, data = run("file.move", {"source": str(src), "destination": str(dest)})
    _blocked(outside, before, status, data)
    assert src.read_text() == "secret"
    assert not dest.exists()


# ------------------------------------------------------------- browser modules

def test_pagination_state_outside(run, browser_session, outside):
    sid = browser_session(fail_after_first=True)
    before = snapshot(outside)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(outside / "state.json"),
        "max_pages": 3, "wait_between_pages_ms": 0, "no_more_indicator": ".end",
    }, {"browser_session": sid})
    _blocked(outside, before, status, data)


def test_pagination_completed_run_leaves_outside_file(run, browser_session, outside):
    sid = browser_session(fail_after_first=False)
    keep = outside / "keep.json"
    keep.write_text("precious")
    before = snapshot(outside)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(keep),
        "max_pages": 1, "wait_between_pages_ms": 0,
    }, {"browser_session": sid})
    _blocked(outside, before, status, data)
    assert keep.read_text() == "precious"
