# Apache mod_evasive Configuration

This directory contains the Apache rate limit configuration generated from `config.yaml` by `ratelimit2apache.py`, for the third-party module mod_evasive.

## Generated File

*   **`apache_rate_limit.conf`**: mod_evasive directives for the global request limit, the whitelist, and a `<Location "/">` block for the blacklist.

## What it does, and what it cannot do

*   **One request limit per client IP:** the global `requests_per_minute`, counted over `window` (`DOSSiteCount`, `DOSSiteInterval`, and the same values per page). An address over the limit is refused with 403 for one window (`DOSBlockingPeriod`).
*   **Not generated:** per-path limits (mod_evasive directives are not allowed inside `<Location>`), limits keyed by user agent or header (mod_evasive counts per IP only), and `burst` (no equivalent). Each is written into the file as a comment and reported as a warning when the file is generated.
*   **Approximate count:** mod_evasive keeps its counters per Apache child process, so a client is refused somewhat after the exact limit.
*   **Whitelist:** IPv4 addresses and networks, written as wildcards (`10.16.*.*`), the only form mod_evasive 1.10 matches; CIDR is only matched by 2.x. IPv6 entries are skipped.

Verified with Apache 2.4 and both mod_evasive 1.10.1 (Ubuntu 24.04) and 2.4.0 (Debian trixie): `apachectl -t` accepts the file, and a client is refused once over the limit unless it is whitelisted.

## Integration

1.  **Install and enable mod_evasive:**
    ```bash
    # Debian/Ubuntu
    sudo apt-get install libapache2-mod-evasive
    sudo a2enmod evasive
    ```

2.  **Copy the configuration file to your server:**
    ```bash
    scp apache_rate_limit.conf user@your-server:/etc/apache2/conf-available/
    ```

3.  **Include it in the server configuration or a virtual host** (not `.htaccess`, where mod_evasive directives are not valid):
    ```apache
    Include /etc/apache2/conf-available/apache_rate_limit.conf
    ```

4.  **Test the configuration:**
    ```bash
    apachectl configtest
    ```

5.  **Restart Apache:**
    ```bash
    systemctl restart apache2
    ```

## Troubleshooting

*   **`Invalid command 'DOSSiteCount'`**: mod_evasive is not loaded. Enable it; the file is deliberately not wrapped in `<IfModule>`, so a missing module is an error instead of a silent no-op.
*   **Nobody is ever refused on mod_evasive 2.x**: it stays disabled unless `DOSEnabled true` is set; the generated `<IfDirective DOSEnabled>` block does that. `DOSEnabled On` is refused by the module.
*   **Too many false positives**: raise `requests_per_minute` in `config.yaml`, or whitelist the addresses.
