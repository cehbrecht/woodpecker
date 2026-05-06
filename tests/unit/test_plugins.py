from __future__ import annotations

from types import SimpleNamespace

import pytest

from woodpecker.fixes import plugins


def test_load_plugins_imports_module_entrypoint(monkeypatch):
    calls: list[str] = []

    def fake_load():
        calls.append("loaded-module")
        return object()  # module import side effects already happened

    monkeypatch.setattr(
        plugins,
        "_iter_plugin_entry_points",
        lambda: [SimpleNamespace(name="module_plugin", load=fake_load)],
    )
    monkeypatch.setattr(plugins, "_PLUGINS_LOADED", False)

    plugins.load_plugins()
    assert calls == ["loaded-module"]


def test_load_plugins_calls_loader_function_entrypoint(monkeypatch):
    calls: list[str] = []

    def plugin_loader():
        calls.append("called-loader")

    def fake_load():
        calls.append("loaded-entrypoint")
        return plugin_loader

    monkeypatch.setattr(
        plugins,
        "_iter_plugin_entry_points",
        lambda: [SimpleNamespace(name="callable_plugin", load=fake_load)],
    )
    monkeypatch.setattr(plugins, "_PLUGINS_LOADED", False)

    plugins.load_plugins()
    assert calls == ["loaded-entrypoint", "called-loader"]


def test_load_plugins_warns_on_plugin_error(monkeypatch):
    def fake_load():
        raise RuntimeError("boom")

    monkeypatch.setattr(
        plugins,
        "_iter_plugin_entry_points",
        lambda: [SimpleNamespace(name="bad_plugin", load=fake_load)],
    )
    monkeypatch.setattr(plugins, "_PLUGINS_LOADED", False)

    with pytest.warns(RuntimeWarning, match="Failed to load woodpecker plugin 'bad_plugin'"):
        plugins.load_plugins()


def test_load_plugins_runs_once(monkeypatch):
    calls: list[str] = []

    def fake_load():
        calls.append("loaded-once")
        return object()

    monkeypatch.setattr(
        plugins,
        "_iter_plugin_entry_points",
        lambda: [SimpleNamespace(name="once_plugin", load=fake_load)],
    )
    monkeypatch.setattr(plugins, "_PLUGINS_LOADED", False)

    plugins.load_plugins()
    plugins.load_plugins()

    assert calls == ["loaded-once"]
