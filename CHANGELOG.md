# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **The nginx generator emitted a rate unit nginx does not accept, so every generated config was rejected at reload, including the shipped defaults** (#6). `limit_req_zone ... rate=` takes only `r/s` or `r/m`; `_parse_window` passed the configured window through as a unit, producing `rate=60r/1min` from the default `requests_per_minute: 60` with `window: 1m`. Verified against nginx 1.31.5: `invalid rate "rate=60r/1min"`. The window is now folded into the rate, and a rate nginx cannot express is refused rather than emitted.
- **The nginx whitelist blanked the page for whitelisted addresses, and could not load at all.** `if ($whitelist) { set $limit_bypass 1; }` was written at `http` level, where nginx does not allow `if`, and the matching `if ($limit_bypass) { return 200; }` in the server block answered the request with an empty 200 instead of letting it through. Whitelisting now works by mapping the address to an empty zone key, which nginx does not account. Verified at runtime: an address in the whitelist is served all six of six requests against a 2r/m limit, an address outside it gets one 200 and then 503.
- **`burst: 0` produced `burst=0`, which nginx rejects** ("invalid burst value"). The parameter is omitted when the burst is zero, which is also its default.
- **`limit_by_header` was passed through as written, so a normal header name produced a shared bucket.** nginx exposes a header as `$http_` plus the name lowercased with `-` turned into `_`, and reading `$http_X-API-Key` it takes `$http_X` as the variable and `-API-Key` as a literal. That parses, so `nginx -t` is happy, but the zone key becomes a constant and every client is counted together. Verified at runtime: with `X-API-Key: secret` on the request, `$http_X-API-Key` evaluates to `-API-Key`. Header names are now normalised.
- **The generated locations contained `... # Your other configurations here`**, which is not valid nginx, so the output could never be validated as it stood. It is now a comment.

### Added

- **`tests/smoke_nginx.py`**, which generates configuration for nine scenarios and validates each with the real `nginx -t`, plus a `validate` workflow that runs it on every push and pull request and also checks the committed `rate_limit_rules/nginx/nginx_rate_limit.conf`. The defect above survived for over a year because nothing validated the output with the server it targets.
- A comment above each `limit_req_zone` recording the requests and window it was generated from.


### Added
- Comprehensive documentation improvements
- README files for each web server configuration directory (Nginx, Apache, Traefik, HAProxy)
- CONTRIBUTING.md with detailed contribution guidelines
- CHANGELOG.md to track project changes
- Prerequisites section in main README
- Troubleshooting section in main README
- Enhanced Contributing section with detailed steps

### Changed
- Improved installation instructions with clearer step-by-step guidance
- Updated repository clone URL in README to use correct repository name
- Fixed Traefik configuration code block format (changed from `toml` to `yaml`)
- Enhanced Contributing section with more detailed workflow

### Fixed
- Typo in config.yaml: "blackist" corrected to "blacklist"
- Repository URL in installation instructions (was `rate-limit-patterns`, now `limits`)

## [1.0.0] - Initial Release

### Added
- Core rate limiting configuration system
- Support for multiple web servers (Nginx, Apache, Traefik, HAProxy)
- Python scripts for converting configurations:
  - `ratelimit.py` - Main configuration loader and validator
  - `ratelimit2nginx.py` - Nginx configuration generator
  - `ratelimit2apache.py` - Apache ModSecurity configuration generator
  - `ratelimit2traefik.py` - Traefik configuration generator
  - `ratelimit2haproxy.py` - HAProxy configuration generator
- Import scripts for each web server platform
- Centralized `config.yaml` for rate limit definitions
- GitHub Actions workflow for automated daily updates
- Support for:
  - Global rate limiting
  - Path-specific rate limits
  - IP whitelist/blacklist
  - Different limiting strategies (by IP, User-Agent, custom headers)
  - Configurable logging levels
- MIT License
- Basic README with usage instructions

[Unreleased]: https://github.com/fabriziosalmi/limits/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/fabriziosalmi/limits/releases/tag/v1.0.0
