"""Wait until the local OrangeHRM instance is ready for tests.

Polls the login page until it returns HTTP 200 and renders the login form.
Fails fast if OrangeHRM redirects to its setup wizard, which means the seed
database or Conf.php was not loaded.

Usage:
    python infra/wait_for_ready.py [--url URL] [--timeout SECONDS] [--interval SECONDS]

The URL defaults to $TEST_ORANGEHRM_URL, then http://localhost:8081.
Exit codes: 0 ready, 1 timed out, 2 not installed (setup wizard shown).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_URL = "http://localhost:8081"
LOGIN_PATH = "/web/index.php/auth/login"
LOGIN_MARKER = "<auth-login"


class NotInstalledError(Exception):
    """OrangeHRM is running but shows the setup wizard."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def redirects_to_installer(base_url: str, request_timeout: float) -> bool:
    """An uninstalled OrangeHRM answers 500 on app pages but redirects `/` to the installer."""
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(base_url.rstrip("/") + "/", timeout=request_timeout).close()
    except urllib.error.HTTPError as exc:
        return "installer" in (exc.headers.get("Location") or "")
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        pass
    return False


def check_once(base_url: str, request_timeout: float) -> str | None:
    """Return None when ready, otherwise a short reason it is not ready yet."""
    url = base_url.rstrip("/") + LOGIN_PATH
    try:
        with urllib.request.urlopen(url, timeout=request_timeout) as resp:
            final_url = resp.geturl()
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if not redirects_to_installer(base_url, request_timeout):
            return f"HTTP {exc.code}"
        final_url, body = "installer", ""
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return f"not reachable ({reason})"

    if "installer" in final_url:
        raise NotInstalledError(
            f"{base_url} redirects to the setup wizard. The seed was not loaded: run "
            "`docker compose -f infra/docker-compose.orangehrm.yml down -v` and start it again."
        )
    if LOGIN_MARKER not in body:
        return "login page has not rendered yet"
    return None


def wait_for_ready(base_url: str, timeout: float, interval: float) -> bool:
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        attempt += 1
        reason = check_once(base_url, request_timeout=min(10.0, interval * 2))
        if reason is None:
            print(f"OrangeHRM is ready at {base_url} (attempt {attempt})")
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print(f"Timed out after {timeout:.0f}s waiting for {base_url}: {reason}", file=sys.stderr)
            return False
        print(f"Waiting for OrangeHRM ({reason}); {remaining:.0f}s left")
        time.sleep(min(interval, remaining))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=os.environ.get("TEST_ORANGEHRM_URL", DEFAULT_URL))
    parser.add_argument("--timeout", type=float, default=180.0, help="seconds to wait (default 180)")
    parser.add_argument("--interval", type=float, default=3.0, help="seconds between checks (default 3)")
    args = parser.parse_args(argv)

    try:
        return 0 if wait_for_ready(args.url, args.timeout, args.interval) else 1
    except NotInstalledError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
