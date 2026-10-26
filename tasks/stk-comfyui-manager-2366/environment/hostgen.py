#!/usr/bin/env python3
"""Create two minimal ComfyUI host doubles for running ComfyUI-Manager locally.

The manager repository is a ComfyUI extension: at run time it imports the host's
``folder_paths`` module (and a handful of modules pulled in by the server package).
This script writes two host trees, one that models a current ComfyUI build and one
that models an older build, plus a shared directory of stand-in modules.

Usage: hostgen.py <destination>
"""
import os
import sys

HOST_NEW = '''"""Minimal ComfyUI folder_paths double: a current build with the System User API."""
import os

base_path = os.environ.get("COMFYUI_PATH") or os.path.dirname(os.path.realpath(__file__))
user_directory = os.path.join(base_path, "user")
models_dir = os.path.join(base_path, "models")
SYSTEM_USER_PREFIX = "__"

folder_names_and_paths = {
    "custom_nodes": ([os.path.join(base_path, "custom_nodes")], set()),
    "checkpoints": ([os.path.join(models_dir, "checkpoints")], {".ckpt", ".safetensors"}),
    "loras": ([os.path.join(models_dir, "loras")], {".ckpt", ".safetensors"}),
    "vae": ([os.path.join(models_dir, "vae")], {".ckpt", ".safetensors"}),
}


def get_user_directory() -> str:
    return user_directory


def set_user_directory(user_dir: str) -> None:
    global user_directory
    user_directory = user_dir


def get_public_user_directory(user_id: str):
    """Directories the HTTP file endpoints are allowed to touch.

    System users (the ``__`` prefix) are internal only and yield None here.
    """
    if not user_id or not isinstance(user_id, str):
        return None
    if user_id.startswith(SYSTEM_USER_PREFIX):
        return None
    return os.path.join(user_directory, user_id)


def get_system_user_directory(name: str = "system") -> str:
    """Internal-only directory for a system user."""
    if not name or not isinstance(name, str):
        raise ValueError("system user name cannot be empty")
    if not name.replace("_", "").isalnum():
        raise ValueError("invalid system user name: %r" % (name,))
    if name.startswith("_"):
        raise ValueError("system user name must not start with underscore")
    return os.path.join(user_directory, SYSTEM_USER_PREFIX + name)


def get_folder_paths(folder_name: str):
    entry = folder_names_and_paths.get(folder_name)
    return list(entry[0]) if entry else []


def get_filename_list(folder_name: str):
    return []


def get_save_image_path(*args, **kwargs):
    return os.path.join(base_path, "output"), "image", 1, "", ""
'''

HOST_LEGACY = '''"""Minimal ComfyUI folder_paths double: an older build, before the System User API."""
import os

base_path = os.environ.get("COMFYUI_PATH") or os.path.dirname(os.path.realpath(__file__))
user_directory = os.path.join(base_path, "user")
models_dir = os.path.join(base_path, "models")

folder_names_and_paths = {
    "custom_nodes": ([os.path.join(base_path, "custom_nodes")], set()),
    "checkpoints": ([os.path.join(models_dir, "checkpoints")], {".ckpt", ".safetensors"}),
    "loras": ([os.path.join(models_dir, "loras")], {".ckpt", ".safetensors"}),
    "vae": ([os.path.join(models_dir, "vae")], {".ckpt", ".safetensors"}),
}


def get_user_directory() -> str:
    return user_directory


def set_user_directory(user_dir: str) -> None:
    global user_directory
    user_directory = user_dir


def get_folder_paths(folder_name: str):
    entry = folder_names_and_paths.get(folder_name)
    return list(entry[0]) if entry else []


def get_filename_list(folder_name: str):
    return []


def get_save_image_path(*args, **kwargs):
    return os.path.join(base_path, "output"), "image", 1, "", ""
'''

SERVER = '''"""Stand-in for ComfyUI's prompt server, enough for the manager's route table."""
import os

ROOT = os.environ.get("COMFYUI_PATH") or os.getcwd()


class RouteTable:
    def __init__(self):
        self.items = []

    def _record(self, method):
        def decorator(path):
            def register(handler):
                self.items.append((method, path, handler))
                return handler
            return register
        return decorator

    def get(self, path):
        return self._record("GET")(path)

    def post(self, path):
        return self._record("POST")(path)


class PromptServer:
    instance = None

    def __init__(self):
        self.routes = RouteTable()
        self.events = []

    def send_sync(self, event, data=None, sid=None):
        self.events.append({"event": event, "data": data, "sid": sid})

    def add_on_prompt_handler(self, handler):
        return None


PromptServer.instance = PromptServer()
'''

NODES = '''"""Stand-in for ComfyUI's node registry."""
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
'''

LATENT = '''"""Stand-in for ComfyUI's preview method enum."""
import enum


class LatentPreviewMethod(enum.IntEnum):
    NoPreviews = 0
    Auto = 1
    Latent2RGB = 2
    TAESplit = 3
    TAESD = 4
'''

CLI_ARGS = '''"""Command line arguments a running ComfyUI server would have parsed."""


class Args:
    listen = "127.0.0.1"
    port = 8188
    preview_method = None
    base_directory = None
    models_directory = None


args = Args()
'''

EXTRA_CONFIG = '''"""Stand-in for ComfyUI's extra model path loader."""


def load_extra_path_config(path):
    return None
'''

README = """# ComfyUI host doubles

ComfyUI-Manager normally runs inside ComfyUI. This image has no ComfyUI checkout, so
`/opt/comfyui` holds two small host doubles that stand in for `folder_paths` and the
modules the manager's server package imports.

- `host-new`: models a current ComfyUI build. Its `folder_paths` exposes the System
  User Protection API: `get_system_user_directory(NAME)` returns `<user>/__NAME`, and
  the `__` prefix is reserved for internal users that the HTTP file endpoints cannot
  reach. `get_public_user_directory(ID)` returns None for those names.
- `host-legacy`: models an older build. It has `get_user_directory()` but no knowledge
  of system users, so every directory below the user directory is reachable from the
  HTTP file endpoints.
- `common`: shared stand-ins (`server`, `nodes`, `latent_preview`, `comfy`, `utils`).

To run the manager against one of them, put the host directory and the manager's
`glob` directory on the path and point `COMFYUI_FOLDERS_BASE_PATH` at a scratch
ComfyUI tree:

    mkdir -p /tmp/comfy/custom_nodes /tmp/comfy/user
    COMFYUI_PATH=/tmp/comfy \\
    PYTHONPATH=/opt/comfyui/host-new:/opt/comfyui/common:/workspace/glob:/workspace \\
    python3 -c 'import manager_core; print(manager_core.manager_files_path)'

`prestartup_script.py` is imported by ComfyUI before the rest of the extension loads,
so it can be exercised the same way.
"""


def write_tree(root, files):
    for relative, text in files.items():
        path = os.path.join(root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)


def main(argv):
    if len(argv) != 2:
        print("usage: hostgen.py <destination>", file=sys.stderr)
        return 2
    root = os.path.abspath(argv[1])
    common = {
        "server.py": SERVER,
        "nodes.py": NODES,
        "latent_preview.py": LATENT,
        "comfy/__init__.py": "",
        "comfy/cli_args.py": CLI_ARGS,
        "utils/__init__.py": "",
        "utils/extra_config.py": EXTRA_CONFIG,
    }
    write_tree(os.path.join(root, "common"), common)
    write_tree(os.path.join(root, "host-new"), {"folder_paths.py": HOST_NEW})
    write_tree(os.path.join(root, "host-legacy"), {"folder_paths.py": HOST_LEGACY})
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as handle:
        handle.write(README)
    print("host doubles written to " + root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
