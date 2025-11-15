# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
