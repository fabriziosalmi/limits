# ratelimit2traefik.py
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

def generate_traefik_config(config: Dict[str, Any]) -> str:
    """Generates Traefik rate limiting configuration from the loaded config."""
    traefik_config = []
    traefik_config.append("[http.middlewares]")

    # Whitelist Configuration
    if config['whitelist']['enabled']:
        traefik_config.append(f'  [http.middlewares.whitelist-middleware.ipWhiteList]')
        traefik_config.append(f'    sourceRange = {config["whitelist"]["ips"]}')


    # Blacklist Configuration
    if config['blacklist']['enabled']:
      traefik_config.append(f'  [http.middlewares.blacklist-middleware.ipWhiteList]')
      traefik_config.append(f'    sourceRange = {config["blacklist"]["ips"]}')

    # Global rate limiting settings
    global_settings = config['global']
    if global_settings['enabled']:
        global_rpm = global_settings['requests_per_minute']
        global_burst = global_settings['burst']
        global_window = global_settings['window']
        global_limit_by = global_settings['limit_by']
        middleware_name = "global-rate-limit"

        if global_limit_by == 'ip':
          traefik_config.append(f'  [http.middlewares.{middleware_name}.ratelimit]')
          traefik_config.append(f'    average = {global_rpm}')
          traefik_config.append(f'    burst = {global_burst}')
        elif global_limit_by == 'user_agent':
           traefik_config.append(f' [http.middlewares.{middleware_name}.headers]')
           traefik_config.append(f'    customRequestHeaders.X-User-Agent =  {{Header "User-Agent"}}')
           traefik_config.append(f'  [http.middlewares.{middleware_name}.ratelimit]')
           traefik_config.append(f'    average = {global_rpm}')
           traefik_config.append(f'    burst = {global_burst}')
           traefik_config.append(f'    sourceCriterion.requestHeaderName = "X-User-Agent"')
        elif global_limit_by == 'header_name':
           header_name = config['global'].get('limit_by_header', 'custom_header').replace('-','_')
           traefik_config.append(f' [http.middlewares.{middleware_name}.headers]')
           traefik_config.append(f'    customRequestHeaders.X-{header_name} =  {{Header "{header_name}"}}')
           traefik_config.append(f'  [http.middlewares.{middleware_name}.ratelimit]')
           traefik_config.append(f'    average = {global_rpm}')
           traefik_config.append(f'    burst = {global_burst}')
           traefik_config.append(f'    sourceCriterion.requestHeaderName = "X-{header_name}"')

    # Path specific limits
    if 'paths' in config:
      for path, limits in config['paths'].items():
          if limits['enabled']:
                rpm = limits['requests_per_minute']
                burst = limits['burst']
                limit_by = limits['limit_by']
                middleware_name = f"{_generate_middleware_name(path)}-rate-limit"

                if limit_by == 'ip':
                  traefik_config.append(f'  [http.middlewares.{middleware_name}.ratelimit]')
                  traefik_config.append(f'    average = {rpm}')
                  traefik_config.append(f'    burst = {burst}')
                elif limit_by == 'user_agent':
                   traefik_config.append(f'  [http.middlewares.{middleware_name}.headers]')
                   traefik_config.append(f'    customRequestHeaders.X-User-Agent =  {{Header "User-Agent"}}')
                   traefik_config.append(f'  [http.middlewares.{middleware_name}.ratelimit]')
                   traefik_config.append(f'    average = {rpm}')
                   traefik_config.append(f'    burst = {burst}')
                   traefik_config.append(f'    sourceCriterion.requestHeaderName = "X-User-Agent"')
                elif limit_by == 'header_name':
                   header_name = config['paths'][path].get('limit_by_header', 'custom_header').replace('-','_')
                   traefik_config.append(f' [http.middlewares.{middleware_name}.headers]')
                   traefik_config.append(f'    customRequestHeaders.X-{header_name} =  {{Header "{header_name}"}}')
                   traefik_config.append(f'  [http.middlewares.{middleware_name}.ratelimit]')
                   traefik_config.append(f'    average = {rpm}')
                   traefik_config.append(f'    burst = {burst}')
                   traefik_config.append(f'    sourceCriterion.requestHeaderName = "X-{header_name}"')


    # Routes section (example on how to add the rate limit middleware)
    traefik_config.append("[http.routers]")

    if config['whitelist']['enabled']:
        traefik_config.append(f'  [http.routers.my-router.middlewares]')
        traefik_config.append(f'    - whitelist-middleware')

    if config['blacklist']['enabled']:
      traefik_config.append(f'  [http.routers.my-router.middlewares]')
      traefik_config.append(f'    - blacklist-middleware')

    if global_settings['enabled']:
      traefik_config.append(f'  [http.routers.my-router.middlewares]')
      traefik_config.append(f'    - global-rate-limit')


    if 'paths' in config:
      for path, limits in config['paths'].items():
          if limits['enabled']:
            middleware_name = f"{_generate_middleware_name(path)}-rate-limit"
            traefik_config.append(f'  [http.routers.my-router.middlewares]')
            traefik_config.append(f'    - {middleware_name}')

    return "\n".join(traefik_config)


def _generate_middleware_name(path:str)->str:
  """ Generates a valid middleware name based on the path"""
  return re.sub(r'[^a-zA-Z0-9_]', '_', path).strip('_')


if __name__ == "__main__":
    config = load_config()
    if config:
      traefik_config = generate_traefik_config(config)
      print(traefik_config)
