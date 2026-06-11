# import_haproxy_rate_limit.py
import os
import re
import logging
from typing import Optional

# Constants
SOURCE_FILE = 'rate_limit_rules/haproxy/haproxy_rate_limit.conf'
DEST_ENV_VAR = 'HAPROXY_RATE_LIMIT_FILE'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def indent_content(content: str, indent: str = '    ') -> str:
    """Indent each non-empty line of content with the given indent string."""
    lines = content.splitlines(keepends=True)
    indented = []
    for line in lines:
        if line.strip():  # non-empty line
            indented.append(indent + line)
        else:
            indented.append(line)
    return ''.join(indented)

def import_haproxy_rate_limit() -> None:
    """
    Imports the generated HAProxy rate limit configuration to the destination file.
    The destination file path should be in the environment variable HAPROXY_RATE_LIMIT_FILE.
    """
    dest_file = os.environ.get(DEST_ENV_VAR)

    if not dest_file:
        logger.error("Error: HAPROXY_RATE_LIMIT_FILE environment variable not set.")
        return

    try:
        with open(SOURCE_FILE, 'r') as source:
            config_content = source.read()

        # Guard against empty source content to prevent config corruption
        if not config_content.strip():
            logger.warning("Source file is empty; skipping import.")
            return

        with open(dest_file, 'r+') as dest:
            content = dest.read()
            # Regex to find the first frontend block, or add one if not present
            match = re.search(r'frontend\s+(\w+)', content)
            if match:
                start = match.start()
                # Indent config content to match frontend block's context
                indented_config = indent_content(config_content)
                new_content = content[:start + len(match.group(0))] + '\n' + indented_config + '\n' + content[start + len(match.group(0)):]
            else:
                # Add new frontend block with indented config
                indented_config = indent_content(config_content)
                new_content = content + '\nfrontend http-in\n' + indented_config

            dest.seek(0)
            dest.write(new_content)
            dest.truncate()

        logger.info(f"Successfully imported HAProxy rate limit configuration to {dest_file}")
    except FileNotFoundError:
        logger.error(f"Error: Source file not found: {SOURCE_FILE}")
    except PermissionError:
        logger.error(f"Error: Permission denied while writing to {dest_file}")
    except Exception as e:
        logger.error(f"Error writing to the file: {e}")

if __name__ == "__main__":
    import_haproxy_rate_limit()
