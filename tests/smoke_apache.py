#!/usr/bin/env python3
"""
Validates the Apache generator's output with Apache itself.

`ratelimit2apache.py` emitted a `RateLimit` directive that no Apache module
provides, inside `<IfModule mod_ratelimit.c>`, which hid the error whenever the
module was absent (issue #8). It now generates mod_evasive configuration; this
test runs the real `apache2ctl -t` over it with mod_evasive loaded, and checks
the text for defects a syntax check cannot see.

Usage:
    python3 tests/smoke_apache.py

Requires `apache2ctl` with mod_evasive enabled (Debian/Ubuntu:
`apt-get install apache2 libapache2-mod-evasive && a2enmod evasive`), and
permission to read the Apache configuration. Exits non-zero on any failure.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ratelimit2apache  # noqa: E402

GLOBAL = {"enabled": True, "requests_per_minute": 60, "burst": 20, "window": "1m", "limit_by": "ip"}
OFF = {"enabled": False, "ips": []}

CASES = {
    "shipped defaults": {
        "global": GLOBAL,
        "paths": {"/login": {"enabled": True, "requests_per_minute": 10, "burst": 5,
                             "window": "1m", "limit_by": "ip"}},
        "whitelist": OFF, "blacklist": OFF,
    },
    "whitelist enabled": {
        "global": GLOBAL,
        "whitelist": {"enabled": True,
                      "ips": ["192.168.1.10", "192.168.1.11/32", "10.16.0.0/12", "2001:0db8::/32"]},
        "blacklist": OFF,
    },
    "blacklist enabled": {
        "global": GLOBAL, "whitelist": OFF,
        "blacklist": {"enabled": True, "ips": ["192.168.1.20", "192.168.1.22/32", "2001:db8::1"]},
    },
    "both lists enabled": {
        "global": GLOBAL,
        "whitelist": {"enabled": True, "ips": ["10.0.0.1"]},
        "blacklist": {"enabled": True, "ips": ["10.0.0.2"]},
    },
    "sub-minute window": {
        "global": dict(GLOBAL, window="30s"), "whitelist": OFF, "blacklist": OFF,
    },
    "keyed by user agent": {
        "global": dict(GLOBAL, limit_by="user_agent"), "whitelist": OFF, "blacklist": OFF,
    },
}

# (config, expected substrings, forbidden substrings)
CONTENT_CHECKS = {
    "no RateLimit directive and no IfModule that hides a missing module": (
        CASES["shipped defaults"], ["DOSSiteCount 60", "DOSSiteInterval 60"], ["RateLimit", "<IfModule"]),
    "mod_evasive 2.x is switched on, 1.x is not given an unknown directive": (
        CASES["shipped defaults"], ["<IfDirective DOSEnabled>", "DOSEnabled true"], ["DOSEnabled On"]),
    "a per-path limit is reported, not faked inside <Location>": (
        CASES["shipped defaults"], ["# path /login"], ["<Location \"/login\">"]),
    "whitelist CIDR becomes wildcards both module versions match": (
        CASES["whitelist enabled"],
        ["DOSWhitelist 192.168.1.10", "DOSWhitelist 192.168.1.11", "DOSWhitelist 10.16.*.*",
         "DOSWhitelist 10.31.*.*", "# whitelist entry not generated: 2001:0db8::/32"],
        ["DOSWhitelist 192.168.1.11/32", "DOSWhitelist 10.16.0.0/12", "DOSWhitelist 2001"]),
    "a whitelisted address is never denied": (
        CASES["both lists enabled"], ["DOSWhitelist 10.0.0.1", "Require not ip 10.0.0.2"],
        ["Require not ip 10.0.0.1"]),
    "the blacklist grants everyone else": (
        CASES["blacklist enabled"],
        ["Require all granted", "Require not ip 192.168.1.20 192.168.1.22/32 2001:db8::1"], []),
    "30 s window scales the count": (
        CASES["sub-minute window"], ["DOSSiteCount 30", "DOSSiteInterval 30"], []),
    "a limit not keyed by IP is reported, not generated": (
        CASES["keyed by user agent"], ["# global limit not generated"], ["DOSSiteCount"]),
}


def apache_check(generated: str, workdir: Path) -> tuple[bool, str]:
    conf = workdir / "generated.conf"
    conf.write_text(generated)
    # -c runs after the main configuration, so the module is already loaded.
    result = subprocess.run(["apache2ctl", "-t", "-c", f"Include {conf}"],
                            capture_output=True, text=True)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def main() -> int:
    if shutil.which("apache2ctl") is None:
        print("apache2ctl is not on PATH: cannot validate the generated configuration.")
        return 2

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for name, config in CASES.items():
            validated = ratelimit2apache._validate_config(config)
            if validated is None:
                print(f"FAIL  {name}: the configuration did not validate")
                failures += 1
                continue
            generated = ratelimit2apache.generate_apache_config(validated)
            ok, message = apache_check(generated, workdir)
            if ok:
                print(f"ok    {name}")
            else:
                failures += 1
                print(f"FAIL  {name}")
                for line in message.splitlines():
                    print(f"      {line}")

        for name, (config, expected, forbidden) in CONTENT_CHECKS.items():
            generated = ratelimit2apache.generate_apache_config(ratelimit2apache._validate_config(config))
            problems = [f"expected {t!r}" for t in expected if t not in generated]
            problems += [f"found {t!r}" for t in forbidden if t in generated]
            if problems:
                failures += 1
                print(f"FAIL  {name}: " + ", ".join(problems))
            else:
                print(f"ok    {name}")

    print(f"{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
