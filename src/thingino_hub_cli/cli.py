from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable

import typer

from .client import HubApiError, HubClient

app = typer.Typer(help="Thingino Hub API v2 command-line client")
cameras_app = typer.Typer(help="Camera read commands")
actions_app = typer.Typer(help="Camera action commands")
lifecycle_app = typer.Typer(help="Camera lifecycle commands")
bulk_app = typer.Typer(help="Bulk action commands")
app.add_typer(cameras_app, name="cameras")
app.add_typer(actions_app, name="actions")
app.add_typer(lifecycle_app, name="lifecycle")
app.add_typer(bulk_app, name="bulk")


@dataclass
class CliContext:
    client: HubClient
    json_output: bool


def _print_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def _run_api_call(ctx: CliContext, label: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except HubApiError as error:
        typer.echo(f"{label} failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"{label} failed: {error}", err=True)
        raise typer.Exit(code=1) from error


def _print_cameras(payload: dict[str, Any]) -> None:
    cameras = payload.get("cameras") or []
    if not isinstance(cameras, list) or not cameras:
        typer.echo("No cameras returned.")
        return

    typer.echo("CAMERA ID                             STATUS   API      IP               NAME")
    for entry in cameras:
        if not isinstance(entry, dict):
            continue
        camera_id = str(entry.get("camera_id") or "")[:36]
        status = str(entry.get("status") or "unknown")[:8]
        api_status = str(entry.get("api_status") or "unknown")[:8]
        ip = str(entry.get("ip") or "-")[:15]
        name = str(entry.get("name") or "")
        typer.echo(f"{camera_id:<36} {status:<8} {api_status:<8} {ip:<15} {name}")


def _print_attention(payload: dict[str, Any]) -> None:
    cameras = payload.get("cameras") or []
    if not isinstance(cameras, list) or not cameras:
        typer.echo("No cameras requiring attention for current filters.")
        return
    for entry in cameras:
        if not isinstance(entry, dict):
            continue
        typer.echo(f"- {entry.get('camera_id')} ({entry.get('name')}), score={entry.get('score')}")
        for issue in entry.get("issues") or []:
            if not isinstance(issue, dict):
                continue
            typer.echo(
                f"  [{issue.get('severity')}] {issue.get('code')}: "
                f"{issue.get('message')} -> {issue.get('suggested_action')}"
            )


def _print_action_result(payload: dict[str, Any]) -> None:
    if "camera_id" in payload and "action" in payload:
        typer.echo(f"{payload.get('action')} {payload.get('camera_id')}: {payload.get('result')}")
        typer.echo(str(payload.get("message") or ""))
        return
    if "action" in payload and "result" in payload:
        result = payload.get("result")
        if isinstance(result, dict):
            typer.echo(
                f"{payload.get('action')}: "
                f"{result.get('success_count', 0)}/{result.get('total', 0)} successful"
            )
            typer.echo(str(payload.get("message") or ""))
            return
    typer.echo(str(payload.get("message") or "ok"))


@app.callback()
def main(
    ctx: typer.Context,
    base_url: str = typer.Option(
        default_factory=lambda: os.environ.get("THINGINO_HUB_BASE_URL", "http://127.0.0.1:8090"),
        help="Thingino Hub base URL (without /api/v2).",
    ),
    timeout: float = typer.Option(
        default_factory=lambda: float(os.environ.get("THINGINO_HUB_TIMEOUT", "10")),
        help="HTTP timeout in seconds.",
    ),
    insecure: bool = typer.Option(False, "--insecure", help="Disable TLS certificate verification."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    ctx.obj = CliContext(
        client=HubClient(base_url=base_url, timeout=timeout, verify_tls=not insecure),
        json_output=json_output,
    )


@app.command("health")
def health(ctx: typer.Context) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "health", state.client.health)
    if state.json_output:
        _print_json(payload)
        return
    hub = payload.get("hub") or {}
    typer.echo(f"ok: {payload.get('ok')}")
    typer.echo(f"mqtt_connected: {hub.get('mqtt_connected')}")
    typer.echo(f"mqtt_host: {hub.get('mqtt_host')}")
    typer.echo(f"api_ready: {hub.get('api_ready')}/{hub.get('api_known')}")


@cameras_app.command("list")
def cameras_list(
    ctx: typer.Context,
    limit: int = typer.Option(0, min=0, help="Max number of cameras to return (0 = default/all)."),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "camera list", lambda: state.client.cameras(limit=limit))
    if state.json_output:
        _print_json(payload)
        return
    _print_cameras(payload)


@cameras_app.command("attention")
def cameras_attention(
    ctx: typer.Context,
    minimum_severity: str = typer.Option("high", help="low|medium|high|critical"),
    limit: int = typer.Option(20, min=1, max=500, help="Max results."),
    include_ready: bool = typer.Option(False, help="Include cameras without actionable issues."),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(
        state,
        "camera attention",
        lambda: state.client.attention(
            minimum_severity=minimum_severity,
            limit=limit,
            include_ready=include_ready,
        ),
    )
    if state.json_output:
        _print_json(payload)
        return
    _print_attention(payload)


@actions_app.command("refresh-api")
def refresh_api(ctx: typer.Context, camera_id: str) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "refresh-api", lambda: state.client.refresh_api(camera_id))
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@actions_app.command("refresh-onvif")
def refresh_onvif(ctx: typer.Context, camera_id: str) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "refresh-onvif", lambda: state.client.refresh_onvif(camera_id))
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@actions_app.command("refresh-snapshot")
def refresh_snapshot(ctx: typer.Context, camera_id: str) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "refresh-snapshot", lambda: state.client.refresh_snapshot(camera_id))
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@actions_app.command("rescan")
def rescan(ctx: typer.Context, camera_id: str) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "rescan", lambda: state.client.rescan(camera_id))
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@actions_app.command("privacy")
def privacy(
    ctx: typer.Context,
    camera_id: str,
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="Enable or disable privacy."),
    channel: str = typer.Option("all", help="Channel selector, defaults to all."),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(
        state,
        "privacy",
        lambda: state.client.set_privacy(camera_id, enabled=enabled, channel=channel),
    )
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@actions_app.command("daynight")
def daynight(
    ctx: typer.Context,
    camera_id: str,
    mode: str = typer.Option(..., help="auto|day|night"),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "daynight", lambda: state.client.set_daynight(camera_id, mode=mode))
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@actions_app.command("record")
def record(
    ctx: typer.Context,
    camera_id: str,
    duration_seconds: int = typer.Option(10, min=1),
    stream_id: int = typer.Option(0, min=0),
    path: str = typer.Option("", help="Output path on hub side if supported."),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(
        state,
        "record",
        lambda: state.client.record(
            camera_id,
            duration_seconds=duration_seconds,
            stream_id=stream_id,
            path=path,
        ),
    )
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@lifecycle_app.command("enroll")
def enroll(
    ctx: typer.Context,
    ip: str = typer.Option(..., help="Camera IP address."),
    camera_id: str = typer.Option("", help="Optional camera id."),
    api_token: str = typer.Option("", help="Optional API token."),
    onvif_username: str = typer.Option("", help="ONVIF username."),
    onvif_password: str = typer.Option("", help="ONVIF password."),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(
        state,
        "enroll",
        lambda: state.client.enroll(
            ip=ip,
            camera_id=camera_id,
            api_token=api_token,
            onvif_username=onvif_username,
            onvif_password=onvif_password,
        ),
    )
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@lifecycle_app.command("connect")
def connect(
    ctx: typer.Context,
    camera_id: str,
    onvif_username: str = typer.Option("", help="ONVIF username."),
    onvif_password: str = typer.Option("", help="ONVIF password."),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(
        state,
        "connect",
        lambda: state.client.connect(
            camera_id,
            onvif_username=onvif_username,
            onvif_password=onvif_password,
        ),
    )
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@lifecycle_app.command("pair")
def pair(ctx: typer.Context, camera_id: str) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(state, "pair", lambda: state.client.pair(camera_id))
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@lifecycle_app.command("delete")
def delete(
    ctx: typer.Context,
    camera_id: str,
    yes: bool = typer.Option(False, "--yes", help="Confirm delete action."),
) -> None:
    state: CliContext = ctx.obj
    if not yes:
        typer.echo("Refusing to delete without --yes", err=True)
        raise typer.Exit(code=1)
    payload = _run_api_call(state, "delete", lambda: state.client.delete(camera_id))
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)


@bulk_app.command("run")
def bulk_run(
    ctx: typer.Context,
    action: str = typer.Option(..., help="Bulk action name, e.g. refresh-api."),
    camera_ids: list[str] = typer.Option(..., "--camera-id", help="Repeat for each target camera."),
) -> None:
    state: CliContext = ctx.obj
    payload = _run_api_call(
        state,
        "bulk action",
        lambda: state.client.bulk_action(action=action, camera_ids=camera_ids),
    )
    if state.json_output:
        _print_json(payload)
        return
    _print_action_result(payload)
