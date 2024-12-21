# ratelimit2haproxy.py
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

def generate_haproxy_config(config: Dict[str, Any]) -> str:
    """Generates HAProxy rate limiting configuration from the loaded config."""
    haproxy_config = []

     # Whitelist Configuration
    if config['whitelist']['enabled']:
        for ip in config['whitelist']['ips']:
            haproxy_config.append(f'acl whitelist src {ip}')
        haproxy_config.append('http-request allow if whitelist')


     # Blacklist Configuration
    if config['blacklist']['enabled']:
         for ip in config['blacklist']['ips']:
           haproxy_config.append(f'acl blacklist src {ip}')
         haproxy_config.append('http-request deny if blacklist')

    # Global rate limiting settings
    global_settings = config['global']
    if global_settings['enabled']:
      global_rpm = global_settings['requests_per_minute']
      global_window = global_settings['window']
      global_limit_by = global_settings['limit_by']
      acl_name = 'global_rate_limit'
      if global_limit_by == 'ip':
        haproxy_config.append(f'acl {acl_name} src_conn_rate_ge {global_rpm}')
      elif global_limit_by == 'user_agent':
        haproxy_config.append(f'acl {acl_name} req.hdr(User-Agent),rate_ge {global_rpm}')
      elif global_limit_by == 'header_name':
        header_name = config['global'].get('limit_by_header', 'custom_header')
        haproxy_config.append(f'acl {acl_name} req.hdr({header_name}),rate_ge {global_rpm}')

      haproxy_config.append(f'http-request deny if {acl_name}')



    # Path specific limits
    if 'paths' in config:
      for path, limits in config['paths'].items():
         if limits['enabled']:
          rpm = limits['requests_per_minute']
          limit_by = limits['limit_by']
          acl_name = f'{_generate_acl_name(path)}_rate_limit'
          haproxy_config.append(f'acl is_{_generate_acl_name(path)} path_beg {path}')
          if limit_by == 'ip':
            haproxy_config.append(f'acl {acl_name} src_conn_rate_ge {rpm}')
          elif limit_by == 'user_agent':
            haproxy_config.append(f'acl {acl_name} req.hdr(User-Agent),rate_ge {rpm}')
          elif limit_by == 'header_name':
            header_name = config['paths'][path].get('limit_by_header', 'custom_header')
            haproxy_config.append(f'acl {acl_name} req.hdr({header_name}),rate_ge {rpm}')

          haproxy_config.append(f'http-request deny if is_{_generate_acl_name(path)} {acl_name}')

    return "\n".join(haproxy_config)


def _generate_acl_name(path:str)->str:
  """ Generates a valid acl name based on the path"""
  return re.sub(r'[^a-zA-Z0-9_]', '_', path).strip('_')


if __name__ == "__main__":
    config = load_config()
    if config:
        haproxy_config = generate_haproxy_config(config)
        print(haproxy_config)
