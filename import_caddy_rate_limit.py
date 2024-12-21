# import_caddy_rate_limit.py
import os
import shutil

def import_caddy_rate_limit():
    """
    Imports the generated Caddy rate limit configuration to the destination file.
    The destination file path should be in the environment variable CADDY_RATE_LIMIT_FILE.
    """
    source_file = 'rate_limit_rules/caddy/caddy_rate_limit.conf'
    dest_file = os.environ.get('CADDY_RATE_LIMIT_FILE')

    if not dest_file:
        print("Error: CADDY_RATE_LIMIT_FILE environment variable not set.")
        return

    try:
        shutil.copyfile(source_file, dest_file)
        print(f"Successfully imported Caddy rate limit configuration to {dest_file}")
    except FileNotFoundError:
        print(f"Error: Source file not found: {source_file}")
    except Exception as e:
        print(f"Error copying the file: {e}")



if __name__ == "__main__":
    import_caddy_rate_limit()
