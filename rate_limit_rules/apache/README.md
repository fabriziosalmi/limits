# Apache ModSecurity Rate Limit Configuration

This directory contains the automatically generated Apache ModSecurity rate limit configuration file.

## Generated File

*   **`apache_rate_limit.conf`**: The main Apache ModSecurity rate limit configuration file generated from `config.yaml`.

## Integration

To integrate this configuration with your Apache server:

1.  **Ensure ModSecurity is installed and enabled:**
    ```bash
    # For Debian/Ubuntu
    sudo apt-get install libapache2-mod-security2
    sudo a2enmod security2
    
    # For RHEL/CentOS
    sudo yum install mod_security
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

*   **ModSecurity rules**: Custom rules for rate limiting based on IP addresses
*   **Path-specific rules**: Different rate limits for different URL paths
*   **IP whitelist/blacklist**: Allow or deny specific IP addresses

## Troubleshooting

*   **ModSecurity not loading**: Check Apache error logs and ensure ModSecurity module is properly installed.
*   **Rules not applying**: Verify that ModSecurity engine is enabled (`SecRuleEngine On`).
*   **Too many false positives**: Adjust the rate limit thresholds in `config.yaml`.

## Resources

*   [Apache ModSecurity Documentation](https://github.com/SpiderLabs/ModSecurity)
*   [ModSecurity Reference Manual](https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual-(v2.x))
