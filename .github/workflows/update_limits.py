name: Update Rate Limit Rules

on:
  schedule:
    - cron: '0 0 * * *'  # Run daily at midnight UTC
  workflow_dispatch: # Allow manual triggering

jobs:
  generate_rate_limits:
    runs-on: ubuntu-latest
    
    env:
       PYTHON_VERSION: 3.11 # Define a variable for the Python version
       CONFIG_FILE: config.yaml # Define a variable for the config file

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }} # Use the environment variable

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate Rate Limit Configs
        run: |
          python ratelimit2nginx.py > rate_limit_rules/nginx/nginx_rate_limit.conf
          python ratelimit2apache.py > rate_limit_rules/apache/apache_rate_limit.conf
          python ratelimit2traefik.py > rate_limit_rules/traefik/traefik_rate_limit.conf
          python ratelimit2haproxy.py > rate_limit_rules/haproxy/haproxy_rate_limit.conf

      - name: Check for changes
        id: check_changes
        run: |
          if [[ $(git status --porcelain | wc -l) -gt 0 ]]; then
             echo "::set-output name=has_changes::true"
          else
             echo "::set-output name=has_changes::false"
          fi


      - name: Commit and push changes
        if: steps.check_changes.outputs.has_changes == 'true'
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "Update rate limit rules"
          file_pattern: rate_limit_rules/*/*
