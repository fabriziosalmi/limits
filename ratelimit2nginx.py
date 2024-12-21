# ratelimit2nginx.py
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



def generate_nginx_config(config: Dict[str, Any]) -> str:
    """Generates Nginx rate limiting configuration from the loaded config."""
    nginx_config = []

    # Map for whitelisting
    if config['whitelist']['enabled']:
        nginx_config.append('geo $whitelist {')
        nginx_config.append('  default 0;')
        for item in config['whitelist']['ips']:
             nginx_config.append(f'  {item} 1;')
        nginx_config.append('}')

        nginx_config.append('if ($whitelist) {')
        nginx_config.append('   set $limit_bypass 1;')
        nginx_config.append('}')

    # Map for blacklisting
    if config['blacklist']['enabled']:
        nginx_config.append('geo $blacklist {')
        nginx_config.append('  default 0;')
        for item in config['blacklist']['ips']:
             nginx_config.append(f'  {item} 1;')
        nginx_config.append('}')

        nginx_config.append('if ($blacklist) {')
        nginx_config.append('   return 403;') # Return 403 for blacklisted ips
        nginx_config.append('}')

    # Global limits
    global_settings = config['global']
    if global_settings['enabled']:
      global_rpm = global_settings['requests_per_minute']
      global_burst = global_settings['burst']
      global_window = global_settings['window']
      global_limit_by = global_settings['limit_by']
      zone_var = '$binary_remote_addr'

      if global_limit_by == 'user_agent':
          zone_var = '$http_user_agent'
      elif global_limit_by == 'header_name':
        zone_var = '$http_' + config['global'].get('limit_by_header','custom_header')

      nginx_config.append(f'limit_req_zone {zone_var} zone=default:10m rate={global_rpm}r/{_parse_window(global_window)};')


    # Path specific limits
    if 'paths' in config:
        for path, limits in config['paths'].items():
            if limits['enabled']:
              rpm = limits['requests_per_minute']
              burst = limits['burst']
              window = limits['window']
              limit_by = limits['limit_by']
              zone_name = _generate_zone_name(path)
              zone_var = '$binary_remote_addr'
              if limit_by == 'user_agent':
                zone_var = '$http_user_agent'
              elif limit_by == 'header_name':
                  zone_var = '$http_' + config['paths'][path].get('limit_by_header','custom_header')
              nginx_config.append(f'limit_req_zone {zone_var} zone={zone_name}:10m rate={rpm}r/{_parse_window(window)};')


    nginx_config.append('server {')

    if config['whitelist']['enabled']:
      nginx_config.append('  if ($limit_bypass) {')
      nginx_config.append('      return 200;')
      nginx_config.append('  }')


    # default location
    if global_settings['enabled']:
      nginx_config.append(f' location / {{')
      nginx_config.append(f'  limit_req zone=default burst={global_burst} nodelay;')
      nginx_config.append(f'  ... # Your other configurations here')
      nginx_config.append(f' }}')

    # path specific locations
    if 'paths' in config:
      for path, limits in config['paths'].items():
        if limits['enabled']:
          burst = limits['burst']
          zone_name = _generate_zone_name(path)
          nginx_config.append(f' location {path} {{')
          nginx_config.append(f'  limit_req zone={zone_name} burst={burst} nodelay;')
          nginx_config.append(f'  ... # Your other configurations here')
          nginx_config.append(f' }}')

    nginx_config.append('}')
    return "\n".join(nginx_config)

def _generate_zone_name(path:str)->str:
  """ Generates a valid zone name based on the path"""
  return re.sub(r'[^a-zA-Z0-9_]', '_', path).strip('_')

def _parse_window(window:str)->str:
    """Parses the window time and transforms to the nginx format"""
    if window.endswith('s'):
        return window.replace('s','')
    elif window.endswith('m'):
        return window.replace('m','min')
    elif window.endswith('h'):
        return window.replace('h', 'h')
    else:
        return 'min'


if __name__ == "__main__":
  config = load_config()
  if config:
    nginx_config = generate_nginx_config(config)
    print(nginx_config)
