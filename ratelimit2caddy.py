# ratelimit2caddy.py
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


def generate_caddy_config(config: Dict[str, Any]) -> str:
    """Generates Caddy rate limiting configuration from the loaded config."""
    caddy_config = []


    # Global limits
    global_settings = config['global']
    if global_settings['enabled']:
      global_rpm = global_settings['requests_per_minute']
      global_burst = global_settings['burst']
      global_window = global_settings['window']
      global_limit_by = global_settings['limit_by']
      caddy_config.append('{')
      caddy_config.append('  rate_limit {')
      caddy_config.append(f'    limit {global_rpm}')
      caddy_config.append(f'    burst {global_burst}')
      caddy_config.append(f'    window {_parse_window(global_window)}')
      if global_limit_by == 'ip':
        caddy_config.append('    by ip')
      elif global_limit_by == 'user_agent':
        caddy_config.append('    by header User-Agent')
      elif global_limit_by == 'header_name':
         header_name = config['global'].get('limit_by_header','custom_header')
         caddy_config.append(f'   by header {header_name}')
      caddy_config.append('  }')


    # Path specific limits
    if 'paths' in config:
        for path, limits in config['paths'].items():
          if limits['enabled']:
            rpm = limits['requests_per_minute']
            burst = limits['burst']
            window = limits['window']
            limit_by = limits['limit_by']
            caddy_config.append('  rate_limit {')
            caddy_config.append(f'    match path {path}')
            caddy_config.append(f'    limit {rpm}')
            caddy_config.append(f'    burst {burst}')
            caddy_config.append(f'    window {_parse_window(window)}')
            if limit_by == 'ip':
              caddy_config.append('    by ip')
            elif limit_by == 'user_agent':
              caddy_config.append('    by header User-Agent')
            elif limit_by == 'header_name':
              header_name = config['paths'][path].get('limit_by_header','custom_header')
              caddy_config.append(f'   by header {header_name}')
            caddy_config.append('  }')

    if config['whitelist']['enabled']:
      caddy_config.append('  @whitelist {')
      caddy_config.append(f'    remote_ip {" ".join(config["whitelist"]["ips"])}')
      caddy_config.append('  }')
      caddy_config.append('  respond @whitelist 200')
    caddy_config.append('}') #Close main config


    return "\n".join(caddy_config)


def _parse_window(window:str)->str:
    """Parses the window time and transforms to the caddy format"""
    if window.endswith('s') or window.endswith('m') or window.endswith('h'):
        return window
    else:
        return '1m'

if __name__ == "__main__":
    config = load_config()
    if config:
      caddy_config = generate_caddy_config(config)
      print(caddy_config)
