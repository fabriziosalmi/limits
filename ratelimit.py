# ratelimit.py
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

if __name__ == '__main__':
  config = load_config()
  if config:
      print("Loaded config:")
      print(config)
