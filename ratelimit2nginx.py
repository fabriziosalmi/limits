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

def generate_nginx_config(config: Dict[str, Any]) -> str:
    """
    Generates Nginx rate limiting configuration from the loaded config.

    Args:
        config: The validated configuration dictionary.

    Returns:
        A string containing the generated Nginx configuration.
    """
    nginx_config = []

    # Whitelist Configuration
    if config[WHITELIST_SECTION][ENABLED_KEY]:
        nginx_config.append('geo $whitelist {')
        nginx_config.append('  default 0;')
        for ip in config[WHITELIST_SECTION][IPS_KEY]:
            nginx_config.append(f'  {ip} 1;')
        nginx_config.append('}')
        nginx_config.append('if ($whitelist) {')
        nginx_config.append('   set $limit_bypass 1;')
        nginx_config.append('}')

    # Blacklist Configuration
    if config[BLACKLIST_SECTION][ENABLED_KEY]:
        nginx_config.append('geo $blacklist {')
        nginx_config.append('  default 0;')
        for ip in config[BLACKLIST_SECTION][IPS_KEY]:
            nginx_config.append(f'  {ip} 1;')
        nginx_config.append('}')
        nginx_config.append('if ($blacklist) {')
        nginx_config.append('   return 403;')  # Return 403 for blacklisted IPs
        nginx_config.append('}')

    # Global rate limiting settings
    global_settings = config[GLOBAL_SECTION]
    if global_settings[ENABLED_KEY]:
        global_rpm = global_settings[REQUESTS_PER_MINUTE_KEY]
        global_burst = global_settings[BURST_KEY]
        global_window = global_settings[WINDOW_KEY]
        global_limit_by = global_settings[LIMIT_BY_KEY]
        zone_var = '$binary_remote_addr'

        if global_limit_by == 'user_agent':
            zone_var = '$http_user_agent'
        elif global_limit_by == 'header_name':
            header_name = global_settings.get('limit_by_header', 'custom_header')
            zone_var = f'$http_{header_name}'

        nginx_config.append(f'limit_req_zone {zone_var} zone=default:10m rate={global_rpm}r/{_parse_window(global_window)};')

    # Path-specific rate limiting settings
    if PATHS_SECTION in config:
        for path, limits in config[PATHS_SECTION].items():
            if limits[ENABLED_KEY]:
                rpm = limits[REQUESTS_PER_MINUTE_KEY]
                burst = limits[BURST_KEY]
                window = limits[WINDOW_KEY]
                limit_by = limits[LIMIT_BY_KEY]
                zone_name = _generate_zone_name(path)
                zone_var = '$binary_remote_addr'

                if limit_by == 'user_agent':
                    zone_var = '$http_user_agent'
                elif limit_by == 'header_name':
                    header_name = limits.get('limit_by_header', 'custom_header')
                    zone_var = f'$http_{header_name}'

                nginx_config.append(f'limit_req_zone {zone_var} zone={zone_name}:10m rate={rpm}r/{_parse_window(window)};')

    # Server block
    nginx_config.append('server {')

    if config[WHITELIST_SECTION][ENABLED_KEY]:
        nginx_config.append('  if ($limit_bypass) {')
        nginx_config.append('      return 200;')
        nginx_config.append('  }')

    # Default location
    if global_settings[ENABLED_KEY]:
        nginx_config.append('  location / {')
        nginx_config.append(f'    limit_req zone=default burst={global_burst} nodelay;')
        nginx_config.append('    ... # Your other configurations here')
        nginx_config.append('  }')

    # Path-specific locations
    if PATHS_SECTION in config:
        for path, limits in config[PATHS_SECTION].items():
            if limits[ENABLED_KEY]:
                burst = limits[BURST_KEY]
                zone_name = _generate_zone_name(path)
                nginx_config.append(f'  location {path} {{')
                nginx_config.append(f'    limit_req zone={zone_name} burst={burst} nodelay;')
                nginx_config.append('    ... # Your other configurations here')
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

def _parse_window(window: str) -> str:
    """
    Parses the window time and transforms it to the Nginx format.

    Args:
        window: The window string (e.g., '1m', '30s', '2h').

    Returns:
        The window string in Nginx format (e.g., '1min', '30', '2h').
    """
    if window.endswith('s'):
        return window[:-1]
    elif window.endswith('m'):
        return window[:-1] + 'min'
    elif window.endswith('h'):
        return window
    return 'min'

if __name__ == "__main__":
    config = load_config()
    if config:
        nginx_config = generate_nginx_config(config)
        print(nginx_config)
