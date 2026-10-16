"""V4 — when plugin signature enforcement is turned off, the node loads unsigned
third-party plugin code at startup with no explicit operator acknowledgement,
silently executing untrusted code.

Security property: disabling signature enforcement must not be sufficient on its
own to load unsigned plugins; at startup, with no explicit operator
acknowledgement given (the default), the node must either refuse to start or
start without the unsigned plugin registered (a refusal must be deliberate, not a
crash). Exercised through the real startup
path (create_app lifespan), as the instruction describes, not an internal call.
"""
from __future__ import annotations

import conftest as H
import stigmem_node.plugins.lifecycle as lifecycle
import stigmem_node.plugins.registry as registry_module
from stigmem_node.plugins.discovery import DiscoveredPlugin
from stigmem_node.plugins.manifest import PluginManifest
from stigmem_node.plugins.registry import HookRegistry


def test_unsigned_plugin_refused_without_acknowledgement(settings_guard, monkeypatch, tmp_path):
    # Signature enforcement off, but NO extra acknowledgement configured (the
    # default). A correct fix must still keep the unsigned plugin from loading.
    plugin = DiscoveredPlugin(
        manifest=PluginManifest(name="untrusted-plugin", version="0.1.0"),
        entry_point_name="untrusted_plugin",
        entry_point_value="untrusted_plugin:manifest",
    )
    monkeypatch.setattr(lifecycle, "discover_plugin_manifests", lambda: [plugin])
    monkeypatch.setattr(
        lifecycle,
        "resolve_plugin_dependencies",
        lambda discovered, registered_plugins: list(discovered),
    )
    fresh = HookRegistry()
    previous = registry_module.set_registry(fresh)
    try:
        booted = H.start_node(
            settings_guard,
            lambda: H.Settings(
                db_path=str(tmp_path / "v4.db"),
                host="127.0.0.1",
                node_url="http://localhost:8765",
                plugin_signing_required=False,
            ),
        )
    finally:
        registry_module.set_registry(previous)

    loaded = booted and "untrusted-plugin" in fresh.registered_plugins()
    assert not loaded, (
        "node started and registered an unsigned plugin with signature enforcement "
        "off and no explicit operator acknowledgement"
    )
