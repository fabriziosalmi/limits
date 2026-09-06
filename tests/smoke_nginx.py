#!/usr/bin/env python3
"""
Validates the nginx generator's output with nginx itself.

`ratelimit2nginx.py` produced configuration that nginx rejects, including with
the shipped defaults, for over a year (issue #6). A test that only checks that
a file was produced would not have caught it, so this one runs the real
`nginx -t` over the generated output.

Usage:
    python3 tests/smoke_nginx.py

Requires the `nginx` binary on PATH. Exits non-zero on the first failure.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ratelimit2nginx  # noqa: E402


# Each case is a full configuration, so a failure names one scenario rather than
# a diff against a base.
CASES = {
    "shipped defaults": {
        "global": {"enabled": True, "requests_per_minute": 60, "burst": 20,
                   "window": "1m", "limit_by": "ip"},
        "paths": {
            "/login": {"enabled": True, "requests_per_minute": 10, "burst": 5,
                       "window": "1m", "limit_by": "ip"},
            "/api": {"enabled": True, "requests_per_minute": 120, "burst": 40,
                     "window": "1m", "limit_by": "ip"},
        },
        "whitelist": {"enabled": False, "ips": []},
        "blacklist": {"enabled": False, "ips": []},
    },
    "whitelist enabled": {
        "global": {"enabled": True, "requests_per_minute": 60, "burst": 20,
                   "window": "1m", "limit_by": "ip"},
        "whitelist": {"enabled": True,
                      "ips": ["192.168.1.10", "192.168.1.11/32", "2001:0db8::/32"]},
        "blacklist": {"enabled": False, "ips": []},
    },
    "blacklist enabled": {
        "global": {"enabled": True, "requests_per_minute": 60, "burst": 20,
                   "window": "1m", "limit_by": "ip"},
        "whitelist": {"enabled": False, "ips": []},
        "blacklist": {"enabled": True, "ips": ["192.168.1.20", "192.168.1.22/32"]},
    },
    "both lists enabled": {
        "global": {"enabled": True, "requests_per_minute": 60, "burst": 20,
                   "window": "1m", "limit_by": "ip"},
        "whitelist": {"enabled": True, "ips": ["10.0.0.1"]},
        "blacklist": {"enabled": True, "ips": ["10.0.0.2"]},
    },
    "sub-minute window": {
        "global": {"enabled": True, "requests_per_minute": 60, "burst": 20,
                   "window": "30s", "limit_by": "ip"},
        "whitelist": {"enabled": False, "ips": []},
        "blacklist": {"enabled": False, "ips": []},
    },
    "multi-hour window": {
        "global": {"enabled": True, "requests_per_minute": 120, "burst": 20,
                   "window": "2h", "limit_by": "ip"},
        "whitelist": {"enabled": False, "ips": []},
        "blacklist": {"enabled": False, "ips": []},
    },
    "zero burst": {
        "global": {"enabled": True, "requests_per_minute": 2, "burst": 0,
                   "window": "1m", "limit_by": "ip"},
        "whitelist": {"enabled": False, "ips": []},
        "blacklist": {"enabled": False, "ips": []},
    },
    "keyed by user agent and by header": {
        "global": {"enabled": True, "requests_per_minute": 60, "burst": 20,
                   "window": "1m", "limit_by": "user_agent"},
        "paths": {
            "/api": {"enabled": True, "requests_per_minute": 30, "burst": 10,
                     "window": "1m", "limit_by": "header_name",
                     "limit_by_header": "x_api_key"},
        },
        "whitelist": {"enabled": True, "ips": ["10.0.0.1"]},
        "blacklist": {"enabled": False, "ips": []},
    },
}

# Rates nginx cannot express. The generator must refuse them rather than emit
# something that fails at deploy time.
REJECTED = {
    "below one request per minute": {"requests": 1, "window": "2h"},
}


def wrap(generated: str) -> str:
    """Wraps the generated snippet in the smallest nginx.conf that will load it."""
    return f"events {{ worker_connections 64; }}\nhttp {{\n{generated}\n}}\n"


def nginx_check(config_text: str, workdir: Path) -> tuple[bool, str]:
    conf = workdir / "nginx.conf"
    conf.write_text(config_text)
    result = subprocess.run(
        ["nginx", "-t", "-c", str(conf), "-p", str(workdir)],
        capture_output=True, text=True,
    )
    return result.returncode == 0, result.stderr.strip()


def main() -> int:
    if shutil.which("nginx") is None:
        print("nginx is not on PATH: cannot validate the generated configuration.")
        return 2

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)

        for name, config in CASES.items():
            validated = ratelimit2nginx._validate_config(config)
            if validated is None:
                print(f"FAIL  {name}: the configuration did not validate")
                failures += 1
                continue

            generated = ratelimit2nginx.generate_nginx_config(validated)
            ok, message = nginx_check(wrap(generated), workdir)
            if ok:
                print(f"ok    {name}")
            else:
                failures += 1
                print(f"FAIL  {name}")
                for line in message.splitlines():
                    print(f"      {line}")
                print("      generated:")
                for line in generated.splitlines():
                    print(f"        {line}")

        for name, case in REJECTED.items():
            try:
                rate = ratelimit2nginx._nginx_rate(case["requests"], case["window"])
            except ValueError:
                print(f"ok    {name} is refused")
            else:
                failures += 1
                print(f"FAIL  {name}: expected a refusal, got rate={rate}")

    print()
    if failures:
        print(f"{failures} failing")
        return 1
    print(f"{len(CASES) + len(REJECTED)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
