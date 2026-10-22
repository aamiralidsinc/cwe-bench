"""A module run through the execution API must not create, overwrite or remove
anything outside the operator's sandbox directory, whatever location value the
caller supplies — including locations a module derives itself, secondary
destinations a caller opts into, and file names taken from the data being written.

Each test: the run is refused and the outside directory is exactly as it was
before."""
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
        "data": "hello", "output_path": str(outside / "code.png"), "format": "png",
    })
    _blocked(outside, before, status, data)


# ----------------------------------------------------------- document writers

def test_excel_write_outside(run, outside):
    before = snapshot(outside)
    status, data = run("excel.write", {
        "path": str(outside / "book.xlsx"), "data": [["a", "1"]],
    })
    _blocked(outside, before, status, data)


def test_pdf_fill_form_outside(run, inside, outside):
    template = make_pdf(inside / "form.pdf")
    before = snapshot(outside)
    status, data = run("pdf.fill_form", {
        "template": template, "output": str(outside / "filled.pdf"), "fields": {},
    })
    _blocked(outside, before, status, data)


def test_pdf_to_word_explicit_outside(run, inside, outside):
    src = make_pdf(inside / "in.pdf")
    before = snapshot(outside)
    status, data = run("pdf.to_word", {
        "input_path": src, "output_path": str(outside / "out.docx"),
    })
    _blocked(outside, before, status, data)


def test_pdf_to_word_default_next_to_outside_input(run, outside):
    src = make_pdf(outside / "od.pdf")
    before = snapshot(outside)
    status, data = run("pdf.to_word", {"input_path": src})
    _blocked(outside, before, status, data)


def test_word_to_pdf_explicit_outside(run, inside, outside):
    src = make_docx(inside / "w.docx")
    before = snapshot(outside)
    status, data = run("word.to_pdf", {
        "input_path": src, "output_path": str(outside / "w.pdf"),
    })
    _blocked(outside, before, status, data)


def test_word_to_pdf_default_next_to_outside_input(run, outside):
    src = make_docx(outside / "od.docx")
    before = snapshot(outside)
    status, data = run("word.to_pdf", {"input_path": src})
    _blocked(outside, before, status, data)


# ------------------------------------------------- paginator resume state file

def test_pagination_checkpoint_outside_on_interrupted_run(run, outside, browser_session):
    sid = browser_session(fail_after_first=True)
    target = outside / "ckpt.json"
    target.write_text("precious")
    before = snapshot(outside)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(target),
        "max_pages": 3, "wait_between_pages_ms": 0, "no_more_indicator": ".end",
    }, context={"browser_session": sid})
    assert refused(status, data), f"run was not refused: {status} {data}"
    assert snapshot(outside) == before, "the run wrote, replaced or removed the outside state file"


def test_pagination_checkpoint_outside_on_completed_run(run, outside, browser_session):
    sid = browser_session(fail_after_first=False)
    target = outside / "keep.json"
    target.write_text("precious")
    before = snapshot(outside)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(target),
        "max_pages": 1, "wait_between_pages_ms": 0,
    }, context={"browser_session": sid})
    assert refused(status, data), f"run was not refused: {status} {data}"
    assert snapshot(outside) == before, "the run wrote, replaced or removed the outside state file"


# ------------------------------------- other writers the published fix misses

def test_csv_write_absolute_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.csv.write", {
        "file_path": str(outside / "b.csv"), "data": [{"a": 1}],
    })
    _blocked(outside, before, status, data)


def test_json_to_csv_absolute_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.json_to_csv", {
        "input_data": [{"a": 1}], "output_path": str(outside / "b2.csv"),
    })
    _blocked(outside, before, status, data)


def test_json_to_csv_refusal_creates_no_directory(run, outside):
    before = snapshot(outside)
    status, data = run("data.json_to_csv", {
        "input_data": [{"a": 1}], "output_path": str(outside / "made2" / "x.csv"),
    })
    _blocked(outside, before, status, data)


def test_csv_write_refusal_creates_no_directory(run, outside):
    before = snapshot(outside)
    status, data = run("data.csv.write", {
        "file_path": str(outside / "made2b" / "x.csv"), "data": [{"a": 1}],
    })
    _blocked(outside, before, status, data)


def test_file_copy_destination_outside(run, inside, outside):
    src = inside / "s.txt"
    src.write_text("hi")
    before = snapshot(outside)
    status, data = run("file.copy", {
        "source": str(src), "destination": str(outside / "copied.txt"),
    })
    _blocked(outside, before, status, data)


def test_file_move_destination_outside(run, inside, outside):
    src = inside / "m.txt"
    src.write_text("hi")
    before = snapshot(outside)
    status, data = run("file.move", {
        "source": str(src), "destination": str(outside / "moved.txt"),
    })
    _blocked(outside, before, status, data)


def test_file_move_source_outside_is_not_removed(run, inside, outside):
    victim = outside / "victim.txt"
    victim.write_text("victim")
    before = snapshot(outside)
    status, data = run("file.move", {
        "source": str(victim), "destination": str(inside / "in.txt"),
    })
    _blocked(outside, before, status, data)


def test_word_parse_images_dir_outside(run, inside, outside):
    src = make_docx(inside / "d.docx", with_image=make_png(inside / "p.png"))
    before = snapshot(outside)
    status, data = run("word.parse", {
        "file_path": src, "extract_images": True,
        "images_output_dir": str(outside / "imgs"),
    })
    _blocked(outside, before, status, data)


def test_pdf_generate_outside(run, outside):
    before = snapshot(outside)
    status, data = run("pdf.generate", {
        "output_path": str(outside / "gen.pdf"), "title": "t", "content": "hello",
    })
    _blocked(outside, before, status, data)


def test_dedup_hash_file_outside(run, outside):
    before = snapshot(outside)
    status, data = run("data.dedup", {
        "items": [{"u": "1"}], "keys": ["u"],
        "hash_file": str(outside / "seen.json"), "storage": "disk",
    })
    _blocked(outside, before, status, data)


def test_dedup_hash_file_refusal_creates_no_directory(run, outside):
    before = snapshot(outside)
    status, data = run("data.dedup", {
        "items": [{"u": "1"}], "keys": ["u"],
        "hash_file": str(outside / "made3" / "s.json"), "storage": "disk",
    })
    _blocked(outside, before, status, data)


# -------------------------------- secondary destinations inside already-guarded
# modules, and file names a module takes from the data it is writing

def test_write_backup_copy_outside(run, inside, outside):
    target = inside / "doc.txt"
    target.write_text("old")
    before = snapshot(outside)
    status, data = run("file.write", {
        "path": str(target), "content": "new",
        "backup_path": str(outside / "doc.txt.bak"),
    })
    _blocked(outside, before, status, data)


def test_write_backup_copy_refusal_creates_no_directory(run, inside, outside):
    target = inside / "doc.txt"
    target.write_text("old")
    before = snapshot(outside)
    status, data = run("file.write", {
        "path": str(target), "content": "new",
        "backup_path": str(outside / "newdir" / "doc.txt.bak"),
    })
    _blocked(outside, before, status, data)


def test_storage_extra_file_outside(run, outside):
    before = snapshot(outside)
    status, data = run("storage.set", {
        "namespace": "ns", "key": "k", "value": {"v": 1},
        "file_path": str(outside / "entry.json"),
    })
    _blocked(outside, before, status, data)


def test_storage_extra_file_refusal_creates_no_directory(run, outside):
    before = snapshot(outside)
    status, data = run("storage.set", {
        "namespace": "ns", "key": "k", "value": {"v": 1},
        "file_path": str(outside / "newdir" / "entry.json"),
    })
    _blocked(outside, before, status, data)


def test_export_records_relative_name_escapes(run, inside, outside):
    # A relative name taken from the record walks out of the output directory.
    out_dir = inside / "recs"
    before = snapshot(outside)
    escaping = os.path.relpath(outside / "pwned", out_dir)
    assert ".." in escaping
    status, data = run("data.export_records", {
        "records": [{"name": escaping, "v": 1}],
        "output_dir": str(out_dir), "name_key": "name",
    })
    _blocked(outside, before, status, data)


def test_export_records_absolute_name_escapes(run, inside, outside):
    out_dir = inside / "recs"
    before = snapshot(outside)
    status, data = run("data.export_records", {
        "records": [{"name": str(outside / "abs.json"), "v": 1}],
        "output_dir": str(out_dir), "name_key": "name",
    })
    _blocked(outside, before, status, data)


def test_export_records_name_with_subdir_escapes(run, inside, outside):
    out_dir = inside / "recs"
    before = snapshot(outside)
    escaping = os.path.relpath(outside / "deep" / "pwned", out_dir)
    status, data = run("data.export_records", {
        "records": [{"name": escaping, "v": 1}],
        "output_dir": str(out_dir), "name_key": "name",
    })
    _blocked(outside, before, status, data)
