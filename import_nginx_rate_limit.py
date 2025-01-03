# import_nginx_rate_limit.py
import os
import shutil
import logging
from typing import Optional

# Constants
SOURCE_FILE = 'rate_limit_rules/nginx/nginx_rate_limit.conf'
DEST_ENV_VAR = 'NGINX_RATE_LIMIT_FILE'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_nginx_rate_limit() -> None:
    """
    Imports the generated Nginx rate limit configuration to the destination file.
    The destination file path should be in the environment variable NGINX_RATE_LIMIT_FILE.
    """
    dest_file = os.environ.get(DEST_ENV_VAR)

    if not dest_file:
        logger.error("Error: NGINX_RATE_LIMIT_FILE environment variable not set.")
        return

    try:
        shutil.copyfile(SOURCE_FILE, dest_file)
        logger.info(f"Successfully imported Nginx rate limit configuration to {dest_file}")
    except FileNotFoundError:
        logger.error(f"Error: Source file not found: {SOURCE_FILE}")
    except PermissionError:
        logger.error(f"Error: Permission denied while copying to {dest_file}")
    except Exception as e:
        logger.error(f"Error copying the file: {e}")

if __name__ == "__main__":
    import_nginx_rate_limit()
