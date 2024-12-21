# 🔒 Limits: Automated Rate Limiting for Web Servers

🚀 Protect your web servers against abuse and ensure optimal performance with automated rate limiting configurations. This project generates and manages rate limit rules for multiple web server platforms, making it easy to implement robust protection against excessive requests.

## 📌 Project Highlights

*   **⚙️ Multi-Web Server Support:** Generates rate limiting configurations for Apache (ModSecurity), Nginx, Caddy, Traefik, and HAProxy.
*   **⏱️ Centralized Configuration:** Uses a single `config.yaml` file to define global and path-specific rate limits, as well as IP whitelisting/blacklisting.
*   **🔄 Automated Updates:** GitHub Actions automatically fetch the latest configuration and generate new rules daily.
*   **🛡️ Flexible Rate Limiting:** Supports limiting by IP address, User-Agent, or custom headers.
*   **✅ Easy Integration:** Clear instructions and example configurations are provided to quickly integrate rate limiting into your servers.
*   **🎛️ Granular Control:** Configure rate limits at both global and path-specific levels for detailed control.

## 🌐 Supported Web Servers

*   🔵 **Nginx**
*   🟢 **Caddy**
*   🟠 **Apache** (ModSecurity)
*   🟣 **Traefik**
*   🔴 **HAProxy**

## 📂 Project Structure

```
rate-limit-patterns/
├── rate_limit_rules/       # 🔧 Generated rate limit config files
│   ├── caddy/              # Caddy rate limit configs
│   ├── nginx/              # Nginx rate limit configs
│   ├── apache/             # Apache rate limit configs (ModSecurity)
│   ├── traefik/            # Traefik rate limit configs
│   └── haproxy/            # HAProxy rate limit configs
│
│── import_apache_rate_limit.py
│── import_caddy_rate_limit.py
│── import_haproxy_rate_limit.py
│── import_nginx_rate_limit.py
│── import_traefik_rate_limit.py
├── ratelimit.py           # ⚙️ Main Script to fetch rate limits config
├── ratelimit2caddy.py      # 🔄 Convert rate limit config to Caddy
├── ratelimit2nginx.py      # 🔄 Convert rate limit config to Nginx
├── ratelimit2apache.py     # 🔄 Convert rate limit config to Apache ModSecurity
├── ratelimit2traefik.py    # 🔄 Convert rate limit config to Traefik
├── ratelimit2haproxy.py   # 🔄 Convert rate limit config to HAProxy
├── config.yaml             # 📝 Configuration file to define rate limits
├── requirements.txt        # 📄 Required dependencies
└── .github/workflows/      # 🤖 GitHub Actions for automation
    └── update_rules.yml
```

## 🛠️ How It Works

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
*   The `ratelimit2*.py` scripts generate the platform-specific rate limiting configurations using the loaded config.
   * `ratelimit2caddy.py` generates Caddy configuration
   * `ratelimit2nginx.py` generates Nginx configuration
   * `ratelimit2apache.py` generates Apache ModSecurity configuration
   * `ratelimit2traefik.py` generates Traefik configuration
   * `ratelimit2haproxy.py` generates HAProxy configuration

### 3. Automation

*   GitHub Actions automatically generate rate limiting configurations daily.
*   Modified configuration files are automatically committed and pushed to the repository.

## ⚙️ Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/rate-limit-patterns.git
    cd rate-limit-patterns
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure `config.yaml`:**
     * Adapt the `config.yaml` with your specific requirements.

## 🚀 Usage (Web Server Integration)

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
### 2. Caddy Rate Limit Integration
 * Copy the `rate_limit_rules/caddy/caddy_rate_limit.conf` to your server.
 * Include the configuration in your caddyfile:
  ```caddyfile
  {
    include /path/to/caddy_rate_limit.conf
    ...
  }
  ```
### 3. Apache Rate Limit Integration
  * Copy `rate_limit_rules/apache/apache_rate_limit.conf` to your server.
  * Include the configuration in your apache virtualhost configuration file or inside a `.htaccess` file.

  ```apache
  <VirtualHost *:80>
    ...
     Include /path/to/apache_rate_limit.conf
   ...
  </VirtualHost>
  ```

### 4. Traefik Rate Limit Integration
   * Copy the content of `rate_limit_rules/traefik/traefik_rate_limit.conf` to your traefik configuration file (`traefik.yml`)

     ```toml
     # traefik.yml
     ...
     http:
       middlewares:
         # Insert content of traefik_rate_limit.conf here
       routers:
        # Add the rate limit middlewares to the routes

     ...
     ```
### 5. Haproxy Rate Limit Integration
    *   Copy `rate_limit_rules/haproxy/haproxy_rate_limit.conf` to your server.
    *   Include the configuration in your HAProxy configuration file (`haproxy.cfg`)
  ```
    frontend http-in
        # Insert the content of haproxy_rate_limit.conf here
    ...
  ```

## 🤖 Automation (GitHub Workflow)

*   **Daily Updates:** GitHub Actions fetches new rate limit configurations daily at midnight UTC.
*   **Auto Deployment:** Pushes new configuration files directly to `rate_limit_rules/`.
*   **Manual Trigger:**  Updates can also be triggered manually.

## 🤝 Contributing

*   Fork the repository.
*   Create a feature branch (`feature/new-feature`).
*   Commit and push changes.
*   Open a Pull Request.

## 📄 License

This project is licensed under the MIT License.
See the `LICENSE` file for details.

## 📞 Need Help?

*   Issues? Open a ticket in the Issues tab.

## 🌐 Resources

*   [Nginx Rate Limiting](https://docs.nginx.com/nginx/admin-guide/security/rate-limiting/)
*   [Caddy Rate Limiting](https://caddyserver.com/docs/caddyfile/directives/rate_limit)
*   [Apache mod_ratelimit](https://httpd.apache.org/docs/2.4/mod/mod_ratelimit.html)
*   [Traefik Rate Limiting](https://doc.traefik.io/traefik/middlewares/http/ratelimit/)
*   [HAProxy Rate Limiting](https://www.haproxy.com/blog/rate-limiting-with-haproxy/)

