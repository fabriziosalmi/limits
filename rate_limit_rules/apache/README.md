# Apache mod_ratelimit Configuration

This directory contains the automatically generated Apache rate limit configuration file.

## Generated File

*   **`apache_rate_limit.conf`**: The Apache rate limit configuration file generated from `config.yaml` using Apache's `mod_ratelimit` module.

## Integration

To integrate this configuration with your Apache server:

1.  **Ensure mod_ratelimit is installed and enabled:**
    ```bash
    # For Debian/Ubuntu
    sudo a2enmod ratelimit
    
    # For RHEL/CentOS
    # mod_ratelimit is included in the httpd package
    ```

2.  **Copy the configuration file to your server:**
    ```bash
    scp apache_rate_limit.conf user@your-server:/path/to/apache/conf.d/
    ```

3.  **Include it in your Apache configuration:**
    Edit your virtual host file or `.htaccess`:
    ```apache
    <VirtualHost *:80>
        # ... other configurations
        Include /path/to/apache/conf.d/apache_rate_limit.conf
    </VirtualHost>
    ```

4.  **Test the configuration:**
    ```bash
    apachectl configtest
    ```

5.  **Restart Apache:**
    ```bash
    systemctl restart apache2
    # or for RHEL/CentOS
    systemctl restart httpd
    ```

## Configuration Structure

The generated file includes:

*   **mod_ratelimit directives**: `RateLimit` directives for rate limiting by IP, User-Agent, or header
*   **Path-specific rules**: Different rate limits for different URL paths via `<Location>` blocks
*   **IP whitelist/blacklist**: `<Files *>` blocks with `<RequireAll>` and `Require not ip` directives

## Troubleshooting

*   **mod_ratelimit not loading**: Check Apache error logs and ensure the `ratelimit` module is enabled.
*   **Rules not applying**: Verify that the `<IfModule mod_ratelimit.c>` block is being parsed correctly.
*   **Too many false positives**: Adjust the rate limit thresholds in `config.yaml`.

## Resources

*   [Apache mod_ratelimit Documentation](https://httpd.apache.org/docs/2.4/mod/mod_ratelimit.html)
