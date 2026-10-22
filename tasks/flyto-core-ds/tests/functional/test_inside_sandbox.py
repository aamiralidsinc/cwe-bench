"""Legitimate use inside the operator's sandbox keeps working exactly as today:
absolute and relative locations, locations whose spelling contains '.' or '..'
segments but stays inside, directories that do not exist yet, default output
locations modules derive, names and labels that contain dots, and side files.
"""
import os

from conftest import (
    SANDBOX,
    image_url,
    make_docx,
    make_pdf,
    make_png,
    relative_to,
)


def _ok(status, data):
    assert status == 200, (status, data)
    assert data.get("ok") is True, data
    inner = data.get("data")
    if isinstance(inner, dict) and "ok" in inner:
        assert inner["ok"] is True, inner


# ------------------------------------------------------------- image modules

def test_image_compress_inside_new_directory(run, inside):
    src = make_png(inside / "in.png")
    _ok(*run("image.compress", {
        "input_path": src, "output_path": str(inside / "new" / "a.png"),
    }))
    assert (inside / "new" / "a.png").is_file()


def test_image_convert_inside(run, inside):
    src = make_png(inside / "in.png")
    _ok(*run("image.convert", {
        "input_path": src, "output_path": str(inside / "new2" / "b.jpg"),
        "format": "jpeg",
    }))
    assert (inside / "new2" / "b.jpg").is_file()


def test_image_crop_dot_segments_staying_inside(run, inside):
    src = make_png(inside / "in.png")
    (inside / "sub").mkdir()
    spelled = f"{inside}/sub/../sub/./c.png"
    _ok(*run("image.crop", {
        "input_path": src, "output_path": spelled,
        "left": 0, "top": 0, "right": 10, "bottom": 10,
    }))
    assert (inside / "sub" / "c.png").is_file()


def test_image_resize_explicit_and_default_inside(run, inside):
    src = make_png(inside / "photo.png")
    _ok(*run("image.resize", {
        "input_path": src, "output_path": str(inside / "d.png"),
        "width": 10, "height": 10,
    }))
    assert (inside / "d.png").is_file()
    _ok(*run("image.resize", {"input_path": src, "width": 10, "height": 10}))
    assert (inside / "photo_resized.png").is_file()


def test_image_rotate_inside(run, inside):
    src = make_png(inside / "in.png")
    _ok(*run("image.rotate", {
        "input_path": src, "output_path": str(inside / "e.png"), "angle": 90,
    }))
    assert (inside / "e.png").is_file()


def test_image_watermark_inside(run, inside):
    src = make_png(inside / "in.png")
    _ok(*run("image.watermark", {
        "input_path": src, "output_path": str(inside / "f.png"), "text": "x",
    }))
    assert (inside / "f.png").is_file()


def test_image_qrcode_png_and_svg_inside(run, inside):
    _ok(*run("image.qrcode_generate", {
        "data": "hi", "output_path": str(inside / "qr" / "g.png"),
    }))
    assert (inside / "qr" / "g.png").is_file()
    _ok(*run("image.qrcode_generate", {
        "data": "hi", "output_path": str(inside / "qr" / "h.png"), "format": "svg",
    }))
    assert (inside / "qr" / "h.svg").is_file()


def test_image_download_explicit_path_inside(run, inside):
    target = inside / "fresh" / "x.png"
    _ok(*run("image.download", {
        "url": image_url(), "output_path": str(target), "output_dir": str(inside),
    }))
    assert target.is_file() and target.stat().st_size > 0


def test_image_download_default_name_into_dir(run, inside):
    _ok(*run("image.download", {
        "url": image_url("pic.png"), "output_dir": str(inside / "dl"),
    }))
    assert (inside / "dl" / "pic.png").is_file()


def test_image_thumbnail_named_and_derived_inside(run, inside):
    src = make_png(inside / "photo.png")
    _ok(*run("image.thumbnail", {
        "input_path": src, "output_dir": str(inside / "thumbs"), "name": "cover.2026",
    }))
    assert (inside / "thumbs" / "cover.2026.png").is_file()
    _ok(*run("image.thumbnail", {
        "input_path": src, "output_dir": str(inside / "thumbs"), "name": "holiday snap",
    }))
    assert (inside / "thumbs" / "holiday snap.png").is_file()
    _ok(*run("image.thumbnail", {"input_path": src, "output_dir": str(inside / "thumbs")}))
    assert (inside / "thumbs" / "photo-thumb.png").is_file()


def test_image_gallery_export_inside(run, inside):
    first = make_png(inside / "one.png")
    second = make_png(inside / "two.png", color="green")
    gallery = inside / "gallery"
    gallery.mkdir()
    stale = gallery / "stale.txt"
    stale.write_text("old")
    _ok(*run("image.gallery_export", {
        "images": [first, second], "output_dir": str(gallery), "clear_existing": True,
    }))
    assert sorted(os.listdir(gallery)) == ["one.png", "two.png"]

    keep = gallery / "keep.txt"
    keep.write_text("keep")
    _ok(*run("image.gallery_export", {
        "images": [first], "output_dir": str(gallery), "clear_existing": False,
    }))
    assert keep.read_text() == "keep"


# ---------------------------------------------------------- document modules

def test_document_excel_write_inside(run, inside):
    _ok(*run("excel.write", {
        "path": str(inside / "x" / "h.xlsx"), "data": [{"a": 1}],
    }))
    assert (inside / "x" / "h.xlsx").is_file()


def test_document_pdf_fill_form_inside(run, inside):
    tpl = make_pdf(inside / "form.pdf")
    _ok(*run("pdf.fill_form", {
        "template": tpl, "output": str(inside / "filled.pdf"), "fields": {},
    }))
    assert (inside / "filled.pdf").is_file()


def test_document_pdf_to_word_inside_and_default(run, inside):
    pdf = make_pdf(inside / "doc.pdf")
    _ok(*run("pdf.to_word", {
        "input_path": pdf, "output_path": str(inside / "out" / "j.docx"),
    }))
    assert (inside / "out" / "j.docx").is_file()
    _ok(*run("pdf.to_word", {"input_path": pdf}))
    assert (inside / "doc.docx").is_file()


def test_document_word_to_pdf_inside_and_default(run, inside):
    docx = make_docx(inside / "letter.docx")
    _ok(*run("word.to_pdf", {
        "input_path": docx, "output_path": str(inside / "o" / "k.pdf"),
    }))
    assert (inside / "o" / "k.pdf").is_file()
    _ok(*run("word.to_pdf", {"input_path": docx}))
    assert (inside / "letter.pdf").is_file()


def test_document_pdf_generate_inside(run, inside):
    _ok(*run("pdf.generate", {
        "content": "hi", "output_path": str(inside / "n.pdf"),
    }))
    assert (inside / "n.pdf").is_file()


def test_document_word_parse_images_inside(run, inside):
    docx = make_docx(inside / "pics.docx", with_image=make_png(inside / "p.png"))
    status, data = run("word.parse", {
        "file_path": docx, "extract_images": True,
        "images_output_dir": str(inside / "imgs"),
    })
    _ok(status, data)
    assert sorted(os.listdir(inside / "imgs")) == ["image_1.png"]


def test_document_pdf_metadata_backup_inside(run, inside):
    src = make_pdf(inside / "doc.pdf")
    _ok(*run("document.pdf_metadata", {
        "input_path": src, "output_path": str(inside / "out" / "meta.pdf"),
        "metadata": {"Title": "T"}, "keep_backup": True,
        "backup_path": str(inside / "out" / "original.pdf"),
    }))
    assert (inside / "out" / "meta.pdf").is_file()
    assert (inside / "out" / "original.pdf").is_file()
    _ok(*run("document.pdf_metadata", {
        "input_path": src, "output_path": str(inside / "plain.pdf"),
        "metadata": {"Author": "A"},
    }))
    assert (inside / "plain.pdf").is_file()


# ---------------------------------------------------------------- data modules

def test_data_csv_write_inside(run, inside):
    _ok(*run("data.csv.write", {
        "file_path": str(inside / "l.csv"), "data": [{"a": 1}],
    }))
    assert (inside / "l.csv").read_text().splitlines() == ["a", "1"]


def test_data_json_to_csv_inside(run, inside):
    _ok(*run("data.json_to_csv", {
        "input_data": [{"a": 1}], "output_path": str(inside / "sub" / "m.csv"),
    }))
    assert (inside / "sub" / "m.csv").is_file()


def test_data_dedup_hash_file_inside_persists(run, inside):
    hashes = inside / "state" / "seen.json"
    _ok(*run("data.dedup", {
        "items": [{"a": 1}, {"a": 1}], "keys": ["a"], "hash_file": str(hashes),
    }))
    assert hashes.is_file()
    status, data = run("data.dedup", {
        "items": [{"a": 1}, {"a": 2}], "keys": ["a"], "hash_file": str(hashes),
    })
    _ok(status, data)
    assert data["data"]["items"] == [{"a": 2}]


# ---------------------------------------------------------------- file modules

def test_file_copy_inside(run, inside):
    (inside / "note.txt").write_text("note")
    _ok(*run("file.copy", {
        "source": str(inside / "note.txt"), "destination": str(inside / "copy.txt"),
    }))
    assert (inside / "copy.txt").read_text() == "note"


def test_file_move_inside(run, inside):
    (inside / "note.txt").write_text("note")
    _ok(*run("file.move", {
        "source": str(inside / "note.txt"), "destination": str(inside / "moved.txt"),
    }))
    assert (inside / "moved.txt").read_text() == "note"
    assert not (inside / "note.txt").exists()


def test_file_write_inside_and_append(run, inside):
    _ok(*run("file.write", {"path": str(inside / "w.txt"), "content": "hello"}))
    assert (inside / "w.txt").read_text() == "hello"
    _ok(*run("file.write", {
        "path": str(inside / "w.txt"), "content": " again", "mode": "append",
    }))
    assert (inside / "w.txt").read_text() == "hello again"


# ------------------------------------------------------------- report modules

def test_verify_report_inside_with_dotted_name(run, inside):
    _ok(*run("verify.report", {
        "results": [], "output_dir": str(inside / "reports"),
        "format": "all", "name": "release.2026",
    }))
    for ext in ("html", "json", "md"):
        assert (inside / "reports" / f"release.2026.{ext}").is_file()


def test_warroom_report_inside(run, inside):
    _ok(*run("warroom.report", {
        "site_graph": {}, "scenarios": {}, "run_result": {}, "artifacts": {},
        "output_path": str(inside / "evidence" / "pack.json"),
    }))
    assert (inside / "evidence" / "pack.json").is_file()


# ------------------------------------------------------------- path spellings

def test_relative_paths_inside(run, inside, monkeypatch):
    monkeypatch.chdir(SANDBOX)
    rel = relative_to(inside, SANDBOX)
    src = make_png(inside / "in.png")
    _ok(*run("image.rotate", {
        "input_path": src, "output_path": f"{rel}/rot.png", "angle": 90,
    }))
    assert (inside / "rot.png").is_file()
    _ok(*run("data.csv.write", {
        "file_path": f"{rel}/rows.csv", "data": [{"a": 1}],
    }))
    assert (inside / "rows.csv").read_text().splitlines()[0] == "a"


def test_in_sandbox_symlink_inside(run, inside):
    real = inside / "real"
    real.mkdir()
    link = inside / "link"
    os.symlink(real, link)
    src = make_png(inside / "in.png")
    _ok(*run("image.rotate", {
        "input_path": src, "output_path": str(link / "through.png"), "angle": 90,
    }))
    assert (real / "through.png").is_file()


# ------------------------------------------------------------ browser modules

def test_browser_pagination_checkpoint_inside_and_resume(run, browser_session, inside):
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


def test_browser_pagination_without_checkpoint(run, browser_session):
    sid = browser_session(fail_after_first=False)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "max_pages": 1, "wait_between_pages_ms": 0,
    }, {"browser_session": sid})
    _ok(status, data)
    assert data["data"]["total_items"] == 1


def test_browser_download_inside_new_directory(run, browser_download_session, inside):
    sid = browser_download_session()
    target = inside / "downloads" / "2026" / "report.v.2.bin"
    _ok(*run("browser.download", {"save_path": str(target)},
             {"browser_session": sid}))
    assert target.is_file()
    assert target.read_text() == "downloaded"
