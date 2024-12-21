# ratelimit2apache.py
import yaml
from typing import Dict, Any, List
import re

def load_config(config_path='config.yaml') -> Dict[str, Any]:
    """
    Load rate limit settings from config.yaml.

    Returns:
        A dictionary containing the validated configuration, or None if loading fails.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                print("Error: config file is empty")
                return None
            return _validate_config(config)
    except FileNotFoundError:
        print(f"Error: config file not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return None


def _validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the loaded configuration, setting default values and ensuring
    required keys are present.

    Args:
        config: The raw configuration dictionary loaded from the YAML file.

    Returns:
        A validated configuration dictionary, or None if validation fails.
    """

    # Validate global settings
    if 'global' not in config:
        print("Error: 'global' section is missing in config")
        return None

    global_settings = config['global']
    global_settings.setdefault('enabled', True)
    global_settings.setdefault('requests_per_minute', 60)
    global_settings.setdefault('burst', 20)
    global_settings.setdefault('window', '1m')
    global_settings.setdefault('limit_by', 'ip')

    if global_settings['limit_by'] not in ['ip', 'user_agent', 'header_name']:
         print("Error: Invalid 'limit_by' value in global section")
         return None


    # Validate paths settings
    if 'paths' in config:
        if not isinstance(config['paths'], dict):
          print("Error: 'paths' must be a dictionary")
          return None
        for path, settings in config['paths'].items():
          settings.setdefault('enabled', True)
          settings.setdefault('requests_per_minute', 60)
          settings.setdefault('burst', 20)
          settings.setdefault('window', '1m')
          settings.setdefault('limit_by', 'ip')
          if settings['limit_by'] not in ['ip', 'user_agent', 'header_name']:
            print(f"Error: Invalid 'limit_by' value for path {path}")
            return None


    # Validate whitelist
    if 'whitelist' in config:
        whitelist_config = config['whitelist']
        whitelist_config.setdefault('enabled', False)
        if 'ips' in whitelist_config:
            if not isinstance(whitelist_config['ips'], list):
                print("Error: 'ips' in 'whitelist' must be a list")
                return None
        else:
            whitelist_config['ips'] = [] # Ensure ips exist

    #Validate blacklist
    if 'blacklist' in config:
        blacklist_config = config['blacklist']
        blacklist_config.setdefault('enabled', False)
        if 'ips' in blacklist_config:
          if not isinstance(blacklist_config['ips'], list):
              print("Error: 'ips' in 'blacklist' must be a list")
              return None
        else:
          blacklist_config['ips'] = []

    # Validate advanced settings
    if 'advanced' in config:
      advanced_settings = config['advanced']
      advanced_settings.setdefault('log_level', 'info')
      if advanced_settings['log_level'] not in ['debug', 'info', 'warning', 'error']:
          print("Error: Invalid 'log_level' value in advanced section")
          return None
    else:
      config['advanced'] = {}
      config['advanced']['log_level'] = 'info'

    return config

def generate_apache_config(config: Dict[str, Any]) -> str:
    """Generates Apache ModSecurity rate limiting configuration from the loaded config."""
    apache_config = []

    apache_config.append("<IfModule mod_ratelimit.c>")

    # Whitelist Configuration
    if config['whitelist']['enabled']:
        apache_config.append("  <Files *>")
        apache_config.append("    <RequireAll>")
        for ip in config['whitelist']['ips']:
            apache_config.append(f"       Require not ip {ip}")
        apache_config.append("    </RequireAll>")
        apache_config.append("  </Files>")

    # Blacklist Configuration
    if config['blacklist']['enabled']:
        apache_config.append("  <Files *>")
        apache_config.append("    <RequireAll>")
        for ip in config['blacklist']['ips']:
            apache_config.append(f"      Require not ip {ip}")
        apache_config.append("    </RequireAll>")
        apache_config.append("  </Files>")

    # Global rate limiting settings
    global_settings = config['global']
    if global_settings['enabled']:
        global_rpm = global_settings['requests_per_minute']
        global_window = global_settings['window']
        global_limit_by = global_settings['limit_by']
        limit_by_directive = "REMOTE_ADDR"

        if global_limit_by == 'user_agent':
          limit_by_directive = "HTTP_USER_AGENT"
        elif global_limit_by == 'header_name':
          limit_by_directive = 'HTTP_' + config['global'].get('limit_by_header', 'custom_header').upper().replace('-','_')
        apache_config.append(f'  RateLimit {limit_by_directive} {global_rpm}/{_parse_window(global_window)}')
    # Path specific limits
    if 'paths' in config:
        for path, limits in config['paths'].items():
            if limits['enabled']:
                rpm = limits['requests_per_minute']
                window = limits['window']
                limit_by = limits['limit_by']
                limit_by_directive = "REMOTE_ADDR"
                if limit_by == 'user_agent':
                    limit_by_directive = "HTTP_USER_AGENT"
                elif limit_by == 'header_name':
                    limit_by_directive = 'HTTP_' + config['paths'][path].get('limit_by_header', 'custom_header').upper().replace('-','_')
                apache_config.append(f'  <Location "{path}">')
                apache_config.append(f'   RateLimit {limit_by_directive} {rpm}/{_parse_window(window)}')
                apache_config.append(f' </Location>')

    apache_config.append("</IfModule>")


    return "\n".join(apache_config)

def _parse_window(window:str)->str:
    """Parses the window time and transforms to the Apache format"""
    if window.endswith('s'):
       return window.replace('s','')
    elif window.endswith('m'):
        return window.replace('m', 'min')
    elif window.endswith('h'):
        return window.replace('h','h')
    else:
        return '1min'


if __name__ == "__main__":
    config = load_config()
    if config:
        apache_config = generate_apache_config(config)
        print(apache_config)
