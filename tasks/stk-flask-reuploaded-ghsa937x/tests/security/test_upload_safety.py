"""A stored file must never carry a type the set refuses, and must stay inside the destination."""
import pytest
from conftest import files_under
from conftest import make_set
from conftest import upload
from flask_uploads import AllExcept
from flask_uploads import DEFAULTS
from flask_uploads import IMAGES
from flask_uploads import SCRIPTS
from flask_uploads import UploadNotAllowed


def test_explicit_name_with_a_refused_type_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("photo.jpg"), name="payload.php")
    assert files_under(destination) == []


def test_explicit_name_is_checked_without_regard_to_case(tmp_path):
    app, uset, destination = make_set(tmp_path, AllExcept(SCRIPTS))
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("safe.txt"), name="backdoor.PHP")
    assert files_under(destination) == []


def test_refused_type_before_the_last_dot_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, DEFAULTS, deny=("php",))
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("report.php.txt"))
    assert files_under(destination) == []


def test_preset_refused_type_before_the_last_dot_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, AllExcept(SCRIPTS))
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("report.php.txt"))
    assert files_under(destination) == []


def test_explicit_folder_cannot_escape_the_destination(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    escape = tmp_path / "outside"
    with app.test_request_context():
        try:
            uset.save(upload("safe.jpg"), folder="../outside")
        except Exception:  # noqa: BLE001 - any refusal is acceptable here
            pass
    assert not (escape / "safe.jpg").exists()


def test_name_folder_cannot_escape_the_destination(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    escape = tmp_path / "outside"
    with app.test_request_context():
        try:
            uset.save(upload("safe.jpg"), name="../outside/payload.jpg")
        except Exception:  # noqa: BLE001 - any refusal is acceptable here
            pass
    assert not (escape / "payload.jpg").exists()


def test_symlinked_subfolder_cannot_escape_the_destination(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES, create_destination=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (destination / "link").symlink_to(outside)
    with app.test_request_context():
        try:
            uset.save(upload("safe.jpg"), folder="link")
        except Exception:  # noqa: BLE001 - any refusal is acceptable here
            pass
    assert not (outside / "safe.jpg").exists()


def test_symlinked_filename_cannot_escape_the_destination(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES, create_destination=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (destination / "safe.jpg").symlink_to(outside / "owned.jpg")
    with app.test_request_context():
        try:
            uset.save(upload("safe.jpg"))
        except Exception:  # noqa: BLE001 - any refusal is acceptable here
            pass
    assert not (outside / "owned.jpg").exists()
