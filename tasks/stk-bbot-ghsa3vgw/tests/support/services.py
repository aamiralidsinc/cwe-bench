"""Build the service modules under test and answer their remote calls locally."""
from support.harness import FakeResponse, load_module, new_scan, run

APKPURE = ("bbot.modules.apkpure", "apkpure")
POSTMAN = ("bbot.modules.postman_download", "postman_download")


async def _nothing():
    return None


def apkpure_module(tmp_path):
    output = tmp_path / "apk-out"
    scan = new_scan(modules=["apkpure"], module_config={"modules": {"apkpure": {"output_folder": str(output)}}})
    module = load_module(*APKPURE, scan)
    run(module.setup())
    # the module must never need the network to be judged: the remote call answers "nothing"
    scan.helpers.request = lambda *_a, **_k: _nothing()
    return scan, module, output / "apk_files"


def postman_module(tmp_path):
    output = tmp_path / "pm-out"
    scan = new_scan(
        modules=["postman_download"],
        module_config={"modules": {"postman_download": {"output_folder": str(output)}}},
    )
    module = load_module(*POSTMAN, scan)
    module.auth_required = False
    assert run(module.setup()) is True
    return scan, module, output / "postman_workspaces"


def serve_postman(scan, module, workspace_name, collection_name=None):
    """Answer the Postman API endpoints the download module uses."""
    collections = [{"uid": "collection-1"}] if collection_name else []

    async def request(url, **_kwargs):
        if "ws/proxy" in url:
            return FakeResponse({"data": [{"id": "wsid-1"}]})
        if url.endswith("/globals"):
            return FakeResponse({"data": {"id": "globals-1"}})
        return FakeResponse({})

    async def api_request(url, **_kwargs):
        if "/collections/" in url:
            return FakeResponse({"collection": {"info": {"name": collection_name}}})
        return FakeResponse({"workspace": {"name": workspace_name, "id": "wsid-1", "collections": collections}})

    scan.helpers.request = request
    module.api_request = api_request
