from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = (
    "MiamiNetworkFeedBot/1.0 (+https://github.com/MLavenant/miami-network-feed; "
    "personal research feed; respectful; contact via GitHub issues)"
)
DEFAULT_TIMEOUT = 25
MIN_GAP_SECONDS = 1.25


@dataclass
class FetchResult:
    ok: bool
    url: str
    status_code: int | None
    text: str
    content: bytes
    headers: dict[str, str]
    error: str | None = None
    skipped_robots: bool = False


class HttpClient:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml,application/rss+xml,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self._last_host_hit: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}

    def _host(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    def _throttle(self, url: str) -> None:
        host = self._host(url)
        last = self._last_host_hit.get(host, 0.0)
        wait = MIN_GAP_SECONDS - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        self._last_host_hit[host] = time.monotonic()

    def allowed_by_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            rp = RobotFileParser()
            robots_url = f"{origin}/robots.txt"
            try:
                self._throttle(robots_url)
                resp = self.session.get(robots_url, timeout=12)
                if resp.status_code >= 400:
                    self._robots[origin] = None
                else:
                    rp.parse(resp.text.splitlines())
                    self._robots[origin] = rp
            except Exception:
                self._robots[origin] = None
        rp = self._robots[origin]
        if rp is None:
            return True
        try:
            return rp.can_fetch(USER_AGENT, url)
        except Exception:
            return True

    def get(
        self,
        url: str,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
        respect_robots: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ) -> FetchResult:
        if respect_robots and not self.allowed_by_robots(url):
            return FetchResult(
                ok=False,
                url=url,
                status_code=None,
                text="",
                content=b"",
                headers={},
                error="blocked by robots.txt",
                skipped_robots=True,
            )
        req_headers: dict[str, str] = {}
        if etag:
            req_headers["If-None-Match"] = etag
        if last_modified:
            req_headers["If-Modified-Since"] = last_modified
        if headers:
            req_headers.update(headers)
        try:
            self._throttle(url)
            resp = self.session.get(url, timeout=timeout, headers=req_headers, allow_redirects=True)
            text = resp.text if resp.content else ""
            return FetchResult(
                ok=resp.status_code < 400 or resp.status_code == 304,
                url=str(resp.url),
                status_code=resp.status_code,
                text=text,
                content=resp.content or b"",
                headers={k: v for k, v in resp.headers.items()},
                error=None if resp.status_code < 400 or resp.status_code == 304 else f"HTTP {resp.status_code}",
            )
        except Exception as exc:
            return FetchResult(
                ok=False,
                url=url,
                status_code=None,
                text="",
                content=b"",
                headers={},
                error=str(exc),
            )


def stable_hash(*parts: Any) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(str(p or "").encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()
