"""A module run through the execution API must not create, overwrite or remove
anything outside the operator's sandbox directory, whatever value the caller
supplies for a location. Each test runs one module through POST /v1/execute and
asserts that the run is refused and that the outside directory is unchanged."""
import os

from conftest import (
    image_url,
    make_docx,
    make_pdf,
    make_png,
    refused,
    relative_to,
    snapshot,
)


def _blocked(outside, before, status, data):
    assert refused(status, data), f"run was not refused: {status} {data}"
    assert snapshot(outside) == before, "the run changed files outside the sandbox"


# ------------------------------------------------------------ image download

def test_image_download_explicit_path_outside(run, outside):
    before = snapshot(outside)
    status, data = run("image.download", {
        "url": image_url(), "output_path": str(outside / "fresh" / "x.png"),
        "output_dir": str(outside),
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


# ------------------------------------------------------------- image modules

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
    escaping = f"{inside}/{relative_to(outside, inside)}/c.png"
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


def test_image_qrcode_png_outside(run, outside):
    before = snapshot(outside)
    status, data = run("image.qrcode_generate", {
        "data": "hello", "output_path": str(outside / "code.png"),
    })
    _blocked(outside, before, status, data)


def test_image_qrcode_svg_outside(run, outside):
    before = snapshot(outside)
    status, data = run("image.qrcode_generate", {
        "data": "hello", "output_path": str(outside / "code.png"), "format": "svg",
    })
    _blocked(outside, before, status, data)


def test_image_thumbnail_name_traversal(run, inside, outside):
    src = make_png(inside / "in.png")
    before = snapshot(outside)
    output_dir = inside / "thumbs"
    status, data = run("image.thumbnail", {
        "input_path": src, "output_dir": str(output_dir),
        "name": f"{relative_to(outside, output_dir)}/escaped",
    })
    _blocked(outside, before, status, data)


def test_image_thumbnail_absolute_name(run, inside, outside):
    src = make_png(inside / "in.png")
    before = snapshot(outside)
    status, data = run("image.thumbnail", {
        "input_path": src, "output_dir": str(inside / "thumbs2"),
        "name": str(outside / "absolute"),
    })
    _blocked(outside, before, status, data)


def test_image_gallery_export_clears_outside_directory(run, inside, outside):
    src = make_png(inside / "in.png")
    victim = outside / "precious.txt"
    victim.write_text("precious")
    before = snapshot(outside)
    status, data = run("image.gallery_export", {
        "images": [src], "output_dir": str(outside), "clear_existing": True,
    })
    _blocked(outside, before, status, data)
    assert victim.read_text() == "precious"


def test_image_gallery_export_prefix_becomes_outside_location(run, inside, outside):
    src = make_png(inside / "in.png")
    gallery = inside / "gallery"
    before = snapshot(outside)
    status, data = run("image.gallery_export", {
        "images": [src], "output_dir": str(gallery), "clear_existing": False,
        "prefix": f"{relative_to(outside, gallery)}/",
    })
    _blocked(outside, before, status, data)


# ---------------------------------------------------------- document modules

def test_document_excel_write_outside(run, outside):
    before = snapshot(outside)
    status, data = run("excel.write", {
        "path": str(outside / "h.xlsx"), "data": [{"a": 1}],
    })
    _blocked(outside, before, status, data)


def test_document_excel_write_into_new_outside_directory(run, outside):
    before = snapshot(outside)
    status, data = run("excel.write", {
        "path": str(outside / "new" / "h.xlsx"), "data": [{"a": 1}],
    })
    _blocked(outside, before, status, data)
    assert not (outside / "new").exists()


def test_document_pdf_fill_form_outside(run, inside, outside):
    tpl = make_pdf(inside / "form.pdf")
    before = snapshot(outside)
    status, data = run("pdf.fill_form", {
        "template": tpl, "output": str(outside / "filled.pdf"), "fields": {},
    })
    _blocked(outside, before, status, data)


def test_document_pdf_to_word_outside(run, inside, outside):
    pdf = make_pdf(inside / "doc.pdf")
    before = snapshot(outside)
    status, data = run("pdf.to_word", {
        "input_path": pdf, "output_path": str(outside / "j.docx"),
    })
    _blocked(outside, before, status, data)


def test_document_word_to_pdf_default_output_next_to_outside_input(run, outside):
    docx = make_docx(outside / "letter.docx")
    before = snapshot(outside)
    status, data = run("word.to_pdf", {"input_path": docx})
    _blocked(outside, before, status, data)


def test_document_pdf_generate_outside(run, outside):
    before = snapshot(outside)
    status, data = run("pdf.generate", {
        "content": "hi", "output_path": str(outside / "n.pdf"),
    })
    _blocked(outside, before, status, data)


def test_document_word_parse_images_outside(run, inside, outside):
    docx = make_docx(inside / "pics.docx", with_image=make_png(inside / "p.png"))
    before = snapshot(outside)
    status, data = run("word.parse", {
        "file_path": docx, "extract_images": True,
        "images_output_dir": str(outside / "imgs"),
    })
    _blocked(outside, before, status, data)


def test_document_pdf_metadata_backup_outside(run, inside, outside):
    src = make_pdf(inside / "doc.pdf")
    before = snapshot(outside)
    status, data = run("document.pdf_metadata", {
        "input_path": src, "output_path": str(inside / "labeled.pdf"),
        "metadata": {"Title": "T"}, "keep_backup": True,
        "backup_path": str(outside / "copies" / "original.pdf"),
    })
    _blocked(outside, before, status, data)


# ---------------------------------------------------------------- data modules

def test_data_csv_write_absolute_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.csv.write", {
        "file_path": str(outside / "l.csv"), "data": [{"a": 1}],
    })
    _blocked(outside, before, status, data)


def test_data_json_to_csv_absolute_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.json_to_csv", {
        "input_data": [{"a": 1}], "output_path": str(outside / "sub" / "m.csv"),
    })
    _blocked(outside, before, status, data)


def test_data_dedup_hash_file_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.dedup", {
        "items": [{"a": 1}, {"a": 1}], "keys": ["a"],
        "hash_file": str(outside / "hashes" / "seen.json"),
    })
    _blocked(outside, before, status, data)


# ---------------------------------------------------------------- file modules

def test_file_copy_destination_outside(run, inside, outside):
    src = inside / "note.txt"
    src.write_text("note")
    before = snapshot(outside)
    status, data = run("file.copy", {
        "source": str(src), "destination": str(outside / "o.txt"),
    })
    _blocked(outside, before, status, data)


def test_file_move_destination_outside(run, inside, outside):
    src = inside / "note.txt"
    src.write_text("note")
    before = snapshot(outside)
    status, data = run("file.move", {
        "source": str(src), "destination": str(outside / "p.txt"),
    })
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


# ------------------------------------------------------------- report modules

def test_verify_report_output_dir_outside(run, outside):
    before = snapshot(outside)
    status, data = run("verify.report", {
        "results": [], "output_dir": str(outside / "reports"), "format": "json",
    })
    _blocked(outside, before, status, data)


def test_verify_report_name_becomes_outside_location(run, inside, outside):
    before = snapshot(outside)
    output_dir = inside / "reports"
    status, data = run("verify.report", {
        "results": [], "output_dir": str(output_dir), "format": "json",
        "name": f"{relative_to(outside, output_dir)}/report",
    })
    _blocked(outside, before, status, data)


def test_warroom_report_output_path_outside(run, outside):
    before = snapshot(outside)
    status, data = run("warroom.report", {
        "site_graph": {}, "scenarios": {}, "run_result": {}, "artifacts": {},
        "output_path": str(outside / "evidence.json"),
    })
    _blocked(outside, before, status, data)


# ------------------------------------------------------------ browser modules

def test_browser_pagination_state_outside(run, browser_session, outside):
    sid = browser_session(fail_after_first=True)
    before = snapshot(outside)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(outside / "state.json"),
        "max_pages": 3, "wait_between_pages_ms": 0, "no_more_indicator": ".end",
    }, {"browser_session": sid})
    _blocked(outside, before, status, data)


def test_browser_pagination_completed_run_leaves_outside_file(run, browser_session, outside):
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


def test_browser_download_save_path_outside(run, browser_download_session, outside):
    """A browser-delivered file is still a file this run creates."""
    sid = browser_download_session()
    before = snapshot(outside)
    status, data = run("browser.download", {
        "save_path": str(outside / "files" / "x.bin"),
    }, {"browser_session": sid})
    _blocked(outside, before, status, data)
    assert not (outside / "files").exists()


def test_browser_download_nested_path_outside_creates_no_directory(run, browser_download_session, outside):
    """The refusal leaves no directory behind for a not-yet-existing target."""
    sid = browser_download_session()
    before = snapshot(outside)
    status, data = run("browser.download", {
        "save_path": str(outside / "nested" / "deeper" / "report.2026.bin"),
    }, {"browser_session": sid})
    _blocked(outside, before, status, data)
    assert not (outside / "nested").exists()
