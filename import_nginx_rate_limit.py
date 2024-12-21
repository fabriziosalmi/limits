# import_nginx_rate_limit.py
import os
import shutil

def import_nginx_rate_limit():
    """
    Imports the generated Nginx rate limit configuration to the destination file.
    The destination file path should be in the environment variable NGINX_RATE_LIMIT_FILE.
    """
    source_file = 'rate_limit_rules/nginx/nginx_rate_limit.conf'
    dest_file = os.environ.get('NGINX_RATE_LIMIT_FILE')

    if not dest_file:
        print("Error: NGINX_RATE_LIMIT_FILE environment variable not set.")
        return

    try:
        shutil.copyfile(source_file, dest_file)
        print(f"Successfully imported Nginx rate limit configuration to {dest_file}")
    except FileNotFoundError:
        print(f"Error: Source file not found: {source_file}")
    except Exception as e:
        print(f"Error copying the file: {e}")

if __name__ == "__main__":
    import_nginx_rate_limit()
