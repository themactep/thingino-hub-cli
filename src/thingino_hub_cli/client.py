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
