"""Functional: the plugin registration subsystem must keep working for
legitimately signed/trusted plugins under the secure default (signatures
required). A fix must not break normal plugin loading.
"""
from __future__ import annotations

import pytest

import conftest as H
import stigmem_node.plugins.lifecycle as lifecycle
from stigmem_node.plugins.discovery import DiscoveredPlugin
from stigmem_node.plugins.manifest import PluginManifest
from stigmem_node.plugins.registry import HookRegistry


def test_trusted_signed_plugin_registers(settings_guard, monkeypatch):
    s = H.Settings(
        db_path="/tmp/pluginok.db",
        host="127.0.0.1",
        node_url="http://localhost:8765",
        plugin_signing_required=True,
        plugin_trusted_publishers="trusted-publisher@example.com",
    )
    settings_guard(s)

    plugin = DiscoveredPlugin(
        manifest=PluginManifest(name="trusted-plugin", version="1.0.0"),
        entry_point_name="trusted_plugin",
        entry_point_value="trusted_plugin:manifest",
        signing_identity="trusted-publisher@example.com",
        signature_verified=True,
    )
    monkeypatch.setattr(lifecycle, "discover_plugin_manifests", lambda: [plugin])
    monkeypatch.setattr(
        lifecycle,
        "resolve_plugin_dependencies",
        lambda discovered, registered_plugins: list(discovered),
    )

    registry = HookRegistry()
    ordered = lifecycle.register_discovered_plugins(
        registry=registry, freeze=False, signing_required=True
    )
    assert [p.manifest.name for p in ordered] == ["trusted-plugin"]
