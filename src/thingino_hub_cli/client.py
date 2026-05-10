from __future__ import annotations

from typing import Any

import httpx


class HubApiError(RuntimeError):
    pass


class HubClient:
    def __init__(self, *, base_url: str, timeout: float = 10.0, verify_tls: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_tls = verify_tls

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout, verify=self.verify_tls) as client:
                response = client.request(method, url, **kwargs)
        except httpx.HTTPError as error:
            raise HubApiError(str(error)) from error

        if response.status_code >= 400:
            detail = response.text
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    detail = str(payload.get("detail") or payload.get("message") or detail)
            except ValueError:
                pass
            raise HubApiError(f"{response.status_code}: {detail}")

        try:
            payload = response.json()
        except ValueError as error:
            raise HubApiError("Invalid JSON response from hub") from error
        if not isinstance(payload, dict):
            raise HubApiError("Unexpected response shape from hub")
        return payload

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/v2/health")

    def cameras(self, *, limit: int = 0) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if limit > 0:
            params["limit"] = limit
        return self._request("GET", "/api/v2/cameras", params=params)

    def attention(
        self,
        *,
        minimum_severity: str = "high",
        limit: int = 20,
        include_ready: bool = False,
    ) -> dict[str, Any]:
        params = {
            "minimum_severity": minimum_severity,
            "limit": limit,
            "include_ready": str(include_ready).lower(),
        }
        return self._request("GET", "/api/v2/cameras/attention", params=params)

    def refresh_api(self, camera_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v2/cameras/{camera_id}/refresh/api")

    def refresh_onvif(self, camera_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v2/cameras/{camera_id}/refresh/onvif")

    def refresh_snapshot(self, camera_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v2/cameras/{camera_id}/refresh/snapshot")

    def rescan(self, camera_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v2/cameras/{camera_id}/rescan")

    def set_privacy(self, camera_id: str, *, enabled: bool, channel: str = "all") -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v2/cameras/{camera_id}/privacy",
            json={"enabled": enabled, "channel": channel},
        )

    def set_daynight(self, camera_id: str, *, mode: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v2/cameras/{camera_id}/daynight",
            json={"mode": mode},
        )

    def record(
        self,
        camera_id: str,
        *,
        duration_seconds: int = 10,
        stream_id: int = 0,
        path: str = "",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v2/cameras/{camera_id}/record",
            json={
                "duration_seconds": duration_seconds,
                "stream_id": stream_id,
                "path": path,
            },
        )

    def enroll(
        self,
        *,
        ip: str,
        camera_id: str = "",
        api_token: str = "",
        onvif_username: str = "",
        onvif_password: str = "",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v2/enroll",
            json={
                "camera_id": camera_id,
                "ip": ip,
                "api_token": api_token,
                "onvif_username": onvif_username,
                "onvif_password": onvif_password,
            },
        )

    def connect(
        self,
        camera_id: str,
        *,
        onvif_username: str = "",
        onvif_password: str = "",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v2/cameras/{camera_id}/connect",
            json={
                "onvif_username": onvif_username,
                "onvif_password": onvif_password,
            },
        )

    def pair(self, camera_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v2/cameras/{camera_id}/pair")

    def delete(self, camera_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v2/cameras/{camera_id}/delete")

    def bulk_action(self, *, action: str, camera_ids: list[str]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v2/bulk-action",
            json={
                "action": action,
                "camera_ids": camera_ids,
            },
        )
