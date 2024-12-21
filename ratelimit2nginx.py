# ratelimit2nginx.py
import yaml

def load_config(config_path='config.yaml'):
    """Load rate limit settings from config.yaml."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        print(f"Error: config file not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing yaml: {e}")
        return None

def generate_nginx_config(config):
    """Generates Nginx rate limiting configuration from the loaded config."""
    nginx_config = []

    # Map for whitelisting
    nginx_config.append('geo $whitelist {')
    nginx_config.append('  default 0;')
    if config and 'whitelist' in config and config['whitelist']:
        for item in config['whitelist']:
          nginx_config.append(f'  {item} 1;')
    nginx_config.append('}')

    nginx_config.append('if ($whitelist) {')
    nginx_config.append('   set $limit_bypass 1;')
    nginx_config.append('}')


    # Global limits
    global_rpm = config['global']['requests_per_minute']
    global_burst = config['global']['burst']
    nginx_config.append(f'limit_req_zone $binary_remote_addr zone=default:10m rate={global_rpm}r/m;')


    # Path specific limits
    if 'paths' in config:
        for path, limits in config['paths'].items():
            rpm = limits['requests_per_minute']
            burst = limits['burst']
            zone_name = path.replace("/", "_").strip("_") # create a zone name based on the path
            nginx_config.append(f'limit_req_zone $binary_remote_addr zone={zone_name}:10m rate={rpm}r/m;')


    nginx_config.append('server {')
    nginx_config.append('  if ($limit_bypass) {')
    nginx_config.append('      return 200;')
    nginx_config.append('  }')


    nginx_config.append(f' location / {{')
    nginx_config.append(f'  limit_req zone=default burst={global_burst} nodelay;')
    nginx_config.append(f'  ... # Your other configurations here')
    nginx_config.append(f' }}')

    # path specific locations
    if 'paths' in config:
      for path, limits in config['paths'].items():
            burst = limits['burst']
            zone_name = path.replace("/", "_").strip("_") # create a zone name based on the path
            nginx_config.append(f' location {path} {{')
            nginx_config.append(f'  limit_req zone={zone_name} burst={burst} nodelay;')
            nginx_config.append(f'  ... # Your other configurations here')
            nginx_config.append(f' }}')


    nginx_config.append('}')


    return "\n".join(nginx_config)


if __name__ == "__main__":
    config = load_config()
    if config:
      nginx_config = generate_nginx_config(config)
      print(nginx_config)
