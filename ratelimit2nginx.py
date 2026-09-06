# ratelimit2nginx.py
import yaml
import logging
import re
from typing import Dict, Any, List, Optional

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

def _limit_req(zone_name: str, burst: int) -> str:
    """
    Builds a `limit_req` directive.

    nginx rejects `burst=0` ("invalid burst value"), and a burst of zero is the
    directive's own default, so the parameter is omitted instead. `nodelay` only
    affects how a burst is served, so it goes with it.

    Args:
        zone_name: The zone to apply.
        burst: The configured burst size.

    Returns:
        The directive text, without indentation.
    """
    if burst and int(burst) > 0:
        return f'limit_req zone={zone_name} burst={int(burst)} nodelay;'
    return f'limit_req zone={zone_name};'


def _zone_key(settings: Dict[str, Any]) -> str:
    """
    Returns the nginx variable a zone is keyed on, from the `limit_by` setting.

    Args:
        settings: A global or per-path settings dictionary.

    Returns:
        An nginx variable, for example '$binary_remote_addr'.
    """
    limit_by = settings[LIMIT_BY_KEY]
    if limit_by == 'user_agent':
        return '$http_user_agent'
    if limit_by == 'header_name':
        header_name = settings.get('limit_by_header', 'custom_header')
        return f'$http_{header_name}'
    return '$binary_remote_addr'


def _whitelist_map_name(key_var: str) -> str:
    """
    Names the mapped variable that carries the whitelist exemption for a key.

    Args:
        key_var: The nginx variable the zone is keyed on.

    Returns:
        The name of the mapped variable, for example '$rl_key_binary_remote_addr'.
    """
    return f'$rl_key_{key_var.lstrip("$")}'


def generate_nginx_config(config: Dict[str, Any]) -> str:
    """
    Generates Nginx rate limiting configuration from the loaded config.

    Args:
        config: The validated configuration dictionary.

    Returns:
        A string containing the generated Nginx configuration.
    """
    nginx_config = []
    global_settings = config[GLOBAL_SECTION]
    whitelisted = config[WHITELIST_SECTION][ENABLED_KEY]

    # Every key variable the zones below will use, so the whitelist maps can be
    # declared before their first use.
    key_vars = []
    if global_settings[ENABLED_KEY]:
        key_vars.append(_zone_key(global_settings))
    for limits in config.get(PATHS_SECTION, {}).values():
        if limits[ENABLED_KEY]:
            key_vars.append(_zone_key(limits))
    key_vars = list(dict.fromkeys(key_vars))

    # Whitelist Configuration
    #
    # A whitelisted address is exempted by giving its request an *empty* zone
    # key: nginx does not account requests whose key evaluates to an empty
    # string, so the limit simply does not apply to them. The previous approach,
    # `if ($whitelist) { set $limit_bypass 1; }` at http level followed by
    # `if ($limit_bypass) { return 200; }` in the server block, could not work:
    # nginx does not allow `if` at http level, and `return 200` answers the
    # request with an empty body instead of letting it through.
    if whitelisted:
        nginx_config.append('geo $rl_whitelist {')
        nginx_config.append('  default 0;')
        for ip in config[WHITELIST_SECTION][IPS_KEY]:
            nginx_config.append(f'  {ip} 1;')
        nginx_config.append('}')

        for key_var in key_vars:
            nginx_config.append(f'map $rl_whitelist {_whitelist_map_name(key_var)} {{')
            nginx_config.append(f'  0 {key_var};')
            nginx_config.append('  1 "";')
            nginx_config.append('}')

    # Blacklist Configuration
    if config[BLACKLIST_SECTION][ENABLED_KEY]:
        nginx_config.append('geo $rl_blacklist {')
        nginx_config.append('  default 0;')
        for ip in config[BLACKLIST_SECTION][IPS_KEY]:
            nginx_config.append(f'  {ip} 1;')
        nginx_config.append('}')
        # The matching `if ($rl_blacklist) { return 403; }` is emitted inside the
        # server block: nginx does not allow `if` at http level.

    def zone_key(settings: Dict[str, Any]) -> str:
        key_var = _zone_key(settings)
        return _whitelist_map_name(key_var) if whitelisted else key_var

    # Global rate limiting settings
    if global_settings[ENABLED_KEY]:
        global_burst = global_settings[BURST_KEY]
        rate = _nginx_rate(global_settings[REQUESTS_PER_MINUTE_KEY], global_settings[WINDOW_KEY])
        nginx_config.append(
            f'# default: {global_settings[REQUESTS_PER_MINUTE_KEY]} requests per {global_settings[WINDOW_KEY]}'
        )
        nginx_config.append(f'limit_req_zone {zone_key(global_settings)} zone=default:10m rate={rate};')

    # Path-specific rate limiting settings
    for path, limits in config.get(PATHS_SECTION, {}).items():
        if limits[ENABLED_KEY]:
            rate = _nginx_rate(limits[REQUESTS_PER_MINUTE_KEY], limits[WINDOW_KEY])
            zone_name = _generate_zone_name(path)
            nginx_config.append(
                f'# {path}: {limits[REQUESTS_PER_MINUTE_KEY]} requests per {limits[WINDOW_KEY]}'
            )
            nginx_config.append(f'limit_req_zone {zone_key(limits)} zone={zone_name}:10m rate={rate};')

    # Server block
    nginx_config.append('server {')

    if config[BLACKLIST_SECTION][ENABLED_KEY]:
        nginx_config.append('  if ($rl_blacklist) {')
        nginx_config.append('    return 403;')
        nginx_config.append('  }')

    # Default location
    if global_settings[ENABLED_KEY]:
        nginx_config.append('  location / {')
        nginx_config.append(f'    {_limit_req("default", global_settings[BURST_KEY])}')
        nginx_config.append('    # Add the directives that serve this location here.')
        nginx_config.append('  }')

    # Path-specific locations
    for path, limits in config.get(PATHS_SECTION, {}).items():
        if limits[ENABLED_KEY]:
            zone_name = _generate_zone_name(path)
            nginx_config.append(f'  location {path} {{')
            nginx_config.append(f'    {_limit_req(zone_name, limits[BURST_KEY])}')
            nginx_config.append('    # Add the directives that serve this location here.')
            nginx_config.append('  }')

    nginx_config.append('}')
    return "\n".join(nginx_config)


def _generate_zone_name(path: str) -> str:
    """
    Generates a valid zone name based on the path.

    Args:
        path: The path string to convert into a zone name.

    Returns:
        A valid zone name with special characters replaced by underscores.
    """
    return re.sub(r'[^a-zA-Z0-9_]', '_', path).strip('_')

WINDOW_PATTERN = re.compile(r'^(\d+)\s*([smh])$')


def _window_seconds(window: str) -> int:
    """
    Converts a window such as '30s', '1m' or '2h' into seconds.

    Args:
        window: The window string.

    Returns:
        The window length in seconds.

    Raises:
        ValueError: If the window cannot be parsed.
    """
    match = WINDOW_PATTERN.match(str(window).strip())
    if not match:
        raise ValueError(
            f"invalid window {window!r}: expected a number followed by 's', 'm' or 'h', for example '30s', '1m', '2h'"
        )
    amount, unit = int(match.group(1)), match.group(2)
    if amount == 0:
        raise ValueError(f"invalid window {window!r}: the window cannot be zero")
    return amount * {'s': 1, 'm': 60, 'h': 3600}[unit]


def _nginx_rate(requests: int, window: str) -> str:
    """
    Expresses "N requests per window" as an nginx `rate=` value.

    nginx accepts only two units, `r/s` and `r/m`, and only an integer count:
    verified against nginx 1.31.5, which rejects `1.5r/s`, `0r/m`, `1r/h` and
    the `60r/1min` this generator used to emit. So the window has to be folded
    into the rate rather than passed through as a unit.

    Args:
        requests: The number of requests allowed per window.
        window: The window string, for example '1m'.

    Returns:
        An nginx rate value, for example '10r/m' or '2r/s'.

    Raises:
        ValueError: If the rate is below one request per minute, which nginx
            cannot express at all.
    """
    seconds = _window_seconds(window)
    per_second = requests / seconds

    if per_second >= 1 and float(per_second).is_integer():
        return f"{int(per_second)}r/s"

    per_minute = requests * 60 / seconds
    if per_minute < 1:
        raise ValueError(
            f"{requests} requests per {window} is {per_minute:.4g} requests per minute, "
            "and nginx cannot express a rate below 1r/m. Raise the request count or shorten the window."
        )
    if float(per_minute).is_integer():
        return f"{int(per_minute)}r/m"

    rounded = max(1, round(per_minute))
    logger.warning(
        "%s requests per %s is %.4g r/m, which nginx cannot express exactly; emitting %dr/m",
        requests, window, per_minute, rounded,
    )
    return f"{rounded}r/m"


if __name__ == "__main__":
    config = load_config()
    if config:
        nginx_config = generate_nginx_config(config)
        print(nginx_config)
