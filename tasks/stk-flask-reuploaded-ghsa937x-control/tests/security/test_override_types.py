"""An explicit stored name must not be able to carry a refused file type."""
import pytest
from conftest import files_under
from conftest import make_set
from conftest import upload
from flask_uploads import ALL
from flask_uploads import DEFAULTS
from flask_uploads import IMAGES
from flask_uploads import UploadNotAllowed


def test_explicit_name_with_a_refused_type_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("photo.jpg"), name="payload.php")
    assert files_under(destination) == []


def test_explicit_name_with_another_refused_type_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("photo.jpg"), name="payload.html")
    assert files_under(destination) == []


def test_explicit_name_with_a_refused_script_type_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, DEFAULTS)
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("notes.txt"), name="payload.py")
    assert files_under(destination) == []


def test_explicit_name_in_a_subfolder_with_a_refused_type_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, IMAGES)
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("photo.jpg"), name="users/payload.php")
    assert files_under(destination) == []


def test_explicit_name_with_a_denied_type_is_not_stored(tmp_path):
    app, uset, destination = make_set(tmp_path, ALL, deny=("sh",))
    with app.test_request_context():
        with pytest.raises(UploadNotAllowed):
            uset.save(upload("notes.txt"), name="payload.sh")
    assert files_under(destination) == []
