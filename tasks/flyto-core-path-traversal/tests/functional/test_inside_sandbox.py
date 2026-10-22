"""Legitimate use inside the operator's sandbox keeps working exactly as today:
absolute and relative locations, locations whose spelling contains '.' or '..'
segments but stays inside, directories that do not exist yet, and the default
output locations modules derive when the caller gives none."""
import os
from pathlib import Path

import pytest

from conftest import SANDBOX, image_url, make_docx, make_pdf, make_png


def _ok(status, data):
    assert status == 200, (status, data)
    assert data.get("ok") is True, data
    inner = data.get("data")
    if isinstance(inner, dict) and "ok" in inner:
        assert inner["ok"] is True, inner


def _image_cases(d):
    src = make_png(d / "in.png")
    return [
        ("image.compress", {"input_path": src, "output_path": str(d / "new" / "a.png")}, d / "new" / "a.png"),
        ("image.convert", {"input_path": src, "output_path": str(d / "new2" / "b.jpg"), "format": "jpeg"}, d / "new2" / "b.jpg"),
        ("image.crop", {"input_path": src, "output_path": str(d / "c.png"), "left": 0, "top": 0, "right": 10, "bottom": 10}, d / "c.png"),
        ("image.resize", {"input_path": src, "output_path": str(d / "d.png"), "width": 10, "height": 10}, d / "d.png"),
        ("image.rotate", {"input_path": src, "output_path": str(d / "e.png"), "angle": 90}, d / "e.png"),
        ("image.watermark", {"input_path": src, "output_path": str(d / "f.png"), "text": "x"}, d / "f.png"),
        ("image.qrcode_generate", {"data": "hi", "output_path": str(d / "qr" / "g.png")}, d / "qr" / "g.png"),
    ]


IMAGE_IDS = ["compress", "convert", "crop", "resize", "rotate", "watermark", "qrcode"]


@pytest.mark.parametrize("idx", range(len(IMAGE_IDS)), ids=IMAGE_IDS)
def test_image_module_absolute_path_inside(run, inside, idx):
    module_id, params, expected = _image_cases(inside)[idx]
    _ok(*run(module_id, params))
    assert expected.is_file() and expected.stat().st_size > 0


def test_qrcode_svg_inside(run, inside):
    _ok(*run("image.qrcode_generate", {
        "data": "hi", "output_path": str(inside / "code.png"), "format": "svg",
    }))
    assert (inside / "code.svg").is_file()


def test_image_download_explicit_path_inside(run, inside):
    target = inside / "fresh" / "x.png"
    _ok(*run("image.download", {"url": image_url(), "output_path": str(target), "output_dir": str(inside)}))
    assert target.is_file() and target.stat().st_size > 0


def test_image_download_default_name_into_dir(run, inside):
    _ok(*run("image.download", {"url": image_url("pic.png"), "output_dir": str(inside / "dl")}))
    assert (inside / "dl" / "pic.png").is_file()


def test_image_resize_default_output_name(run, inside):
    src = make_png(inside / "photo.png")
    _ok(*run("image.resize", {"input_path": src, "width": 10, "height": 10}))
    assert (inside / "photo_resized.png").is_file()


def test_image_crop_dot_segments_staying_inside(run, inside):
    src = make_png(inside / "in.png")
    (inside / "sub").mkdir()
    spelled = f"{inside}/sub/../sub/./c.png"
    _ok(*run("image.crop", {
        "input_path": src, "output_path": spelled,
        "left": 0, "top": 0, "right": 10, "bottom": 10,
    }))
    assert (inside / "sub" / "c.png").is_file()


def test_relative_paths_inside(run, inside, monkeypatch):
    monkeypatch.chdir(SANDBOX)
    rel = os.path.relpath(inside, SANDBOX)
    src = make_png(inside / "in.png")
    _ok(*run("image.rotate", {"input_path": src, "output_path": f"{rel}/rot.png", "angle": 90}))
    assert (inside / "rot.png").is_file()
    _ok(*run("data.csv.write", {"file_path": f"{rel}/rows.csv", "data": [{"a": 1}]}))
    assert (inside / "rows.csv").read_text().splitlines()[0] == "a"


def test_excel_write_inside(run, inside):
    _ok(*run("excel.write", {"path": str(inside / "x" / "h.xlsx"), "data": [{"a": 1}]}))
    assert (inside / "x" / "h.xlsx").is_file()


def test_pdf_fill_form_inside(run, inside):
    tpl = make_pdf(inside / "form.pdf")
    _ok(*run("pdf.fill_form", {"template": tpl, "output": str(inside / "filled.pdf"), "fields": {}}))
    assert (inside / "filled.pdf").is_file()


def test_pdf_to_word_inside(run, inside):
    pdf = make_pdf(inside / "doc.pdf")
    _ok(*run("pdf.to_word", {"input_path": pdf, "output_path": str(inside / "out" / "j.docx")}))
    assert (inside / "out" / "j.docx").is_file()


def test_pdf_to_word_default_output(run, inside):
    pdf = make_pdf(inside / "doc.pdf")
    _ok(*run("pdf.to_word", {"input_path": pdf}))
    assert (inside / "doc.docx").is_file()


def test_word_to_pdf_default_output(run, inside):
    docx = make_docx(inside / "letter.docx")
    _ok(*run("word.to_pdf", {"input_path": docx}))
    assert (inside / "letter.pdf").is_file()


def test_word_to_pdf_inside(run, inside):
    docx = make_docx(inside / "letter.docx")
    _ok(*run("word.to_pdf", {"input_path": docx, "output_path": str(inside / "o" / "k.pdf")}))
    assert (inside / "o" / "k.pdf").is_file()


def test_pdf_generate_inside(run, inside):
    _ok(*run("pdf.generate", {"content": "hi", "output_path": str(inside / "n.pdf")}))
    assert (inside / "n.pdf").is_file()


def test_word_parse_images_inside(run, inside):
    docx = make_docx(inside / "pics.docx", with_image=make_png(inside / "p.png"))
    status, data = run("word.parse", {
        "file_path": docx, "extract_images": True, "images_output_dir": str(inside / "imgs"),
    })
    _ok(status, data)
    assert sorted(os.listdir(inside / "imgs")) == ["image_1.png"]


def test_word_parse_without_images(run, inside):
    docx = make_docx(inside / "plain.docx")
    _ok(*run("word.parse", {"file_path": docx}))


def test_csv_write_inside(run, inside):
    _ok(*run("data.csv.write", {"file_path": str(inside / "l.csv"), "data": [{"a": 1}]}))
    assert (inside / "l.csv").read_text().splitlines() == ["a", "1"]


def test_json_to_csv_inside(run, inside):
    _ok(*run("data.json_to_csv", {"input_data": [{"a": 1}], "output_path": str(inside / "sub" / "m.csv")}))
    assert (inside / "sub" / "m.csv").is_file()


def test_file_copy_inside(run, inside):
    (inside / "note.txt").write_text("note")
    _ok(*run("file.copy", {"source": str(inside / "note.txt"), "destination": str(inside / "copy.txt")}))
    assert (inside / "copy.txt").read_text() == "note"


def test_file_move_inside(run, inside):
    (inside / "note.txt").write_text("note")
    _ok(*run("file.move", {"source": str(inside / "note.txt"), "destination": str(inside / "moved.txt")}))
    assert (inside / "moved.txt").read_text() == "note"
    assert not (inside / "note.txt").exists()


def test_file_write_inside(run, inside):
    _ok(*run("file.write", {"path": str(inside / "w.txt"), "content": "hello"}))
    assert (inside / "w.txt").read_text() == "hello"


def test_pagination_checkpoint_inside_and_resume(run, browser_session, inside):
    state = inside / "state" / "progress.json"
    sid = browser_session(fail_after_first=True)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(state),
        "max_pages": 3, "wait_between_pages_ms": 0, "no_more_indicator": ".end",
    }, {"browser_session": sid})
    _ok(status, data)
    assert state.is_file()
    assert state.with_suffix(".jsonl").is_file()

    sid2 = browser_session(fail_after_first=False)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(state),
        "max_pages": 2, "wait_between_pages_ms": 0,
    }, {"browser_session": sid2})
    _ok(status, data)
    assert data["data"]["resumed"] is True
    assert not state.exists()


def test_pagination_without_checkpoint(run, browser_session):
    sid = browser_session(fail_after_first=False)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "max_pages": 1, "wait_between_pages_ms": 0,
    }, {"browser_session": sid})
    _ok(status, data)
    assert data["data"]["total_items"] == 1
