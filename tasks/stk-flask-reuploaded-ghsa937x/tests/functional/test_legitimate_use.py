"""Everything that works today keeps working exactly as today."""
from conftest import make_set
from conftest import upload
from flask_uploads import ARCHIVES
from flask_uploads import AllExcept
from flask_uploads import DEFAULTS
from flask_uploads import IMAGES


def _save(app, uset, filename, **options):
    with app.test_request_context():
        return uset.save(upload(filename), **options)


def test_ordinary_upload_is_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    assert _save(app, uset, "photo.jpg") == "photo.jpg"
    assert (destination / "photo.jpg").read_bytes() == b"harmless"


def test_the_stem_keeps_its_case(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    assert _save(app, uset, "Photo.PNG") == "Photo.png"
    assert (destination / "Photo.png").is_file()


def test_dots_inside_the_stem_are_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, DEFAULTS)
    assert _save(app, uset, "my.report.2026.txt") == "my.report.2026.txt"
    assert (destination / "my.report.2026.txt").is_file()


def test_archive_name_with_allowed_parts_is_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, DEFAULTS + ARCHIVES)
    assert _save(app, uset, "archive.tar.gz") == "archive.tar.gz"
    assert (destination / "archive.tar.gz").is_file()


def test_extensionless_upload_is_stored_when_allowed(tmp_path):
    app, uset, destination = make_set(tmp_path, ("",))
    assert _save(app, uset, "foo") == "foo"
    assert (destination / "foo").is_file()


def test_explicit_subfolder_is_used(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    assert _save(app, uset, "photo.jpg", folder="someguy") == "someguy/photo.jpg"
    assert (destination / "someguy" / "photo.jpg").is_file()


def test_subfolder_given_with_the_name_is_used(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    assert _save(app, uset, "boat.jpg", name="someguy/photo_123.") == (
        "someguy/photo_123.jpg"
    )
    assert (destination / "someguy" / "photo_123.jpg").is_file()


def test_explicit_name_without_an_extension_is_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    assert _save(app, uset, "photo.jpg", name="README") == "README"
    assert (destination / "README").is_file()


def test_a_link_that_stays_inside_the_destination_still_works(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES, create_destination=True)
    (destination / "real").mkdir()
    (destination / "link").symlink_to(destination / "real")
    assert _save(app, uset, "photo.jpg", folder="link") == "link/photo.jpg"
    assert (destination / "real" / "photo.jpg").is_file()


def test_an_explicitly_allowed_type_is_not_treated_as_refused(tmp_path):
    app, uset, destination = make_set(
        tmp_path, AllExcept(("php",)), allow=("php",)
    )
    assert _save(app, uset, "module.php.txt") == "module.php.txt"
    assert (destination / "module.php.txt").is_file()
