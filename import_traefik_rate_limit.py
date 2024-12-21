# import_traefik_rate_limit.py
import os
import shutil
import re

def import_traefik_rate_limit():
    """
    Imports the generated Traefik rate limit configuration to the destination file.
    The destination file path should be in the environment variable TRAEFIK_RATE_LIMIT_FILE.
    """
    source_file = 'rate_limit_rules/traefik/traefik_rate_limit.conf'
    dest_file = os.environ.get('TRAEFIK_RATE_LIMIT_FILE')

    if not dest_file:
      print("Error: TRAEFIK_RATE_LIMIT_FILE environment variable not set.")
      return

    try:
       with open(source_file, 'r') as source:
          config_content = source.read()
       with open(dest_file, 'r+') as dest:
           content = dest.read()
           #Regex to find the http middlewares block, or create one if none
           match = re.search(r'\[http\.middlewares\]', content)
           if match:
            start = match.start()
            #Find the next block (or the end of file)
            next_block_match = re.search(r'(\n\[[\w\.]+\])', content[start+1:])
            if next_block_match:
              end = start + 1 + next_block_match.start()
              new_content = content[:start+1] + config_content + '\n' + content[end:]
            else:
              new_content = content[:start+1] + config_content + '\n'
           else:
               new_content = content + '\n[http.middlewares]\n' + config_content
           dest.seek(0)
           dest.write(new_content)
           dest.truncate()
       print(f"Successfully imported Traefik rate limit configuration to {dest_file}")

    except FileNotFoundError:
        print(f"Error: Source file not found: {source_file}")
    except Exception as e:
        print(f"Error writing to the file: {e}")


if __name__ == "__main__":
    import_traefik_rate_limit()
