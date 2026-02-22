"""Client for DelphiUITestExposer HTTP server.

Discovers the Delphi app's test server by scanning listening ports
and checking for the /forms endpoint.
"""

from __future__ import annotations

import logging
import socket
from typing import Any

import psutil
import requests

logger = logging.getLogger(__name__)

# Timeout for HTTP requests to the Delphi bridge (seconds)
REQUEST_TIMEOUT = 3.0

# Timeout for port probe during discovery (seconds)
PROBE_TIMEOUT = 0.5


class DelphiBridge:
    """Client for communicating with a DelphiUITestExposer HTTP server."""

    def __init__(self, host: str = "127.0.0.1", port: int | None = None):
        self.host = host
        self.port = port
        self._base_url: str | None = None
        if port is not None:
            self._base_url = f"http://{host}:{port}"

    @property
    def base_url(self) -> str | None:
        """Return base URL if connected, else None."""
        return self._base_url

    @property
    def connected(self) -> bool:
        """Check if we have a valid connection."""
        return self._base_url is not None

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, process_name: str | None = None) -> bool:
        """Find the Delphi bridge server by probing listening ports.

        If *process_name* is given (e.g. "FineAid.exe"), only ports owned
        by that process are probed.  Otherwise all local listening ports
        are tried.

        Returns True if the bridge was found.
        """
        candidate_ports = self._get_candidate_ports(process_name)
        logger.info(
            f"Discovering Delphi bridge: {len(candidate_ports)} candidate "
            f"ports (process={process_name!r})"
        )

        for port in candidate_ports:
            if self._probe_port(port):
                self.port = port
                self._base_url = f"http://{self.host}:{port}"
                logger.info(f"Delphi bridge found at {self._base_url}")
                return True

        logger.warning("Delphi bridge not found on any candidate port")
        return False

    def _get_candidate_ports(self, process_name: str | None) -> list[int]:
        """Get TCP listening ports, optionally filtered by process name."""
        ports: list[int] = []
        for conn in psutil.net_connections(kind="tcp"):
            if conn.status != "LISTEN":
                continue
            if conn.laddr.ip not in ("0.0.0.0", "127.0.0.1", "::"):
                continue
            if process_name and conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    if process_name.lower() not in proc.name().lower():
                        continue
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            ports.append(conn.laddr.port)
        return sorted(set(ports))

    def _probe_port(self, port: int) -> bool:
        """Check if a port serves the /forms endpoint."""
        # Quick TCP check first
        try:
            with socket.create_connection((self.host, port), timeout=PROBE_TIMEOUT):
                pass
        except OSError:
            return False

        # Try HTTP /forms
        try:
            resp = requests.get(
                f"http://{self.host}:{port}/forms",
                timeout=PROBE_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Validate it looks like the Delphi bridge response
                if isinstance(data, list) and (len(data) == 0 or "handle" in data[0]):
                    return True
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------
    # API methods
    # ------------------------------------------------------------------

    def _get(self, path: str, **params: str) -> Any:
        """Perform a GET request and return parsed JSON.

        On connection failure, automatically re-discovers the bridge
        (the app may have restarted on a different port) and retries once.
        """
        if not self._base_url:
            raise RuntimeError("Not connected. Call discover() or provide a port.")
        try:
            url = f"{self._base_url}{path}"
            resp = requests.get(url, params=params or None, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout) as e:
            old_url = self._base_url
            logger.warning(f"Bridge request failed ({e}), re-discovering...")
            self._base_url = None
            self.port = None
            if self.discover():
                if self._base_url != old_url:
                    logger.info(
                        f"Bridge moved from {old_url} to {self._base_url}"
                    )
                url = f"{self._base_url}{path}"
                resp = requests.get(
                    url, params=params or None, timeout=REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                return resp.json()
            raise

    def get_forms(self) -> list[dict[str, Any]]:
        """GET /forms — list all open forms."""
        return self._get("/forms")

    def get_mainform_controls(self) -> list[dict[str, Any]]:
        """GET /mainform/controls — control tree for the main form."""
        return self._get("/mainform/controls")

    def get_activeform_controls(self) -> list[dict[str, Any]]:
        """GET /activeform/controls — control tree for the active form."""
        return self._get("/activeform/controls")

    def get_form_controls(self, handle: int) -> list[dict[str, Any]]:
        """GET /forms/{handle}/controls — control tree for a specific form."""
        return self._get(f"/forms/{handle}/controls")

    def get_controls(
        self,
        class_name: str | None = None,
        name: str | None = None,
        caption: str | None = None,
    ) -> list[dict[str, Any]]:
        """GET /controls — flat list of all controls with optional filters."""
        params: dict[str, str] = {}
        if class_name is not None:
            params["class"] = class_name
        if name is not None:
            params["name"] = name
        if caption is not None:
            params["caption"] = caption
        return self._get("/controls", **params)

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    def find_control_by_caption(self, caption: str) -> dict[str, Any] | None:
        """Find first control matching caption (case-insensitive)."""
        results = self.get_controls(caption=caption)
        if results:
            return results[0]
        return None

    def find_controls_by_class(self, class_name: str) -> list[dict[str, Any]]:
        """Find all controls of a specific VCL class."""
        return self.get_controls(class_name=class_name)
