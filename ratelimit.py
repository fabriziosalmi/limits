# ratelimit.py
import yaml
import logging
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

# Valid values for certain fields
VALID_LIMIT_BY_VALUES = {'ip', 'user_agent', 'header_name'}
VALID_LOG_LEVELS = {'debug', 'info', 'warning', 'error'}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(config_path: str = 'config.yaml') -> Optional[Dict[str, Any]]:
    """
    Load rate limit settings from config.yaml and validate them.

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
    global_settings.setdefault('requests_per_minute', 60)
    global_settings.setdefault('burst', 20)
    global_settings.setdefault('window', '1m')
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
        settings.setdefault('requests_per_minute', 60)
        settings.setdefault('burst', 20)
        settings.setdefault('window', '1m')
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

if __name__ == '__main__':
    config = load_config()
    if config:
        logger.info("Loaded and validated config:")
        logger.info(config)
