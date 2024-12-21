name: Update Rate Limit Rules

on:
  schedule:
    - cron: '0 0 * * *'  # Run daily at midnight UTC
  workflow_dispatch: # Allow manual triggering

jobs:
  generate_rate_limits:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate Caddy rate limit config
        run: python ratelimit2caddy.py > rate_limit_rules/caddy/caddy_rate_limit.conf

      - name: Generate Nginx rate limit config
        run: python ratelimit2nginx.py > rate_limit_rules/nginx/nginx_rate_limit.conf

      - name: Generate Apache rate limit config
        run: python ratelimit2apache.py > rate_limit_rules/apache/apache_rate_limit.conf

      - name: Generate Traefik rate limit config
        run: python ratelimit2traefik.py > rate_limit_rules/traefik/traefik_rate_limit.conf

      - name: Generate Haproxy rate limit config
        run: python ratelimit2haproxy.py > rate_limit_rules/haproxy/haproxy_rate_limit.conf

      - name: Commit and push changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "Update rate limit rules"
          file_pattern: rate_limit_rules/*/*
