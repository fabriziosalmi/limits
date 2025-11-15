# HAProxy Rate Limit Configuration

This directory contains the automatically generated HAProxy rate limit configuration file.

## Generated File

*   **`haproxy_rate_limit.conf`**: The main HAProxy rate limit configuration file generated from `config.yaml`.

## Integration

To integrate this configuration with your HAProxy server:

1.  **Copy the configuration file to your server:**
    ```bash
    scp haproxy_rate_limit.conf user@your-server:/path/to/haproxy/conf.d/
    ```

2.  **Include it in your HAProxy configuration:**
    Edit your `haproxy.cfg` file:
    ```
    frontend http-in
        bind *:80
        
        # Insert the content of haproxy_rate_limit.conf here
        # or use include if your HAProxy version supports it
        
        default_backend servers
    
    backend servers
        # ... backend configuration
    ```

3.  **Test the configuration:**
    ```bash
    haproxy -c -f /etc/haproxy/haproxy.cfg
    ```

4.  **Reload HAProxy:**
    ```bash
    systemctl reload haproxy
    ```

## Configuration Structure

The generated file includes:

*   **Stick tables**: For tracking request rates per IP address
*   **ACL definitions**: Access control lists for rate limiting logic
*   **HTTP request rules**: Deny or allow requests based on rate limits
*   **Path-specific rules**: Different rate limits for different URL paths

## Troubleshooting

*   **Configuration syntax error**: Use `haproxy -c -f config.file` to check for syntax errors.
*   **Rate limits not working**: Verify that stick tables are properly defined and have enough size.
*   **Memory issues**: Increase stick table size if you have many unique IP addresses.

## Resources

*   [HAProxy Rate Limiting Documentation](https://www.haproxy.com/blog/rate-limiting-with-haproxy/)
*   [HAProxy Configuration Manual](http://docs.haproxy.org/2.8/configuration.html)
*   [HAProxy Stick Tables](https://www.haproxy.com/blog/introduction-to-haproxy-stick-tables/)
