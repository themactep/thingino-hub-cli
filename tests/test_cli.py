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
