from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import typer

from .client import HubApiError, HubClient

app = typer.Typer(help="Thingino Hub API v2 command-line client")
cameras_app = typer.Typer(help="Camera-related commands")
app.add_typer(cameras_app, name="cameras")


@dataclass
class CliContext:
    client: HubClient
    json_output: bool


def _print_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


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
    try:
        payload = state.client.health()
    except HubApiError as error:
        typer.echo(f"health failed: {error}", err=True)
        raise typer.Exit(code=1) from error

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
    try:
        payload = state.client.cameras(limit=limit)
    except HubApiError as error:
        typer.echo(f"camera list failed: {error}", err=True)
        raise typer.Exit(code=1) from error

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
    try:
        payload = state.client.attention(
            minimum_severity=minimum_severity,
            limit=limit,
            include_ready=include_ready,
        )
    except HubApiError as error:
        typer.echo(f"camera attention failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    if state.json_output:
        _print_json(payload)
        return
    _print_attention(payload)
