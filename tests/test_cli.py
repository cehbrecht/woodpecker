import json
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import click
from click.testing import CliRunner

from woodpecker.cli import cli, format_provenance_source


def test_list_fixes_contains_known_codes():
    runner = CliRunner()
    result = runner.invoke(cli, ["list-fixes", "--format", "text"])

    assert result.exit_code == 0
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output
    assert "woodpecker.ensure_latitude_is_increasing" in result.output


def test_io_status_text_output_contains_expected_keys():
    runner = CliRunner()
    result = runner.invoke(cli, ["io-status"])

    assert result.exit_code == 0
    assert "xarray_input:" in result.output
    assert "netcdf_input:" in result.output
    assert "zarr_output:" in result.output


def test_io_status_json_output_structure():
    runner = CliRunner()
    result = runner.invoke(cli, ["io-status", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    expected_keys = {
        "xarray_input",
        "netcdf_input",
        "zarr_input",
        "netcdf_output",
        "zarr_output",
    }
    assert set(payload.keys()) == expected_keys
    assert all(isinstance(payload[key], bool) for key in expected_keys)


def test_check_returns_zero_when_no_findings(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_decadal_ok.nc")
    result = runner.invoke(
        cli, ["check", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin"]
    )

    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_check_returns_nonzero_when_findings_exist(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "code": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "synthetic finding",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.run_check", _fake_run_check)

    result = runner.invoke(
        cli, ["check", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin"]
    )

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_check_json_output_structure(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "code": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "synthetic finding",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.run_check", _fake_run_check)

    result = runner.invoke(
        cli,
        ["check", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin", "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload
    assert {"path", "code", "name", "message"}.issubset(payload[0].keys())
    assert payload[0]["code"] == "woodpecker.normalize_tas_units_to_kelvin"


def test_fix_write_cmip6d01_reports_no_change_for_empty_fallback_dataset(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("c3s-cmip6-decadal.case.nc")

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--force-apply",
            "--output-format",
            "netcdf",
        ],
    )

    assert result.exit_code == 0
    assert "1 fix applications attempted" in result.output
    assert "0 files changed" in result.output


def test_fix_json_output_contains_write_report(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    def _fake_run_fix(*args, **kwargs):
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 1,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.cli.run_fix", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--output-format",
            "netcdf",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "write"
    assert payload["output_format"] == "netcdf"
    assert payload["attempted"] == 1
    assert payload["changed"] == 1
    assert payload["persist_attempted"] == 1
    assert payload["persisted"] == 1
    assert payload["persist_failed"] == 0
    assert payload["force_apply"] is False


def test_fix_json_write_exits_nonzero_on_persist_failure(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    def _fake_run_fix(*args, **kwargs):
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 0,
            "persist_failed": 1,
        }

    monkeypatch.setattr("woodpecker.cli.run_fix", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["persist_failed"] == 1


def test_check_unknown_fix_code_returns_click_error(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    result = runner.invoke(cli, ["check", ".", "--select", "DOESNOTEXIST"])

    assert result.exit_code != 0
    assert "Unknown fix identifier(s): DOESNOTEXIST" in result.output


def test_check_uses_plan_defaults(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "core.basic",
                        "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "code": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "configured by plan",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.run_check", _fake_run_check)

    result = runner.invoke(cli, ["check", "--plan", "plan.json"])

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_fix_uses_auto_output_format_when_not_set(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")
    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "core.basic",
                        "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def _fake_run_fix(inputs, fixes, dry_run, output_format):
        _ = (inputs, fixes, dry_run)
        assert output_format == "auto"
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 1,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.cli.run_fix", _fake_run_fix)

    result = runner.invoke(
        cli,
        ["fix", "--plan", "plan.json", "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["output_format"] == "auto"


def test_check_plan_applies_fix_options_to_message(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("c3s-cmip6.member.nc")
    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "cmip6-msg",
                        "fixes": [
                            {
                                "id": "woodpecker.normalize_tas_units_to_kelvin",
                                "options": {"message": "configured check message"},
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def _fake_run_check(_inputs, fixes):
        message = "default"
        if fixes and hasattr(fixes[0], "config"):
            message = fixes[0].config.get("message", message)
        return [
            {
                "path": "c3s-cmip6.member.nc",
                "code": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": message,
            }
        ]

    monkeypatch.setattr("woodpecker.cli.run_check", _fake_run_check)

    result = runner.invoke(cli, ["check", "--plan", "plan.json"])

    assert result.exit_code == 1
    assert "configured check message" in result.output


def test_fix_writes_provenance_file_by_default(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    result = runner.invoke(
        cli, ["fix", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin"]
    )

    assert result.exit_code == 0
    prov_path = Path("woodpecker.prov.json")
    assert prov_path.exists()
    payload = json.loads(prov_path.read_text(encoding="utf-8"))
    assert "activity" in payload
    assert "entity" in payload


def test_fix_force_apply_is_forwarded_to_runner(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    captured = {}

    def _fake_run_fix(*args, **kwargs):
        captured.update(kwargs)
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 1,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.cli.run_fix", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--force-apply",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured.get("force_apply") is True
    payload = json.loads(result.output)
    assert payload["force_apply"] is True


def test_fix_force_apply_requires_selected_codes(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["fix", ".", "--force-apply"])

    assert result.exit_code != 0
    assert "--force-apply requires explicit fix selection" in result.output


def test_check_uses_json_plan_store_lookup(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "cmip6-default",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "code": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "from json store",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.run_check", _fake_run_check)

    result = runner.invoke(
        cli,
        ["check", ".", "--plan", "plans.json"],
    )

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_check_plan_store_requires_plan_id_when_multiple_match_without_path_filters(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "first",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                },
                {
                    "id": "second",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "fixes": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                },
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        ["check", ".", "--plan", "plans.json"],
    )

    assert result.exit_code != 0
    assert "Multiple matching fix plans found" in result.output


def test_check_plan_store_plan_id_selects_specific_plan_without_path_filters(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "first",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "fixes": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                },
                {
                    "id": "second",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                },
            ]
        ),
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "code": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "selected plan",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.run_check", _fake_run_check)

    result = runner.invoke(
        cli,
        [
            "check",
            ".",
            "--plan",
            "plans.json",
            "--plan-id",
            "second",
        ],
    )

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_check_plan_id_without_plan_errors(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["check", ".", "--plan-id", "alpha"])

    assert result.exit_code != 0
    assert "--plan-id requires --plan" in result.output


def test_check_plan_store_requires_plan_id_when_multiple_match(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {"id": "first", "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]},
                    {"id": "second", "fixes": [{"id": "woodpecker.ensure_latitude_is_increasing"}]},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["check", "--plan", "plan.json"])

    assert result.exit_code != 0
    assert "Multiple matching fix plans found" in result.output


def test_check_plan_store_plan_id_selects_specific_plan(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {"id": "first", "fixes": [{"id": "woodpecker.ensure_latitude_is_increasing"}]},
                    {"id": "second", "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]},
                ]
            }
        ),
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "code": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "selected plan",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.run_check", _fake_run_check)

    result = runner.invoke(cli, ["check", "--plan", "plan.json", "--plan-id", "second"])

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_list_plans_text_output(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "alpha",
                    "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                },
                {
                    "id": "beta",
                    "fixes": [
                        {"id": "woodpecker.ensure_latitude_is_increasing"},
                        {"id": "woodpecker.remove_coordinate_fill_value_encodings"},
                    ],
                },
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        ["list-plans", "--plan", "plans.json"],
    )

    assert result.exit_code == 0
    assert "alpha: 1 fixes" in result.output
    assert "beta: 2 fixes" in result.output


def test_list_plans_json_output(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "alpha",
                    "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "list-plans",
            "--plan",
            "plans.json",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload[0]["id"] == "alpha"


def test_list_plans_requires_store_options(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["list-plans"])

    assert result.exit_code != 0
    assert "Missing option '--plan'" in result.output


def test_load_plans_from_plan_document_into_json_store(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    Path("plan-doc.json").write_text(
        json.dumps(
            {
                "plans": [
                    {"id": "alpha", "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]},
                    {"id": "beta", "fixes": [{"id": "woodpecker.ensure_latitude_is_increasing"}]},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "load-plans",
            "--plan",
            "target.json",
            "--from-plan",
            "plan-doc.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["plans"]] == ["alpha", "beta"]


def test_load_plans_from_store_with_plan_id_filter(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    Path("source.json").write_text(
        json.dumps(
            [
                {"id": "alpha", "fixes": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]},
                {"id": "beta", "fixes": [{"id": "woodpecker.ensure_latitude_is_increasing"}]},
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "load-plans",
            "--plan",
            "target.json",
            "--from-plan",
            "source.json",
            "--from-store",
            "json",
            "--plan-id",
            "beta",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["loaded"] == 1
    assert output["plan_ids"] == ["beta"]
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["plans"]] == ["beta"]


def test_load_plans_requires_source_plan_location(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(
        cli,
        [
            "load-plans",
            "--plan",
            "target.json",
        ],
    )

    assert result.exit_code != 0
    assert "Missing option '--from-plan'" in result.output


def test_load_plans_wraps_save_plan_value_error(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, _ = isolated_cli_workspace
    Path("plan-doc.json").write_text(json.dumps({"plans": []}), encoding="utf-8")

    class _Store:
        def save_plan(self, plan):
            _ = plan
            raise ValueError("save failed value")

    monkeypatch.setattr("woodpecker.cli.create_fix_plan_store", lambda *_args, **_kwargs: _Store())
    monkeypatch.setattr(
        "woodpecker.cli.resolve_load_source_plans",
        lambda **_kwargs: [SimpleNamespace(id="alpha")],
    )

    result = runner.invoke(
        cli,
        [
            "load-plans",
            "--plan",
            "target.json",
            "--from-plan",
            "plan-doc.json",
        ],
        standalone_mode=False,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, click.ClickException)
    assert str(result.exception) == "save failed value"


def test_load_plans_reraises_save_plan_click_exception(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, _ = isolated_cli_workspace
    Path("plan-doc.json").write_text(json.dumps({"plans": []}), encoding="utf-8")

    class _SavePlanClickError(click.ClickException):
        pass

    class _Store:
        def save_plan(self, plan):
            _ = plan
            raise _SavePlanClickError("save failed click")

    monkeypatch.setattr("woodpecker.cli.create_fix_plan_store", lambda *_args, **_kwargs: _Store())
    monkeypatch.setattr(
        "woodpecker.cli.resolve_load_source_plans",
        lambda **_kwargs: [SimpleNamespace(id="alpha")],
    )

    result = runner.invoke(
        cli,
        [
            "load-plans",
            "--plan",
            "target.json",
            "--from-plan",
            "plan-doc.json",
        ],
        standalone_mode=False,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, _SavePlanClickError)
    assert str(result.exception) == "save failed click"


def test_format_provenance_source_for_store_mode():
    context = SimpleNamespace(
        source="store",
        selected_plans=[SimpleNamespace(id="alpha"), SimpleNamespace(id="beta")],
    )

    output = format_provenance_source(
        context,
        store_type="json",
        plan_location=Path("plans.json"),
    )

    assert output == "store type=json location=plans.json plans=alpha, beta"


def test_format_provenance_source_for_direct_mode():
    context = SimpleNamespace(source="direct", selected_plans=[])

    output = format_provenance_source(
        context,
        store_type="json",
        plan_location=Path("plans.json"),
    )

    assert output is None
