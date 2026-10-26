"""Names received from remote services must not place saved data outside the service folder."""
from support.harness import created_since, is_under, make_event, run, snapshot
from support.services import apkpure_module, postman_module, serve_postman


def _assert_no_escaped_paths(tmp_path, root, before):
    escaped = [p for p in created_since(tmp_path, before) if not is_under(p, root)]
    assert not escaped, f"paths were created outside {root}: {escaped}"


def test_app_id_cannot_write_outside_its_folder(tmp_path):
    scan, module, root = apkpure_module(tmp_path)
    before = snapshot(tmp_path)
    event = make_event(
        scan,
        {"url": "https://play.google.com/store/apps/details?id=../../escaped-app"},
        "MOBILE_APP",
        ["android"],
    )
    run(module.handle_event(event))
    _assert_no_escaped_paths(tmp_path, root, before)


def test_absolute_app_id_cannot_write_outside_its_folder(tmp_path):
    scan, module, root = apkpure_module(tmp_path)
    absolute = str(tmp_path / "absolute-victim")
    before = snapshot(tmp_path)
    event = make_event(
        scan,
        {"url": f"https://play.google.com/store/apps/details?id={absolute}"},
        "MOBILE_APP",
        ["android"],
    )
    run(module.handle_event(event))
    _assert_no_escaped_paths(tmp_path, root, before)


def test_workspace_name_cannot_write_outside_its_folder(tmp_path):
    scan, module, root = postman_module(tmp_path)
    serve_postman(scan, module, "../../escaped-workspace")
    before = snapshot(tmp_path)
    event = make_event(scan, {"url": "https://www.postman.com/acme/workspace"}, "CODE_REPOSITORY", ["postman"])
    run(module.handle_event(event))
    _assert_no_escaped_paths(tmp_path, root, before)


def test_absolute_workspace_name_cannot_write_outside_its_folder(tmp_path):
    scan, module, root = postman_module(tmp_path)
    serve_postman(scan, module, str(tmp_path / "absolute-workspace"))
    before = snapshot(tmp_path)
    event = make_event(scan, {"url": "https://www.postman.com/acme/workspace"}, "CODE_REPOSITORY", ["postman"])
    run(module.handle_event(event))
    _assert_no_escaped_paths(tmp_path, root, before)
