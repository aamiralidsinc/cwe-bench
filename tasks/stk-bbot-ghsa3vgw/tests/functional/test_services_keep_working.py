"""Ordinary service data keeps being saved exactly as it is today."""
import zipfile

from support.harness import FakeResponse, make_event, run
from support.services import apkpure_module, postman_module, serve_postman


def test_apk_still_downloads_into_its_app_folder(tmp_path):
    scan, module, root = apkpure_module(tmp_path)

    async def response(_url, **_kwargs):
        return FakeResponse(
            headers={"Content-Disposition": 'attachment; filename="app.apk"'},
            content=b"APK-CONTENT",
        )

    scan.helpers.request = response
    event = make_event(
        scan,
        {"url": "https://play.google.com/store/apps/details?id=com.example.app"},
        "MOBILE_APP",
        ["android"],
    )
    run(module.handle_event(event))
    downloaded = root / "com.example.app" / "com.example.app.apk"
    assert downloaded.is_file(), "an ordinary app download no longer lands in its folder"
    assert downloaded.read_bytes() == b"APK-CONTENT"


def test_postman_workspace_still_saves_in_its_own_folder(tmp_path):
    scan, module, root = postman_module(tmp_path)
    serve_postman(scan, module, "My Workspace", collection_name="My Collection")
    event = make_event(scan, {"url": "https://www.postman.com/acme/workspace"}, "CODE_REPOSITORY", ["postman"])
    run(module.handle_event(event))

    folder = root / "My Workspace"
    assert folder.is_dir(), "an ordinary workspace no longer keeps its own folder"
    archive = folder / "wsid-1.zip"
    assert archive.is_file(), "an ordinary workspace archive was not written"
    with zipfile.ZipFile(archive) as saved:
        names = set(saved.namelist())
    assert "My Workspace.postman_workspace.json" in names
    assert "globals-1.postman_environment.json" in names
    assert "My Collection.postman_collection.json" in names, (
        "an ordinary collection is no longer included in the saved workspace"
    )
