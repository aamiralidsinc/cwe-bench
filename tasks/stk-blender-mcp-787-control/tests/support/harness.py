"""Shared offline harness for the hidden suites.

The product is the Blender add-on.  Blender itself is replaced by ``support/block_bpy`` and
the remote services by ``support.fake_requests``; the add-on's own local socket command
protocol (the interface the MCP server speaks) is the entry point every test drives.
"""

import contextlib
import importlib
import json
import os
import pathlib
import socket
import sys
import tempfile
import time

_HERE = pathlib.Path(__file__).resolve().parent
_BLOCK = str(_HERE / "block_bpy")


def _install_paths(value):
    if _BLOCK not in sys.path:
        sys.path.insert(0, _BLOCK)
    if value not in sys.path:
        sys.path.insert(0, value)


def import_addon(workspace):
    """Import the product add-on with the Blender stand-in on the path."""
    _install_paths(str(workspace))
    return importlib.import_module("addon")


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


def _read_json(sock, timeout):
    sock.settimeout(timeout)
    buf = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            return json.loads(buf.decode("utf-8"))
        except json.JSONDecodeError:
            continue
    raise AssertionError("no JSON response (received %r)" % buf[:400])


class Product:
    """One add-on server, one sandbox.  ``call`` speaks the socket command protocol."""

    def __init__(self, workspace, root):
        self.workspace = pathlib.Path(workspace)
        self.root = pathlib.Path(root)
        self.private = self.root / "private"
        self.private.mkdir(parents=True, exist_ok=True)
        self.addon = import_addon(self.workspace)
        self.bpy = sys.modules["bpy"]
        from support.fake_requests import FakeRequests
        self.fake = FakeRequests()
        self.addon.requests = self.fake
        self._server = None
        self.port = None
        self._old_tmpdir = tempfile.tempdir

    def __enter__(self):
        tempfile.tempdir = str(self.private)
        self.bpy.reset()
        scene = self.bpy.context.scene
        scene.blendermcp_use_polyhaven = True
        scene.blendermcp_use_hyper3d = True
        scene.blendermcp_use_sketchfab = True
        scene.blendermcp_use_hunyuan3d = False
        scene.blendermcp_hyper3d_mode = "MAIN_SITE"
        scene.blendermcp_hyper3d_api_key = "test-hyper3d-key"
        scene.blendermcp_sketchfab_api_key = "test-sketchfab-key"
        port = free_port()
        server = self.addon.BlenderMCPServer(host="127.0.0.1", port=port)
        server.start()
        last = None
        for _ in range(100):
            try:
                probe = socket.create_connection(("127.0.0.1", port), timeout=0.2)
                probe.close()
                last = None
                break
            except OSError as exc:
                last = exc
                time.sleep(0.05)
        if last is not None:
            server.stop()
            raise AssertionError("add-on server did not start: %r" % (last,))
        self._server = server
        self.port = port
        return self

    def __exit__(self, *exc_info):
        if self._server is not None:
            self._server.stop()
        tempfile.tempdir = self._old_tmpdir
        self.bpy.reset()
        return False

    def call(self, command_type, params, timeout=30.0):
        with socket.create_connection(("127.0.0.1", self.port), timeout=timeout) as sock:
            sock.sendall(json.dumps({"type": command_type, "params": params}).encode("utf-8"))
            return _read_json(sock, timeout)

    def snapshot_import(self):
        """Record the asset folder tree at the moment Blender imports the main file."""
        seen = {}
        def hook(name, kwargs):
            if name in ("import_scene.gltf", "import_scene.fbx", "import_scene.obj",
                        "wm.obj_import"):
                path = kwargs.get("filepath")
                if path:
                    seen["filepath"] = str(path)
                    seen["tree"] = _tree(pathlib.Path(path).parent)
        self.bpy.op_hook = hook
        return seen


def _tree(root):
    root = pathlib.Path(root)
    out = []
    if not root.is_dir():
        return out
    for base, dirs, files in os.walk(root):
        for name in sorted(files):
            out.append(str(pathlib.Path(base, name).relative_to(root)))
        for name in sorted(dirs):
            rel = str(pathlib.Path(base, name).relative_to(root))
            if rel:
                out.append(rel + "/")
    return sorted(out)


def outside(root, name):
    path = pathlib.Path(root) / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def visible_files(path):
    path = pathlib.Path(path)
    if not path.exists():
        return []
    return sorted(str(p) for p in path.rglob("*")) if path.is_dir() else [str(path)]


def make_zip(entries):
    """Build a zip archive in memory.  ``entries`` maps member name to bytes."""
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()
