# import_haproxy_rate_limit.py
import os
import shutil
import re

def import_haproxy_rate_limit():
    """
    Imports the generated HAProxy rate limit configuration to the destination file.
    The destination file path should be in the environment variable HAPROXY_RATE_LIMIT_FILE.
    """
    source_file = 'rate_limit_rules/haproxy/haproxy_rate_limit.conf'
    dest_file = os.environ.get('HAPROXY_RATE_LIMIT_FILE')

    if not dest_file:
        print("Error: HAPROXY_RATE_LIMIT_FILE environment variable not set.")
        return

    try:
      with open(source_file, 'r') as source:
        config_content = source.read()

      with open(dest_file, 'r+') as dest:
           content = dest.read()
           #Regex to find the first frontend block, or add one if not present
           match = re.search(r'frontend\s+(\w+)', content)
           if match:
            start = match.start()
            new_content = content[:start+1] + '\n' + config_content + '\n' + content[start+1:]
           else:
               new_content = content + '\nfrontend http-in\n' + config_content
           dest.seek(0)
           dest.write(new_content)
           dest.truncate()
      print(f"Successfully imported HAProxy rate limit configuration to {dest_file}")
    except FileNotFoundError:
        print(f"Error: Source file not found: {source_file}")
    except Exception as e:
        print(f"Error writing to the file: {e}")

if __name__ == "__main__":
    import_haproxy_rate_limit()
