# ratelimit2apache.py
import ipaddress
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple

# Constants for repeated strings
GLOBAL_SECTION = 'global'
PATHS_SECTION = 'paths'
WHITELIST_SECTION = 'whitelist'
BLACKLIST_SECTION = 'blacklist'
ADVANCED_SECTION = 'advanced'
IPS_KEY = 'ips'
ENABLED_KEY = 'enabled'
LIMIT_BY_KEY = 'limit_by'
LOG_LEVEL_KEY = 'log_level'
REQUESTS_PER_MINUTE_KEY = 'requests_per_minute'
WINDOW_KEY = 'window'
BURST_KEY = 'burst'

# Valid values for certain fields
VALID_LIMIT_BY_VALUES = {'ip', 'user_agent', 'header_name'}
VALID_LOG_LEVELS = {'debug', 'info', 'warning', 'error'}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(config_path: str = 'config.yaml') -> Optional[Dict[str, Any]]:
    """
    Load rate limit settings from config.yaml.

    Args:
        config_path: Path to the configuration file.

    Returns:
        A dictionary containing the validated configuration, or None if loading fails.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                logger.error("Error: config file is empty")
                return None
            return _validate_config(config)
    except FileNotFoundError:
        logger.error(f"Error: config file not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML: {e}")
        return None

def _validate_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Validates the loaded configuration, setting default values and ensuring
    required keys are present.

    Args:
        config: The raw configuration dictionary loaded from the YAML file.

    Returns:
        A validated configuration dictionary, or None if validation fails.
    """
    if not _validate_global_section(config):
        return None

    if PATHS_SECTION in config and not _validate_paths_section(config[PATHS_SECTION]):
        return None

    if WHITELIST_SECTION in config and not _validate_list_section(config[WHITELIST_SECTION], WHITELIST_SECTION):
        return None

    if BLACKLIST_SECTION in config and not _validate_list_section(config[BLACKLIST_SECTION], BLACKLIST_SECTION):
        return None

    if ADVANCED_SECTION in config and not _validate_advanced_section(config[ADVANCED_SECTION]):
        return None

    return config

def _validate_global_section(config: Dict[str, Any]) -> bool:
    """
    Validates the 'global' section of the configuration.

    Args:
        config: The configuration dictionary.

    Returns:
        True if the global section is valid, False otherwise.
    """
    if GLOBAL_SECTION not in config:
        logger.error("Error: 'global' section is missing in config")
        return False

    global_settings = config[GLOBAL_SECTION]
    global_settings.setdefault(ENABLED_KEY, True)
    global_settings.setdefault(REQUESTS_PER_MINUTE_KEY, 60)
    global_settings.setdefault(BURST_KEY, 20)
    global_settings.setdefault(WINDOW_KEY, '1m')
    global_settings.setdefault(LIMIT_BY_KEY, 'ip')

    if global_settings[LIMIT_BY_KEY] not in VALID_LIMIT_BY_VALUES:
        logger.error(f"Error: Invalid '{LIMIT_BY_KEY}' value in global section")
        return False

    return True

def _validate_paths_section(paths_config: Dict[str, Any]) -> bool:
    """
    Validates the 'paths' section of the configuration.

    Args:
        paths_config: The 'paths' section of the configuration.

    Returns:
        True if the paths section is valid, False otherwise.
    """
    if not isinstance(paths_config, dict):
        logger.error("Error: 'paths' must be a dictionary")
        return False

    for path, settings in paths_config.items():
        settings.setdefault(ENABLED_KEY, True)
        settings.setdefault(REQUESTS_PER_MINUTE_KEY, 60)
        settings.setdefault(BURST_KEY, 20)
        settings.setdefault(WINDOW_KEY, '1m')
        settings.setdefault(LIMIT_BY_KEY, 'ip')

        if settings[LIMIT_BY_KEY] not in VALID_LIMIT_BY_VALUES:
            logger.error(f"Error: Invalid '{LIMIT_BY_KEY}' value for path {path}")
            return False

    return True

def _validate_list_section(list_config: Dict[str, Any], section_name: str) -> bool:
    """
    Validates the 'whitelist' or 'blacklist' section of the configuration.

    Args:
        list_config: The 'whitelist' or 'blacklist' section of the configuration.
        section_name: The name of the section being validated.

    Returns:
        True if the section is valid, False otherwise.
    """
    list_config.setdefault(ENABLED_KEY, False)
    if IPS_KEY in list_config:
        if not isinstance(list_config[IPS_KEY], list):
            logger.error(f"Error: '{IPS_KEY}' in '{section_name}' must be a list")
            return False
    else:
        list_config[IPS_KEY] = []

    return True

def _validate_advanced_section(advanced_config: Dict[str, Any]) -> bool:
    """
    Validates the 'advanced' section of the configuration.

    Args:
        advanced_config: The 'advanced' section of the configuration.

    Returns:
        True if the advanced section is valid, False otherwise.
    """
    advanced_config.setdefault(LOG_LEVEL_KEY, 'info')
    if advanced_config[LOG_LEVEL_KEY] not in VALID_LOG_LEVELS:
        logger.error(f"Error: Invalid '{LOG_LEVEL_KEY}' value in advanced section")
        return False

    return True

# mod_evasive counts requests per client IP, per page and per site, and blocks
# an address that goes over either count. Verified against Apache 2.4 with
# mod_evasive 1.10.1 (Ubuntu 24.04) and 2.4.0 (Debian trixie):
#  * its directives are server or virtual-host only: "DOSPageCount not allowed
#    in <Location> context", so per-path limits cannot be expressed;
#  * 2.4.0 stays disabled unless "DOSEnabled true" is set ("On" is refused),
#    and 1.10.1 does not know DOSEnabled, hence the <IfDirective>;
#  * DOSWhitelist matches wildcards ("10.1.*.*") on both versions, but CIDR
#    only on 2.4.0: 1.10.1 accepts "10.1.0.0/16" and never matches it.
WHITELIST_EXPANSION_LIMIT = 256


def _window_seconds(window: str) -> int:
    """'30s' -> 30, '1m' -> 60, '2h' -> 7200; anything else -> 60."""
    units = {'s': 1, 'm': 60, 'h': 3600}
    try:
        return max(1, int(window[:-1]) * units[window[-1]])
    except (KeyError, ValueError, IndexError):
        return 60


def _evasive_whitelist(entries: List[str]) -> Tuple[List[str], List[str]]:
    """DOSWhitelist values for *entries*, and the entries that cannot be expressed.

    IPv4 networks become octet wildcards, the only form both module versions
    match; a prefix that is not a multiple of 8 is expanded into the wildcard
    networks it covers, up to WHITELIST_EXPANSION_LIMIT of them.
    """
    values: List[str] = []
    skipped: List[str] = []
    for entry in entries:
        try:
            net = ipaddress.ip_network(str(entry).strip(), strict=False)
        except ValueError:
            skipped.append(f"{entry} (not an IP address or network)")
            continue
        if net.version != 4:
            skipped.append(f"{entry} (IPv6: not supported by mod_evasive)")
            continue
        octets = -(-net.prefixlen // 8)  # prefix rounded up to whole octets
        subnets = [net] if net.prefixlen % 8 == 0 else list(net.subnets(new_prefix=octets * 8))
        if len(subnets) > WHITELIST_EXPANSION_LIMIT:
            skipped.append(f"{entry} (would need {len(subnets)} wildcard entries)")
            continue
        for sub in subnets:
            parts = str(sub.network_address).split('.')
            values.append('.'.join(parts[:octets] + ['*'] * (4 - octets)))
    return values, skipped


def generate_apache_config(config: Dict[str, Any]) -> str:
    """
    Generates an Apache configuration for mod_evasive (request rate limiting per
    client IP) and mod_authz_core (blacklist) from the loaded config.

    Settings mod_evasive cannot express (per-path limits, limit_by other than
    ip, burst, IPv6 whitelist entries) are written as comments and logged as
    warnings, rather than emitted as directives that would not do what they say.

    Args:
        config: The validated configuration dictionary.

    Returns:
        A string containing the generated Apache configuration.
    """
    out = [
        "# Generated by ratelimit2apache.py from config.yaml.",
        "# Requires mod_evasive (Debian/Ubuntu: libapache2-mod-evasive; a2enmod evasive).",
        "# Server or <VirtualHost> context only: mod_evasive directives are not valid in .htaccess.",
        "",
    ]

    global_settings = config[GLOBAL_SECTION]
    limits_on = global_settings[ENABLED_KEY]
    if limits_on and global_settings[LIMIT_BY_KEY] != 'ip':
        msg = (f"global limit not generated: mod_evasive counts per client IP only "
               f"(limit_by: {global_settings[LIMIT_BY_KEY]})")
        logger.warning(msg)
        out.append(f"# {msg}")
        limits_on = False

    if limits_on:
        seconds = _window_seconds(global_settings[WINDOW_KEY])
        count = max(1, -(-global_settings[REQUESTS_PER_MINUTE_KEY] * seconds // 60))
        out += [
            f"# {global_settings[REQUESTS_PER_MINUTE_KEY]} requests per minute per client IP, "
            f"counted over {seconds} s; an address over the limit is refused for {seconds} s.",
            f"# burst ({global_settings[BURST_KEY]}) has no mod_evasive equivalent and is not applied.",
            "<IfDirective DOSEnabled>",
            "    DOSEnabled true",
            "</IfDirective>",
            "DOSHashTableSize 3097",
            f"DOSSiteCount {count}",
            f"DOSSiteInterval {seconds}",
            f"DOSPageCount {count}",
            f"DOSPageInterval {seconds}",
            f"DOSBlockingPeriod {seconds}",
        ]

        whitelist = config[WHITELIST_SECTION]
        if whitelist[ENABLED_KEY]:
            values, skipped = _evasive_whitelist(whitelist[IPS_KEY])
            out += [f"DOSWhitelist {value}" for value in values]
            for item in skipped:
                logger.warning("whitelist entry not generated: %s", item)
                out.append(f"# whitelist entry not generated: {item}")

    for path, limits in (config.get(PATHS_SECTION) or {}).items():
        if limits[ENABLED_KEY]:
            msg = (f"path {path} ({limits[REQUESTS_PER_MINUTE_KEY]} requests per minute) not "
                   f"generated: mod_evasive has no per-path limits")
            logger.warning(msg)
            out.append(f"# {msg}")

    blacklist = config[BLACKLIST_SECTION]
    if blacklist[ENABLED_KEY] and blacklist[IPS_KEY]:
        out += [
            "",
            '<Location "/">',
            "    <RequireAll>",
            "        Require all granted",
            f"        Require not ip {' '.join(str(ip) for ip in blacklist[IPS_KEY])}",
            "    </RequireAll>",
            "</Location>",
        ]

    return "\n".join(out) + "\n"


if __name__ == "__main__":
    config = load_config()
    if config:
        apache_config = generate_apache_config(config)
        print(apache_config, end='')
