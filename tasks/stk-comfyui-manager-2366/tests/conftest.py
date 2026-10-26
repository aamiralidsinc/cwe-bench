"""Harness for the ComfyUI-Manager task.

Every test runs the product in a child process against a fresh ComfyUI host double,
because the manager reads its configuration and startup files at import time. Nothing
here imports product code; the child scenario scripts do that from the restored
workspace, and the tests only inspect their JSON report and harmless marker files.
"""
import http.server
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import functools

import pytest

REPO = os.environ.get("TASK_REPO") or "/workspace"
SUPPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "support")

_NEW_FOLDER_PATHS = '''import os

_ROOT = os.environ.get("COMFYUI_PATH") or os.getcwd()
USER_DIR = os.path.join(_ROOT, "user")
user_directory = USER_DIR
_MODELS = os.path.join(_ROOT, "models")
PREFIX = "__"

folder_names_and_paths = {
    "custom_nodes": ([os.path.join(_ROOT, "custom_nodes")], set()),
    "checkpoints": ([os.path.join(_MODELS, "checkpoints")], {".safetensors"}),
    "loras": ([os.path.join(_MODELS, "loras")], {".safetensors"}),
}


def get_user_directory():
    return USER_DIR


def set_user_directory(value):
    global USER_DIR, user_directory
    USER_DIR = value
    user_directory = value


def get_public_user_directory(ident):
    if not ident or not isinstance(ident, str):
        return None
    if ident[:2] == PREFIX:
        return None
    return os.path.join(USER_DIR, ident)


def get_system_user_directory(name="system"):
    if not isinstance(name, str) or not name:
        raise ValueError("bad system user name")
    if name[0] == "_" or not name.replace("_", "").isalnum():
        raise ValueError("bad system user name")
    return os.path.join(USER_DIR, PREFIX + name)


def get_folder_paths(name):
    value = folder_names_and_paths.get(name)
    return list(value[0]) if value else []


def get_filename_list(name):
    return []
'''

_LEGACY_FOLDER_PATHS = '''import os

_ROOT = os.environ.get("COMFYUI_PATH") or os.getcwd()
USER_DIR = os.path.join(_ROOT, "user")
user_directory = USER_DIR
_MODELS = os.path.join(_ROOT, "models")

folder_names_and_paths = {
    "custom_nodes": ([os.path.join(_ROOT, "custom_nodes")], set()),
    "checkpoints": ([os.path.join(_MODELS, "checkpoints")], {".safetensors"}),
    "loras": ([os.path.join(_MODELS, "loras")], {".safetensors"}),
}


def get_user_directory():
    return USER_DIR


def set_user_directory(value):
    global USER_DIR, user_directory
    USER_DIR = value
    user_directory = value


def get_folder_paths(name):
    value = folder_names_and_paths.get(name)
    return list(value[0]) if value else []


def get_filename_list(name):
    return []
'''

_SERVER = '''class Table:
    def __init__(self):
        self.items = []
    def get(self, path):
        def keep(fn):
            self.items.append(("GET", path, fn)); return fn
        return keep
    def post(self, path):
        def keep(fn):
            self.items.append(("POST", path, fn)); return fn
        return keep

class _Server:
    def __init__(self):
        self.routes = Table()
        self.events = []
    def send_sync(self, name, payload=None, sid=None):
        self.events.append((name, payload))

_Server.instance = _Server()
PromptServer = _Server
'''

_NODES = "NODE_CLASS_MAPPINGS = {}\n"

_LATENT = '''class LatentPreviewMethod:
    NoPreviews = 0
    Auto = 1
    Latent2RGB = 2
    TAESplit = 3
    TAESD = 4
'''

_CLI = '''class Args:
    listen = "127.0.0.1"
    port = 8188
    preview_method = None
    base_directory = None
    models_directory = None

args = Args()
'''

_EXTRA = "def load_extra_path_config(path):\n    return None\n"

_COMMON = {
    "server.py": _SERVER,
    "nodes.py": _NODES,
    "latent_preview.py": _LATENT,
    "comfy/__init__.py": "",
    "comfy/cli_args.py": _CLI,
    "utils/__init__.py": "",
    "utils/extra_config.py": _EXTRA,
}


def _put(path, text):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(text)
    finally:
        handle.close()


def free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class Host:
    """A fresh ComfyUI tree plus a host double of the requested generation."""

    def __init__(self, root, kind):
        self.root = root
        self.kind = kind
        self.comfy = os.path.join(root, "comfyui")
        self.hostdir = os.path.join(root, "host-" + kind)
        self.common = os.path.join(root, "common")
        for sub in ("custom_nodes", "user", "models", "output"):
            os.makedirs(os.path.join(self.comfy, sub), exist_ok=True)
        _put(os.path.join(self.comfy, "requirements.txt"), "# host requirements\n")
        for rel, text in _COMMON.items():
            _put(os.path.join(self.common, rel), text)
        source = _NEW_FOLDER_PATHS if kind == "new" else _LEGACY_FOLDER_PATHS
        _put(os.path.join(self.hostdir, "folder_paths.py"), source)
        self.home = os.path.join(root, "home")
        self.tmp = os.path.join(root, "tmp")
        os.makedirs(self.home, exist_ok=True)
        os.makedirs(self.tmp, exist_ok=True)

    @property
    def user(self):
        return os.path.join(self.comfy, "user")

    @property
    def legacy_manager(self):
        return os.path.join(self.user, "default", "ComfyUI-Manager")

    @property
    def protected_manager(self):
        return os.path.join(self.user, "__manager")

    def seed(self, where, relative, text):
        base = self.legacy_manager if where == "legacy" else self.protected_manager
        _put(os.path.join(base, relative), text)

    def config_text(self, level=None, network="offline", extra=""):
        body = "[default]\nnetwork_mode = %s\n" % network
        if level is not None:
            body += "security_level = %s\n" % level
        return body + extra

    def env(self, extra=None):
        values = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": self.home,
            "TMPDIR": self.tmp,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "PYTHONDONTWRITEBYTECODE": "1",
            "COMFYUI_PATH": self.comfy,
            "PYTHONPATH": os.pathsep.join([self.hostdir, self.common,
                                           os.path.join(REPO, "glob"), REPO]),
            "__COMFY_CLI_SESSION__": os.path.join(self.tmp, "session"),
        }
        values.update(extra or {})
        return values

    def scenario(self, config, timeout=300, extra_env=None):
        config_path = os.path.join(self.tmp, "scenario.json")
        result_path = os.path.join(self.tmp, "result.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(config, handle)
        if os.path.exists(result_path):
            os.remove(result_path)
        env = self.env(dict({"TASK_RESULT": result_path}, **(extra_env or {})))
        proc = subprocess.run([sys.executable, os.path.join(SUPPORT, "scenario.py"), config_path],
                              cwd=self.tmp, env=env, capture_output=True, text=True,
                              timeout=timeout, stdin=subprocess.DEVNULL)
        if os.path.exists(result_path):
            with open(result_path, "r", encoding="utf-8") as handle:
                result = json.load(handle)
        else:
            result = {}
        result["_returncode"] = proc.returncode
        result["_stderr"] = proc.stderr[-3000:]
        return result


class GitDrop:
    """A local dumb-HTTP git repository whose install script drops a marker."""

    def __init__(self, root, marker):
        self.root = root
        self.marker = marker
        self.served = os.path.join(root, "served")
        source = os.path.join(root, "source")
        os.makedirs(source, exist_ok=True)
        _put(os.path.join(source, "install.py"),
             "import os\nopen(os.environ['TASK_MARKER'], 'w').write('ran')\n")
        for cmd in (["git", "init", "-q", "-b", "main"],
                    ["git", "add", "install.py"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@localhost",
                     "commit", "-qm", "init"]):
            subprocess.run(cmd, cwd=source, check=True, capture_output=True)
        bare = os.path.join(self.served, "evil.git")
        os.makedirs(self.served, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--bare", source, bare], check=True,
                       capture_output=True)
        subprocess.run(["git", "update-server-info"], cwd=bare, check=True,
                       capture_output=True)
        handler = functools.partial(_QuietHandler, directory=self.served)
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self):
        return "http://127.0.0.1:%d/evil.git" % self.port

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class IndexCounter:
    """A loopback package index that counts requests and serves an empty page."""

    def __init__(self):
        self.hits = 0
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                outer.hits += 1
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html></html>")

            def log_message(self, *args):
                pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self):
        return "http://127.0.0.1:%d/simple" % self.port

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def host_new(tmp_path):
    return Host(str(tmp_path / "new"), "new")


@pytest.fixture
def host_legacy(tmp_path):
    return Host(str(tmp_path / "legacy"), "legacy")


@pytest.fixture
def evil_repo(tmp_path):
    drop = GitDrop(str(tmp_path / "git"), str(tmp_path / "marker"))
    yield drop
    drop.close()


@pytest.fixture
def index_server():
    counter = IndexCounter()
    yield counter
    counter.close()


def marker_path(tmp_path):
    return str(tmp_path / "marker")


def any_client_error(status):
    return isinstance(status, int) and 400 <= status < 500
