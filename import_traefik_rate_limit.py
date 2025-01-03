# import_traefik_rate_limit.py
import os
import re
import logging
from typing import Optional

# Constants
SOURCE_FILE = 'rate_limit_rules/traefik/traefik_rate_limit.conf'
DEST_ENV_VAR = 'TRAEFIK_RATE_LIMIT_FILE'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_traefik_rate_limit() -> None:
    """
    Imports the generated Traefik rate limit configuration to the destination file.
    The destination file path should be in the environment variable TRAEFIK_RATE_LIMIT_FILE.
    """
    dest_file = os.environ.get(DEST_ENV_VAR)

    if not dest_file:
        logger.error("Error: TRAEFIK_RATE_LIMIT_FILE environment variable not set.")
        return

    try:
        with open(SOURCE_FILE, 'r') as source:
            config_content = source.read()

        with open(dest_file, 'r+') as dest:
            content = dest.read()
            # Regex to find the http middlewares block, or create one if none
            match = re.search(r'\[http\.middlewares\]', content)
            if match:
                start = match.start()
                # Find the next block (or the end of file)
                next_block_match = re.search(r'(\n\[[\w\.]+\])', content[start + 1:])
                if next_block_match:
                    end = start + 1 + next_block_match.start()
                    new_content = content[:start + 1] + config_content + '\n' + content[end:]
                else:
                    new_content = content[:start + 1] + config_content + '\n'
            else:
                new_content = content + '\n[http.middlewares]\n' + config_content

            dest.seek(0)
            dest.write(new_content)
            dest.truncate()

        logger.info(f"Successfully imported Traefik rate limit configuration to {dest_file}")
    except FileNotFoundError:
        logger.error(f"Error: Source file not found: {SOURCE_FILE}")
    except PermissionError:
        logger.error(f"Error: Permission denied while writing to {dest_file}")
    except Exception as e:
        logger.error(f"Error writing to the file: {e}")

if __name__ == "__main__":
    import_traefik_rate_limit()
