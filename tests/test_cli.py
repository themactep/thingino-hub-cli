from __future__ import annotations

from typing import Any

from typer.testing import CliRunner

from thingino_hub_cli.cli import app

runner = CliRunner()


class DummyClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "hub": {
                "mqtt_connected": True,
                "mqtt_host": "192.168.88.25",
                "api_ready": 1,
                "api_known": 2,
            },
        }

    def cameras(self, *, limit: int = 0) -> dict[str, Any]:
        return {
            "ok": True,
            "count": 1,
            "cameras": [
                {
                    "camera_id": "cam1",
                    "name": "Front Door",
                    "status": "online",
                    "api_status": "online",
                    "ip": "192.168.1.10",
                }
            ],
        }

    def attention(self, *, minimum_severity: str, limit: int, include_ready: bool) -> dict[str, Any]:
        return {
            "ok": True,
            "count": 1,
            "cameras": [
                {
                    "camera_id": "cam2",
                    "name": "Garage",
                    "score": 3,
                    "issues": [
                        {
                            "severity": minimum_severity,
                            "code": "native-api-problem",
                            "message": "Native API status is offline.",
                            "suggested_action": "Refresh API details.",
                        }
                    ],
                }
            ],
        }

    def refresh_api(self, camera_id: str) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "refresh-api", "result": "scheduled", "message": "Queued"}

    def refresh_onvif(self, camera_id: str) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "refresh-onvif", "result": "scheduled", "message": "Queued"}

    def refresh_snapshot(self, camera_id: str) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "refresh-snapshot", "result": "scheduled", "message": "Queued"}

    def rescan(self, camera_id: str) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "rescan", "result": "accepted", "message": "Requested"}

    def set_privacy(self, camera_id: str, *, enabled: bool, channel: str = "all") -> dict[str, Any]:
        mode = "enabled" if enabled else "disabled"
        return {"ok": True, "camera_id": camera_id, "action": "privacy", "result": "accepted", "message": f"Privacy {mode}"}

    def set_daynight(self, camera_id: str, *, mode: str) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "daynight", "result": "accepted", "message": f"Mode {mode}"}

    def record(self, camera_id: str, *, duration_seconds: int = 10, stream_id: int = 0, path: str = "") -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "record", "result": "accepted", "message": "Recording requested"}

    def enroll(
        self,
        *,
        ip: str,
        camera_id: str = "",
        api_token: str = "",
        onvif_username: str = "",
        onvif_password: str = "",
    ) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id or "cam3", "action": "enroll", "result": "success", "message": "Connected"}

    def connect(self, camera_id: str, *, onvif_username: str = "", onvif_password: str = "") -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "connect", "result": "success", "message": "Connected"}

    def pair(self, camera_id: str) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "pair", "result": "success", "message": "Paired"}

    def delete(self, camera_id: str) -> dict[str, Any]:
        return {"ok": True, "camera_id": camera_id, "action": "delete", "result": "success", "message": "Deleted"}

    def bulk_action(self, *, action: str, camera_ids: list[str]) -> dict[str, Any]:
        return {
            "ok": True,
            "action": action,
            "message": "Bulk done",
            "result": {
                "action": action,
                "total": len(camera_ids),
                "success_count": len(camera_ids),
                "error_count": 0,
            },
        }


class FailingClient(DummyClient):
    def health(self) -> dict[str, Any]:
        raise RuntimeError("boom")


def test_health_text_output(monkeypatch: Any) -> None:
    monkeypatch.setattr("thingino_hub_cli.cli.HubClient", DummyClient)
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    assert "mqtt_connected: True" in result.stdout
    assert "api_ready: 1/2" in result.stdout


def test_cameras_list_json_output(monkeypatch: Any) -> None:
    monkeypatch.setattr("thingino_hub_cli.cli.HubClient", DummyClient)
    result = runner.invoke(app, ["--json", "cameras", "list"])
    assert result.exit_code == 0
    assert '"camera_id": "cam1"' in result.stdout
    assert '"name": "Front Door"' in result.stdout


def test_attention_command(monkeypatch: Any) -> None:
    monkeypatch.setattr("thingino_hub_cli.cli.HubClient", DummyClient)
    result = runner.invoke(app, ["cameras", "attention", "--minimum-severity", "critical"])
    assert result.exit_code == 0
    assert "cam2" in result.stdout
    assert "[critical] native-api-problem" in result.stdout


def test_actions_commands(monkeypatch: Any) -> None:
    monkeypatch.setattr("thingino_hub_cli.cli.HubClient", DummyClient)
    assert runner.invoke(app, ["actions", "refresh-api", "cam1"]).exit_code == 0
    assert runner.invoke(app, ["actions", "refresh-onvif", "cam1"]).exit_code == 0
    assert runner.invoke(app, ["actions", "refresh-snapshot", "cam1"]).exit_code == 0
    assert runner.invoke(app, ["actions", "rescan", "cam1"]).exit_code == 0
    assert runner.invoke(app, ["actions", "privacy", "cam1", "--disabled"]).exit_code == 0
    assert runner.invoke(app, ["actions", "daynight", "cam1", "--mode", "night"]).exit_code == 0
    assert runner.invoke(app, ["actions", "record", "cam1", "--duration-seconds", "8"]).exit_code == 0


def test_lifecycle_commands(monkeypatch: Any) -> None:
    monkeypatch.setattr("thingino_hub_cli.cli.HubClient", DummyClient)
    assert runner.invoke(app, ["lifecycle", "enroll", "--ip", "192.168.1.50"]).exit_code == 0
    assert runner.invoke(app, ["lifecycle", "connect", "cam1"]).exit_code == 0
    assert runner.invoke(app, ["lifecycle", "pair", "cam1"]).exit_code == 0
    assert runner.invoke(app, ["lifecycle", "delete", "cam1", "--yes"]).exit_code == 0


def test_delete_requires_confirmation(monkeypatch: Any) -> None:
    monkeypatch.setattr("thingino_hub_cli.cli.HubClient", DummyClient)
    result = runner.invoke(app, ["lifecycle", "delete", "cam1"])
    assert result.exit_code == 1
    assert "Refusing to delete without --yes" in result.stderr


def test_bulk_command(monkeypatch: Any) -> None:
    monkeypatch.setattr("thingino_hub_cli.cli.HubClient", DummyClient)
    result = runner.invoke(
        app,
        ["bulk", "run", "--action", "refresh-api", "--camera-id", "cam1", "--camera-id", "cam2"],
    )
    assert result.exit_code == 0
    assert "2/2 successful" in result.stdout
