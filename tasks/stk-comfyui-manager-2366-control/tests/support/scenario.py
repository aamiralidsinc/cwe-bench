"""Run one product scenario in a child process and report the outcome as JSON.

The product reads its configuration and startup state when its modules are imported, so
each scenario gets a fresh interpreter with a fresh host double. The scenario never
computes a security decision itself: it drives the real product entry point (an HTTP
route table or the startup hook import) and records what the product did.
"""
import configparser
import json
import os
import ssl
import sys
import urllib.error
import urllib.request


def write_result(result):
    with open(os.environ["TASK_RESULT"], "w", encoding="utf-8") as handle:
        json.dump(result, handle)


def live_config_path(root):
    """Find the config file the product currently uses, skipping legacy backups."""
    found = []
    for directory, dirs, files in os.walk(os.path.join(root, "user")):
        parts = directory.split(os.sep)
        if ".legacy-manager-backup" in parts:
            continue
        if "config.ini" in files:
            found.append(os.path.join(directory, "config.ini"))
    if not found:
        return None
    return max(found, key=os.path.getmtime)


def http_exchange(method, path, body, timeout=180):
    request = urllib.request.Request("http://127.0.0.1:%d%s" % (PORT[0], path),
                                     data=(body.encode() if body is not None else None),
                                     method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")
    except Exception as error:  # no server response at all
        return None, repr(error)


PORT = [0]


def serve_routes(module):
    import asyncio
    from aiohttp import web

    app = web.Application()
    for method, path, handler in module.routes.items:
        adder = app.router.add_get if method == "GET" else app.router.add_post
        adder(path, handler)

    async def boot():
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        PORT[0] = runner.addresses[0][1]
        return runner

    return asyncio, boot


def run_http(config):
    import asyncio

    import manager_server as server

    loop_runner = serve_routes(server)

    async def main():
        asyncio_mod, boot = loop_runner
        runner = await boot()
        try:
            status, body = await asyncio_mod.to_thread(
                http_exchange, config.get("method", "GET"), config["path"],
                config.get("body"))
        finally:
            await runner.cleanup()
        return status, body

    status, body = asyncio.run(main())
    result = {"status": status, "body": body[:300],
              "marker": os.path.exists(config["marker"]) if config.get("marker") else None}
    if config.get("stored_level"):
        settings = configparser.ConfigParser(strict=False)
        settings.read(server.core.manager_config_path)
        result["stored_level"] = settings.get("default", "security_level", fallback=None)
        result["effective_level"] = server.core.get_config()["security_level"]
        result["config_path"] = server.core.manager_config_path
    return result


def run_schedule(config):
    import asyncio
    import json as jsonlib

    import manager_server as server

    core = server.core
    snapshots = core.manager_snapshot_path
    os.makedirs(snapshots, exist_ok=True)
    with open(os.path.join(snapshots, "legit.json"), "w", encoding="utf-8") as handle:
        jsonlib.dump({"custom_nodes": [],
                      "git_custom_nodes": {config["git_url"]: {"hash": "main"}}}, handle)

    asyncio_mod, boot = serve_routes(server)

    async def main():
        runner = await boot()
        try:
            status, _ = await asyncio_mod.to_thread(
                http_exchange, "GET", "/snapshot/restore?target=legit", None)
        finally:
            await runner.cleanup()
        return status

    status = asyncio.run(main())
    queued = os.path.join(core.manager_startup_script_path, "restore-snapshot.json")
    return {"status": status, "queued": os.path.exists(queued),
            "state": core.manager_files_path}


def run_level():
    import manager_core

    settings = manager_core.get_config()
    return {"level": settings.get("security_level"),
            "policy": settings.get("update_policy"),
            "state": manager_core.manager_files_path}


def run_write_config(config):
    import manager_core

    if config.get("network_mode"):
        manager_core.get_config()["network_mode"] = config["network_mode"]
    manager_core.write_config()
    found = live_config_path(manager_core.comfy_path)
    return {"config_path": found, "state": manager_core.manager_files_path}


def run_reserve(config):
    import manager_core

    manager_core.reserve_script(config["cwd"], config["command"])
    return {"state": manager_core.manager_files_path}


def trusted_configs(root):
    """Every live (non-backup) configuration under the user directory."""
    found = []
    for directory, dirs, files in os.walk(os.path.join(root, "user")):
        if ".legacy-manager-backup" in directory.split(os.sep):
            continue
        if "config.ini" in files:
            found.append(os.path.join(directory, "config.ini"))
    return sorted(found)


def run_seed_trusted(config):
    import manager_core

    manager_core.write_config()
    configs = trusted_configs(manager_core.comfy_path)
    if not configs:
        return {"config_path": None}
    for found in configs:
        settings = configparser.ConfigParser(strict=False)
        settings.read(found)
        if "default" not in settings:
            settings["default"] = {}
        settings["default"]["bypass_ssl"] = "true"
        settings["default"]["file_logging"] = "false"
        settings["default"]["downgrade_blacklist"] = "attacker-downgrade"
        with open(found, "w", encoding="utf-8") as handle:
            settings.write(handle)
        state = os.path.dirname(found)
        with open(os.path.join(state, "pip_overrides.json"), "w", encoding="utf-8") as handle:
            json.dump({"task-attacker-package": "evil-remapped"}, handle)
        with open(os.path.join(state, "pip_blacklist.list"), "w", encoding="utf-8") as handle:
            handle.write("attacker-pinned-package\n")
        with open(os.path.join(state, "pip_auto_fix.list"), "w", encoding="utf-8") as handle:
            handle.write("task-sentinel-pkg==9.9.9 --index-url %s\n" % config["index_url"])
    return {"config_path": configs[-1], "state": os.path.dirname(configs[-1])}


def run_observe():
    import prestartup_script as startup

    return {
        "bypass": ssl._create_default_https_context is ssl._create_unverified_context,
        "override": startup.remap_pip_package("task-attacker-package"),
        "use_uv": startup.manager_util.use_uv,
        "file_logging": startup.enable_file_logging,
        "blacklist_hit": "attacker-pinned-package" in startup.cm_global.pip_blacklist,
    }


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        config = json.load(handle)
    mode = config["mode"]
    if mode == "http":
        result = run_http(config)
    elif mode == "schedule":
        result = run_schedule(config)
    elif mode == "level":
        result = run_level()
    elif mode == "write_config":
        result = run_write_config(config)
    elif mode == "reserve":
        result = run_reserve(config)
    elif mode == "seed_trusted":
        result = run_seed_trusted(config)
    elif mode == "observe":
        result = run_observe()
    elif mode == "prestartup":
        import prestartup_script  # noqa: F401
        result = {"imported": True}
    else:
        result = {"error": "unknown mode %r" % mode}
    write_result(result)


if __name__ == "__main__":
    main()
