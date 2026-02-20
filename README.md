# Limits

Python scripts that generate rate limiting configuration files for common web servers from a single `config.yaml` file. A GitHub Actions workflow runs these scripts daily and commits updated configs to the repository.

## Features

*   **Multi-Web Server Support:** Generates rate limiting configurations for Apache (mod_ratelimit), Nginx, Traefik, and HAProxy.
*   **Centralized Configuration:** Uses a single `config.yaml` file to define global and path-specific rate limits, as well as IP whitelisting/blacklisting.
*   **Automated Config Generation:** GitHub Actions runs the generation scripts daily and commits the resulting files to `rate_limit_rules/`.
*   **Limiting Strategies:** Supports limiting by IP address, User-Agent, or a named request header.
*   **Path-Specific Overrides:** Configure different rate limits for individual URL paths in addition to a global default.

## Supported Web Servers

*   **Nginx**
*   **Apache** (mod_ratelimit)
*   **Traefik**
*   **HAProxy**

> [!NOTE]
> If you use Caddy please check the [caddy-waf](https://github.com/fabriziosalmi/caddy-waf) project.

## Project Structure

```
limits/
├── rate_limit_rules/       # Generated rate limit config files
│   ├── nginx/              # Nginx rate limit configs
│   ├── apache/             # Apache rate limit configs (mod_ratelimit)
│   ├── traefik/            # Traefik rate limit configs
│   └── haproxy/            # HAProxy rate limit configs
├── import_apache_rate_limit.py
├── import_haproxy_rate_limit.py
├── import_nginx_rate_limit.py
├── import_traefik_rate_limit.py
├── ratelimit.py            # Loads and validates config.yaml
├── ratelimit2nginx.py      # Generates Nginx config
├── ratelimit2apache.py     # Generates Apache mod_ratelimit config
├── ratelimit2traefik.py    # Generates Traefik config
├── ratelimit2haproxy.py    # Generates HAProxy config
├── config.yaml             # Rate limit definitions
├── requirements.txt        # Python dependencies
├── CONTRIBUTING.md         # Contribution guidelines
├── CHANGELOG.md            # Project changelog
└── .github/workflows/      # GitHub Actions workflow for automated generation
    └── update_limits.py
```

## How It Works

### 1. Configuration

   *   The `config.yaml` file allows you to configure your desired rate limits, including global settings, path-specific settings, whitelists, blacklists and advanced options.

   ```yaml
   # config.yaml
    global:
      enabled: true
      requests_per_minute: 60
      burst: 20
      window: 1m
      limit_by: ip
      # limit_by_header: custom_header

    paths:
      /login:
        enabled: true
        requests_per_minute: 10
        burst: 5
        window: 1m
        limit_by: ip
      /api:
        enabled: true
        requests_per_minute: 120
        burst: 40
        window: 1m
        limit_by: ip
      '/search/(.*)':
        enabled: true
        requests_per_minute: 100
        burst: 20
        window: 1m
        limit_by: ip

    whitelist:
      enabled: false
      ips:
        - 192.168.1.10
        - 192.168.1.11/32
        - 2001:0db8::/32

    blacklist:
      enabled: false
      ips:
        - 192.168.1.20
        - 192.168.1.22/32

    advanced:
      log_level: info
   ```

### 2. Generation

*   The `ratelimit.py` script loads and validates the configurations from `config.yaml`.
*   `ratelimit2nginx.py` generates Nginx configuration
*   `ratelimit2apache.py` generates Apache mod_ratelimit configuration
*   `ratelimit2traefik.py` generates Traefik configuration
*   `ratelimit2haproxy.py` generates HAProxy configuration

### 3. Automation

*   The GitHub Actions workflow automatically generates rate limiting configurations daily.
*   Modified configuration files are automatically committed and pushed to the repository.

## Installation

### Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Python 3.7+**: Required to run the rate limit generation scripts
*   **pip**: Python package manager (usually comes with Python)
*   **Git**: For cloning the repository
*   **A supported web server**: At least one of the following:
    *   Nginx
    *   Apache with mod_ratelimit
    *   Traefik
    *   HAProxy

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/fabriziosalmi/limits.git
    cd limits
    ```

2.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure `config.yaml`:**
     * Edit the `config.yaml` file to define your specific rate limiting requirements.
     * Configure global settings, path-specific rules, and whitelist/blacklist as needed.

## Usage (Web Server Integration)

1.  **Generate Configuration:**
   *   The rate limit configuration files will be generated automatically by github actions.
2. **Integrate configuration with your webserver**

### 1. Nginx Rate Limit Integration
  * Copy `rate_limit_rules/nginx/nginx_rate_limit.conf` to your server.
  * Include the configuration in your nginx configuration file (`nginx.conf`)

  ```nginx
   http {
      include /path/to/nginx_rate_limit.conf;
      ...
   }
  ```

### 2. Apache Rate Limit Integration
  * Copy `rate_limit_rules/apache/apache_rate_limit.conf` to your server.
  * Include the configuration in your apache virtualhost configuration file or inside a `.htaccess` file.

  ```apache
  <VirtualHost *:80>
    ...
     Include /path/to/apache_rate_limit.conf
   ...
  </VirtualHost>
  ```

### 3. Traefik Rate Limit Integration
   * Copy the content of `rate_limit_rules/traefik/traefik_rate_limit.conf` to your traefik configuration file (`traefik.yml`)

     ```yaml
     # traefik.yml
     ...
     http:
       middlewares:
         # Insert content of traefik_rate_limit.conf here
       routers:
        # Add the rate limit middlewares to the routes

     ...
     ```
### 4. Haproxy Rate Limit Integration
    *   Copy `rate_limit_rules/haproxy/haproxy_rate_limit.conf` to your server.
    *   Include the configuration in your HAProxy configuration file (`haproxy.cfg`)
  ```
    frontend http-in
        # Insert the content of haproxy_rate_limit.conf here
    ...
  ```

## Testing Your Configuration

Before deploying to production, it's important to test your rate limit configuration:

### 1. Validate Configuration Files

**For Nginx:**
```bash
nginx -t
```

**For Apache:**
```bash
apachectl configtest
```

**For HAProxy:**
```bash
haproxy -c -f /etc/haproxy/haproxy.cfg
```

### 2. Test Rate Limiting Locally

You can use tools like `curl` or `ab` (Apache Bench) to test rate limiting:

```bash
# Send multiple rapid requests to test rate limiting
for i in {1..100}; do curl -s http://localhost/api; done

# Use Apache Bench for load testing
ab -n 100 -c 10 http://localhost/api
```

### 3. Monitor Logs

Check your web server logs to verify that rate limiting is working:

**Nginx:**
```bash
tail -f /var/log/nginx/error.log
```

**Apache:**
```bash
tail -f /var/log/apache2/error.log
```

**HAProxy:**
```bash
tail -f /var/log/haproxy.log
```

## Automation (GitHub Workflow)

*   **Daily Generation:** GitHub Actions runs the generation scripts daily at midnight UTC and commits any changed files to `rate_limit_rules/`.
*   **Manual Trigger:** The workflow can also be triggered manually via `workflow_dispatch`.

## Troubleshooting

### Common Issues

**Issue: "Error: config file not found"**
*   **Solution:** Ensure `config.yaml` exists in the root directory of the project.

**Issue: "Error parsing YAML"**
*   **Solution:** Check that your `config.yaml` file has valid YAML syntax. Use a YAML validator if needed.

**Issue: Rate limits not working after configuration**
*   **Solution:** 
    *   Verify that the configuration file is correctly included in your web server's configuration.
    *   Restart your web server after applying the configuration.
    *   Check your web server's error logs for any configuration errors.

**Issue: Generated configuration files are empty**
*   **Solution:** Run the generation scripts manually to check for errors:
    ```bash
    python ratelimit2nginx.py
    python ratelimit2apache.py
    python ratelimit2traefik.py
    python ratelimit2haproxy.py
    ```

**Issue: Import scripts fail with "environment variable not set"**
*   **Solution:** Set the appropriate environment variable before running the import script:
    ```bash
    export NGINX_RATE_LIMIT_FILE=/path/to/nginx/conf.d/rate_limit.conf
    python import_nginx_rate_limit.py
    ```

## Contributing

Contributions are welcome. Here's the typical workflow:

1.  **Fork the Repository:** Click the "Fork" button at the top right of the repository page.
2.  **Clone Your Fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/limits.git
    cd limits
    ```
3.  **Create a Feature Branch:** Use a descriptive name for your branch.
    ```bash
    git checkout -b feature/your-feature-name
    ```
4.  **Make Your Changes:** Implement your feature or bug fix.
5.  **Test Your Changes:** Ensure the scripts run correctly:
    ```bash
    python ratelimit.py
    python ratelimit2nginx.py
    python ratelimit2apache.py
    python ratelimit2traefik.py
    python ratelimit2haproxy.py
    ```
6.  **Commit Your Changes:** Write clear, concise commit messages.
    ```bash
    git add .
    git commit -m "feat: add new feature description"
    ```
7.  **Push to Your Fork:**
    ```bash
    git push origin feature/your-feature-name
    ```
8.  **Open a Pull Request:** Go to the original repository and click "New Pull Request".

### Contribution Guidelines

*   Follow the existing code style and conventions.
*   Add comments to explain complex logic.
*   Update documentation if you change functionality.
*   Test your changes thoroughly before submitting.
*   Keep pull requests focused on a single feature or fix.

For more detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Security Considerations

When implementing rate limiting, keep these security best practices in mind:

### 1. Don't Rely Solely on Rate Limiting

Rate limiting is one layer of defense. Implement additional security measures:
*   Input validation and sanitization
*   Authentication and authorization
*   HTTPS/TLS encryption
*   Web Application Firewall (WAF)
*   Regular security updates

### 2. Configure Appropriate Limits

*   **Too restrictive**: May block legitimate users
*   **Too lenient**: May not prevent abuse effectively
*   Monitor your traffic patterns and adjust accordingly

### 3. Whitelist Trusted IPs Carefully

*   Only whitelist IPs you fully trust (e.g., monitoring services, trusted partners)
*   Regularly review and update your whitelist
*   Use CIDR notation to specify IP ranges precisely

### 4. Protect Sensitive Endpoints

Apply stricter rate limits to sensitive endpoints:
*   Login pages (`/login`, `/auth`)
*   API endpoints (`/api/*`)
*   Password reset (`/reset-password`)
*   Search functionality (`/search`)

### 5. Monitor and Log

*   Enable logging to track rate limit violations
*   Set up alerts for unusual patterns
*   Regularly review logs for potential attacks

### 6. Consider Distributed Environments

If running multiple server instances:
*   Use a shared storage for rate limit counters (Redis, Memcached)
*   Ensure rate limits are synchronized across all instances
*   Consider using a centralized rate limiting solution

## License

This project is licensed under the MIT License.
See the `LICENSE` file for details.

## Need Help?

*   Issues? Open a ticket in the Issues tab.

## Resources

*   [Nginx Rate Limiting](https://docs.nginx.com/nginx/admin-guide/security/rate-limiting/)
*   [Apache mod_ratelimit](https://httpd.apache.org/docs/2.4/mod/mod_ratelimit.html)
*   [Traefik Rate Limiting](https://doc.traefik.io/traefik/middlewares/http/ratelimit/)
*   [HAProxy Rate Limiting](https://www.haproxy.com/blog/rate-limiting-with-haproxy/)

